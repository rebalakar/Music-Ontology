import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re

# Define a common header to mimic a browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/115.0.0.0 Safari/537.36"
}

def fetch_page(url):
    """Fetches page content with a custom header."""
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def parse_year_page(html):
    """
    Extracts chart page URLs from a year page.
    We look for anchor tags where the href contains '/singles-chart/'.
    """
    soup = BeautifulSoup(html, 'html.parser')
    links = soup.find_all('a', href=True)
    chart_urls = set()  # use a set to avoid duplicates

    for link in links:
        href = link['href']
        if '/singles-chart/' in href:
            if href.startswith('http'):
                full_url = href
            else:
                full_url = "https://musicchartsarchive.com" + href
            chart_urls.add(full_url)
    
    return list(chart_urls)

def parse_chart_page(html):
    """
    Parses a chart page to extract chart entries.
    The expected output is a list of dictionaries with keys:
      - rank, song, artist
    Adjust the selectors based on the actual HTML structure.
    """
    soup = BeautifulSoup(html, 'html.parser')
    entries = []
    
    # Try to find a table containing the chart data.
    table = soup.find('table', class_='chart-table')
    
    if table:
        print("✅ Extracting data from TABLE format")
        rows = table.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            # We expect at least three columns: rank, song, artist.
            if len(cols) >= 3:
                rank = cols[0].get_text(strip=True)
                song = cols[1].get_text(strip=True)
                artist = cols[2].get_text(strip=True)
                entries.append({'rank': rank, 'song': song, 'artist': artist})
    else:
        # Fallback extraction if table not found
        content_div = soup.find('div', class_='chart-content')
        if content_div:
            lines = content_div.get_text("\n").splitlines()
            for line in lines:
                if re.match(r"^\d+\s", line):
                    parts = line.split('\t')
                    if len(parts) >= 3:
                        rank = parts[0].strip()
                        song = parts[1].strip()
                        artist = parts[2].strip()
                        entries.append({'rank': rank, 'song': song, 'artist': artist})
    
    return entries

def extract_date_from_url(url):
    """
    Extracts the date from a chart URL.
    Expected format: .../singles-chart/YYYY-MM-DD
    """
    match = re.search(r'(\d{4}-\d{2}-\d{2})', url)
    if match:
        return match.group(1)
    return None

def main():
    # List of years to process
    years = [str(year) for year in range(2010, 2020)]
    all_chart_data = []
    
    for year in years:
        year_url = f"https://musicchartsarchive.com/singles-charts/{year}"
        print(f"\nFetching year page: {year_url}")
        year_html = fetch_page(year_url)
        if not year_html:
            continue
        
        # Extract chart page URLs for the given year
        chart_urls = parse_year_page(year_html)
        print(f"Found {len(chart_urls)} chart pages for {year}.")
        
        # Iterate through each chart page URL
        for url in chart_urls:
            print(f"Fetching chart page: {url}")
            chart_html = fetch_page(url)
            if not chart_html:
                continue
            
            # Parse chart entries from the individual chart page
            entries = parse_chart_page(chart_html)
            chart_date = extract_date_from_url(url)
            for entry in entries:
                entry['date'] = chart_date  # assign the date extracted from URL
            
            all_chart_data.extend(entries)
            
            # Respectful delay between requests
            time.sleep(1)
    
    if all_chart_data:
        # Convert the extracted data to a DataFrame and save it
        df = pd.DataFrame(all_chart_data)
        print("\nSample extracted data:")
        print(df.head())
        output_file = "singles_charts_2010s.csv"
        df.to_csv(output_file, index=False)
        print(f"Data saved to '{output_file}'")
    else:
        print("No chart data extracted.")

if __name__ == "__main__":
    main()
