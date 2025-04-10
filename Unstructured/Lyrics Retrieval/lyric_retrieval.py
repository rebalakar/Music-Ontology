import os
import pandas as pd
import json
import asyncio
import aiohttp
import async_timeout
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import logging

# Set up logging to file and console.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler("lyrics_errors.log"),
        logging.StreamHandler()
    ]
)

# Load environment variables from .env file
load_dotenv()
GENIUS_ACCESS_TOKEN = os.getenv("GENIUS_ACCESS_TOKEN")
BASE_URL = "https://api.genius.com"

def clean_artist(artist):
    lower_artist = artist.lower()
    for indicator in ["feat.", "feat", "ft.", "ft", "featuring"]:
        if indicator in lower_artist:
            lower_artist = lower_artist.split(indicator)[0]
            break
    return lower_artist.strip()

def clean_song(song):
    return song.strip()

async def fetch_song_data(session, song, artist, retries=3):
    """Fetch song metadata from the Genius API with exponential backoff."""
    query = f"{song} {artist}"
    url = f"{BASE_URL}/search?q={query}"
    headers = {"Authorization": f"Bearer {GENIUS_ACCESS_TOKEN}"}
    
    for attempt in range(1, retries + 1):
        try:
            async with async_timeout.timeout(15):
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 429:
                        wait_time = 2 ** attempt
                        logging.warning(f"429 for query '{query}'. Attempt {attempt}/{retries}. Waiting {wait_time} sec.")
                        await asyncio.sleep(wait_time)
                    else:
                        logging.error(f"Error: Status {response.status} for query '{query}'")
                        return None
        except Exception as e:
            logging.error(f"Exception for query '{query}' on attempt {attempt}: {e}")
            await asyncio.sleep(2 ** attempt)
    return None

async def fetch_lyrics_page(session, url, retries=3):
    """Fetch the song page HTML and return the content."""
    for attempt in range(1, retries + 1):
        try:
            async with async_timeout.timeout(15):
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.text()
                    elif response.status == 429:
                        wait_time = 2 ** attempt
                        logging.warning(f"429 when fetching song page {url}. Attempt {attempt}/{retries}. Waiting {wait_time} sec.")
                        await asyncio.sleep(wait_time)
                    else:
                        logging.error(f"Error fetching song page {url}: Status {response.status}")
                        return None
        except Exception as e:
            logging.error(f"Exception when fetching song page {url} on attempt {attempt}: {e}")
            await asyncio.sleep(2 ** attempt)
    return None

def extract_lyrics(html):
    """Extract lyrics from a Genius song page using BeautifulSoup."""
    soup = BeautifulSoup(html, "html.parser")
    divs = soup.find_all("div", attrs={"data-lyrics-container": "true"})
    if not divs:
        return "Lyrics not found"
    lyrics = "\n".join(div.get_text(separator="\n").strip() for div in divs)
    return lyrics

async def process_song(session, row):
    """
    Process a single song: search the API, fetch the song page,
    extract the lyrics.
    """
    artist_raw = row["artist"]
    song_raw = row["song"]
    artist = clean_artist(artist_raw)
    song = clean_song(song_raw)
    key = f"{artist_raw} - {song_raw}"
    
    data = await fetch_song_data(session, song, artist)
    if data and data.get("response", {}).get("hits"):
        hit = data["response"]["hits"][0]
        song_info = hit.get("result", {})
        song_url = song_info.get("url")
        if song_url:
            html = await fetch_lyrics_page(session, song_url)
            if html:
                lyrics = extract_lyrics(html)
            else:
                lyrics = "Error fetching song page"
        else:
            lyrics = "No URL found in song info"
    else:
        lyrics = "Song not found in API search"
    return key, lyrics

async def process_batch(session, rows, batch_index, max_retries=3):
    """
    Process a batch of songs (rows). Retry failed tasks up to max_retries.
    Returns a dictionary mapping song key to lyrics.
    """
    batch_results = {}
    tasks = [process_song(session, row) for _, row in rows]
    
    # Use asyncio.gather with return_exceptions=True
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Retry logic for failures within the batch.
    retry_count = 0
    failed_rows = []
    for idx, result in enumerate(results):
        if isinstance(result, Exception):
            failed_rows.append(rows[idx])
            logging.error(f"Batch {batch_index}: Error processing row {rows[idx][1].to_dict()}: {result}")
        else:
            key, lyrics = result
            batch_results[key] = lyrics
    
    while failed_rows and retry_count < max_retries:
        retry_count += 1
        logging.info(f"Batch {batch_index}: Retrying {len(failed_rows)} failed tasks, attempt {retry_count}/{max_retries}")
        retry_tasks = [process_song(session, row) for _, row in failed_rows]
        retry_results = await asyncio.gather(*retry_tasks, return_exceptions=True)
        new_failed = []
        for idx, result in enumerate(retry_results):
            if isinstance(result, Exception):
                new_failed.append(failed_rows[idx])
                logging.error(f"Batch {batch_index}: Retry error for row {failed_rows[idx][1].to_dict()}: {result}")
            else:
                key, lyrics = result
                batch_results[key] = lyrics
        failed_rows = new_failed
    if failed_rows:
        logging.error(f"Batch {batch_index}: Failed {len(failed_rows)} tasks after {max_retries} retries.")
        # For rows that still fail, record an error message.
        for _, row in failed_rows:
            key = f"{row['artist']} - {row['song']}"
            batch_results[key] = "Failed after retries"
    return batch_results

async def main():
    df = pd.read_csv("singles_charts_2010s.csv")
    lyrics_data = {}

    batch_size = 8
    total_rows = len(df)
    total_batches = (total_rows + batch_size - 1) // batch_size
    
    async with aiohttp.ClientSession() as session:
        rows = list(df.iterrows())
        for i in range(0, total_rows, batch_size):
            batch_index = i // batch_size + 1
            batch_rows = rows[i: i + batch_size]
            logging.info(f"Processing batch {batch_index} of {total_batches} with {len(batch_rows)} songs.")
            
            batch_results = await process_batch(session, batch_rows, batch_index, max_retries=3)
            lyrics_data.update(batch_results)
            
            logging.info(f"Batch {batch_index} completed. Updating lyrics.json...")
            # Write out progress after each batch.
            with open("lyrics.json", "w", encoding="utf-8") as f:
                json.dump(lyrics_data, f, indent=4, ensure_ascii=False)
            logging.info(f"Progress updated in lyrics.json. Total songs processed so far: {len(lyrics_data)}")
    
    logging.info("Lyrics extraction completed.")

if __name__ == "__main__":
    asyncio.run(main())
