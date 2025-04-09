# Knowledge Graph Analysis Report

## Overview
| Metric | Value |
|--------|-------|
| Total triples | 368253 |
| Entities | 35516 |
| Relationships | 231233 |

## Entity Types
| Type | Count |
|------|-------|
| Chart Entries | 26100 |
| Tracks | 2190 |
| Music Writers | 1454 |
| Music Artists | 974 |
| Music Producers | 744 |
| Genres | 691 |
| Instrumentalists | 544 |
| Time Instants | 525 |
| Time Intervals | 522 |
| Vocalists | 519 |
| Labels | 304 |
| Engineers | 293 |
| Recorders | 287 |
| Mixers | 231 |
| Time Durations | 61 |
| Arrangers | 46 |
| Languages | 19 |
| Temporal Units | 7 |
| Genders | 4 |
| Music Charts | 1 |
| Records | 0 |

## Relationship Types
| Type | Count |
|------|-------|
| chart entry-track links | 28932 |
| chart entry-chart links | 26100 |
| chart entry-chart links (alt) | 26100 |
| chart entry-position links | 26100 |
| chart entry-interval links | 26100 |
| chart entry-duration links | 26100 |
| entity-instant links | 26100 |
| track-genre links | 8355 |
| track-writer links | 7875 |
| artist-gender links | 3604 |
| track-artist links | 3190 |
| track-producer links | 2838 |
| track-language links | 2174 |
| track-lyrics links | 2174 |
| track-instrumentalist links | 1813 |
| instant-before-instant links | 1611 |
| instant-after-instant links | 1611 |
| track-vocalist links | 1510 |
| track-mixer links | 1467 |
| track-label links | 1203 |
| track-engineer links | 1132 |
| track-recorder links | 1079 |
| artist-birth date links | 770 |
| artist-area links | 742 |
| artist-country links | 736 |
| instant-date links | 525 |
| interval-start links | 522 |
| interval-end links | 522 |
| track-arranger links | 65 |
| duration-unit links | 61 |
| duration-value links | 61 |
| duration-xsd links | 61 |
| artist-legal name links | 0 |
| track-record links | 0 |

## Time Ontology Analysis
| Metric | Value |
|--------|-------|
| Complete intervals (with beginning and end) | 522 |
| time:before relationships | 1611 |
| time:after relationships | 1611 |
| Total temporal relationships | 3222 |

## Chart Runs Analysis
| Metric | Value |
|--------|-------|
| Total chart runs | 2832 |
| Tracks with chart runs | 2190 |
| Tracks with multiple chart runs | 440 |
| Percentage with multiple runs | 20.1 |
| Average runs per track | 1.29 |
| Average chart run (weeks) | 9.2 |
| Longest continuous chart run (weeks) | 69.0 |
| Shortest chart run (weeks) | 1.0 |
| Top 10 longest continuous chart runs | [{'track': 'Radioactive', 'artist': 'Imagine Dragons', 'duration_weeks': 69.0}, {'track': 'Party Rock Anthem', 'artist': 'GoonRock', 'duration_weeks': 63.0}, {'track': 'Rolling In The Deep', 'artist': 'Adele', 'duration_weeks': 60.0}, {'track': 'Counting Stars', 'artist': 'OneRepublic', 'duration_weeks': 57.0}, {'track': 'Somebody That I Used To Know', 'artist': 'Gotye', 'duration_weeks': 57.0}, {'track': 'Sail', 'artist': 'AWOLNATION', 'duration_weeks': 55.0}, {'track': 'Uptown Funk!', 'artist': 'Bruno Mars', 'duration_weeks': 54.0}, {'track': 'Ho Hey', 'artist': 'The Lumineers', 'duration_weeks': 53.0}, {'track': 'Sunflower', 'artist': 'Post Malone', 'duration_weeks': 53.0}, {'track': 'Better Now', 'artist': 'Post Malone', 'duration_weeks': 52.0}] |
| Top 10 tracks by total weeks on chart | [{'track': 'Radioactive', 'artist': 'Imagine Dragons', 'total_weeks': 69.0, 'chart_runs': 1}, {'track': 'Party Rock Anthem', 'artist': 'GoonRock', 'total_weeks': 63.0, 'chart_runs': 1}, {'track': 'Rolling In The Deep', 'artist': 'Adele', 'total_weeks': 60.0, 'chart_runs': 1}, {'track': 'Counting Stars', 'artist': 'OneRepublic', 'total_weeks': 58.0, 'chart_runs': 2}, {'track': 'Shape Of You', 'artist': 'Ed Sheeran', 'total_weeks': 58.0, 'chart_runs': 4}, {'track': 'Somebody That I Used To Know', 'artist': 'Gotye', 'total_weeks': 57.0, 'chart_runs': 1}, {'track': 'Dark Horse', 'artist': 'Juicy J', 'total_weeks': 55.0, 'chart_runs': 2}, {'track': 'Sail', 'artist': 'AWOLNATION', 'total_weeks': 55.0, 'chart_runs': 1}, {'track': 'Uptown Funk!', 'artist': 'Bruno Mars', 'total_weeks': 55.0, 'chart_runs': 2}, {'track': 'Ho Hey', 'artist': 'The Lumineers', 'total_weeks': 53.0, 'chart_runs': 1}] |

### Chart Run Duration Distribution
| Duration | Count | Percentage |
|----------|-------|------------|
| < 1 week | 0 | 0.00% |
| 1 week | 965 | 34.07% |
| 2 weeks | 328 | 11.58% |
| 3-4 weeks | 265 | 9.36% |
| 5-8 weeks | 241 | 8.51% |
| 9-12 weeks | 241 | 8.51% |
| 13-26 weeks | 531 | 18.75% |
| > 26 weeks | 261 | 9.22% |

### Top 10 Longest Continuous Chart Runs
| Track | Artist | Weeks |
|-------|--------|-------|
| Radioactive | Imagine Dragons | 69.0 |
| Party Rock Anthem | GoonRock | 63.0 |
| Rolling In The Deep | Adele | 60.0 |
| Counting Stars | OneRepublic | 57.0 |
| Somebody That I Used To Know | Gotye | 57.0 |
| Sail | AWOLNATION | 55.0 |
| Uptown Funk! | Bruno Mars | 54.0 |
| Ho Hey | The Lumineers | 53.0 |
| Sunflower | Post Malone | 53.0 |
| Better Now | Post Malone | 52.0 |

### Top 10 Tracks by Total Weeks on Chart
| Track | Artist | Total Weeks | Chart Runs |
|-------|--------|-------------|------------|
| Radioactive | Imagine Dragons | 69.0 | 1 |
| Party Rock Anthem | GoonRock | 63.0 | 1 |
| Rolling In The Deep | Adele | 60.0 | 1 |
| Counting Stars | OneRepublic | 58.0 | 2 |
| Shape Of You | Ed Sheeran | 58.0 | 4 |
| Somebody That I Used To Know | Gotye | 57.0 | 1 |
| Dark Horse | Juicy J | 55.0 | 2 |
| Sail | AWOLNATION | 55.0 | 1 |
| Uptown Funk! | Bruno Mars | 55.0 | 2 |
| Ho Hey | The Lumineers | 53.0 | 1 |

## Lyrics Analysis
| Metric | Value |
|--------|-------|
| Tracks with lyrics | 2174 |
| Total tracks | 2190 |
| Lyrics coverage (%) | 99.26940639269407 |
| Tracks with language info | 2174 |
| Language coverage (%) | 99.26940639269407 |
| Tracks with translated lyrics | 37 |
| Translation coverage (%) | 1.6894977168949772 |
| Tracks with theme info | 2173 |
| Theme coverage (%) | 99.22374429223744 |
| Average lyrics length (chars) | 3046.438 |
| Median lyrics length (chars) | 1905 |
| Average lines per lyrics | 67.752 |

### Lyrics Length Distribution
| Range | Count | Percentage |
|-------|-------|------------|
| 0-1000 chars | 60 | 6.00% |
| 1000-5000 chars | 913 | 91.30% |
| 5000-10000 chars | 21 | 2.10% |
| 10000-inf chars | 6 | 0.60% |

### Theme Distribution
| Theme | Count | Percentage |
|-------|-------|------------|
| joy | 959 | 44.13% |
| anger | 539 | 24.80% |
| sadness | 428 | 19.70% |
| love | 137 | 6.30% |
| fear | 95 | 4.37% |
| surprise | 12 | 0.55% |
| unknown | 3 | 0.14% |

### Language Distribution
| Language | Count | Percentage |
|----------|-------|------------|
| EN | 2137 | 98.30% |
| ES | 15 | 0.69% |
| KO | 6 | 0.28% |
| ET | 3 | 0.14% |
| FR | 3 | 0.14% |
| PT | 3 | 0.14% |
| RU | 2 | 0.09% |
| AR | 1 | 0.05% |
| DE | 1 | 0.05% |
| ID | 1 | 0.05% |
| IT | 1 | 0.05% |
| UNKNOWN | 1 | 0.05% |

## Additional Roles Analysis
| Role | Tracks | Coverage |
|------|--------|----------|
| Engineer | 444 | 20.27% |
| Mixer | 755 | 34.47% |
| Vocalist | 718 | 32.79% |
| Instrumentalist | 521 | 23.79% |
| Recorder | 478 | 21.83% |

## Artist Analysis
| Metric | Value |
|--------|-------|
| Total artists | 974 |
| Artists with birth date | 770 |
| Birth date coverage (%) | 79.06% |
| Artists with country | 736 |
| Country coverage (%) | 75.56% |
| Artists with area | 742 |
| Area coverage (%) | 76.18% |

### Artist Country Distribution
| Country | Count | Percentage |
|---------|-------|------------|
| US | 553 | 75.14% |
| GB | 64 | 8.70% |
| CA | 20 | 2.72% |
| AU | 14 | 1.90% |
| PR | 10 | 1.36% |
| FR | 9 | 1.22% |
| IE | 8 | 1.09% |
| SE | 7 | 0.95% |
| NL | 6 | 0.82% |
| JM | 6 | 0.82% |

### Artist Birth Decade Distribution
| Decade | Count | Percentage |
|--------|-------|------------|
| 1900s | 3 | 0.39% |
| 1910s | 7 | 0.91% |
| 1920s | 2 | 0.26% |
| 1930s | 2 | 0.26% |
| 1940s | 12 | 1.56% |
| 1950s | 12 | 1.56% |
| 1960s | 41 | 5.32% |
| 1970s | 97 | 12.60% |
| 1980s | 231 | 30.00% |
| 1990s | 222 | 28.83% |
| 2000s | 89 | 11.56% |
| 2010s | 52 | 6.75% |

## Label Analysis
| Metric | Value |
|--------|-------|
| Total record labels | 304 |
| Tracks with label | 798 |
| Total tracks | 2190 |
| Label coverage (%) | 36.44% |

### Top Record Labels
| Label | Tracks | Percentage |
|-------|--------|------------|
| WEA International Inc. | 65 | 8.15% |
| Interscope Records | 50 | 6.27% |
| Big Machine Label Group, LLC | 46 | 5.76% |
| Atlantic Recording Corporation | 43 | 5.39% |
| Young Money | 39 | 4.89% |
| Cash Money Records | 39 | 4.89% |
| RCA Records | 30 | 3.76% |
| Republic Records | 28 | 3.51% |
| Aftermath Records | 22 | 2.76% |
| Epic Records | 22 | 2.76% |

## Ontology Utilization
| Metric | Value |
|--------|-------|
| Time ontology entities | 1108 |
| Time ontology relationships | 83274 |
