# Knowledge Graph Analysis Report

## Overview
| Metric | Value |
|--------|-------|
| Total triples | 330327 |
| Entities | 34841 |
| Relationships | 213629 |

## Entity Types
| Type | Count |
|------|-------|
| Chart Entries | 26100 |
| Tracks | 2190 |
| Music Writers | 1475 |
| Music Artists | 943 |
| Music Producers | 634 |
| Instrumentalists | 553 |
| Time Instants | 525 |
| Time Intervals | 522 |
| Genres | 485 |
| Vocalists | 370 |
| Engineers | 276 |
| Recorders | 265 |
| Mixers | 219 |
| Labels | 167 |
| Time Durations | 61 |
| Arrangers | 25 |
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
| track-genre links | 4291 |
| track-writer links | 3364 |
| track-lyrics links | 3110 |
| track-artist links | 2956 |
| track-language links | 2174 |
| instant-before-instant links | 1611 |
| instant-after-instant links | 1611 |
| track-producer links | 1243 |
| artist-gender links | 943 |
| track-instrumentalist links | 942 |
| track-mixer links | 649 |
| track-vocalist links | 635 |
| track-label links | 562 |
| track-engineer links | 553 |
| instant-date links | 525 |
| interval-start links | 522 |
| interval-end links | 522 |
| track-recorder links | 472 |
| artist-birth date links | 332 |
| artist-area links | 323 |
| artist-country links | 316 |
| artist-legal name links | 229 |
| duration-unit links | 61 |
| duration-value links | 61 |
| duration-xsd links | 61 |
| track-arranger links | 29 |
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
| Top 10 longest continuous chart runs | [{'track': 'Radioactive', 'artist': 'Imagine Dragons', 'duration_weeks': 69.0}, {'track': 'Party Rock Anthem', 'artist': 'Lauren Bennett & GoonRock', 'duration_weeks': 63.0}, {'track': 'Rolling In The Deep', 'artist': 'Adele', 'duration_weeks': 60.0}, {'track': 'Counting Stars', 'artist': 'OneRepublic', 'duration_weeks': 57.0}, {'track': 'Somebody That I Used To Know', 'artist': 'Gotye', 'duration_weeks': 57.0}, {'track': 'Sail', 'artist': 'AWOLNATION', 'duration_weeks': 55.0}, {'track': 'Uptown Funk!', 'artist': 'Bruno Mars', 'duration_weeks': 54.0}, {'track': 'Ho Hey', 'artist': 'The Lumineers', 'duration_weeks': 53.0}, {'track': 'Sunflower', 'artist': 'Post Malone', 'duration_weeks': 53.0}, {'track': 'Better Now', 'artist': 'Post Malone', 'duration_weeks': 52.0}] |
| Top 10 tracks by total weeks on chart | [{'track': 'Radioactive', 'artist': 'Imagine Dragons', 'total_weeks': 69.0, 'chart_runs': 1}, {'track': 'Party Rock Anthem', 'artist': 'Lauren Bennett & GoonRock', 'total_weeks': 63.0, 'chart_runs': 1}, {'track': 'Rolling In The Deep', 'artist': 'Adele', 'total_weeks': 60.0, 'chart_runs': 1}, {'track': 'Counting Stars', 'artist': 'OneRepublic', 'total_weeks': 58.0, 'chart_runs': 2}, {'track': 'Shape Of You', 'artist': 'Ed Sheeran', 'total_weeks': 58.0, 'chart_runs': 4}, {'track': 'Somebody That I Used To Know', 'artist': 'Gotye', 'total_weeks': 57.0, 'chart_runs': 1}, {'track': 'Dark Horse', 'artist': 'Juicy J', 'total_weeks': 55.0, 'chart_runs': 2}, {'track': 'Sail', 'artist': 'AWOLNATION', 'total_weeks': 55.0, 'chart_runs': 1}, {'track': 'Uptown Funk!', 'artist': 'Bruno Mars', 'total_weeks': 55.0, 'chart_runs': 2}, {'track': 'Ho Hey', 'artist': 'The Lumineers', 'total_weeks': 53.0, 'chart_runs': 1}] |

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
| Party Rock Anthem | Lauren Bennett & GoonRock | 63.0 |
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
| Party Rock Anthem | Lauren Bennett & GoonRock | 63.0 | 1 |
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
| Average lyrics length (chars) | 2902.263 |
| Median lyrics length (chars) | 2012 |
| Average lines per lyrics | 47.002 |

### Lyrics Length Distribution
| Range | Count | Percentage |
|-------|-------|------------|
| 0-1000 chars | 52 | 5.20% |
| 1000-5000 chars | 916 | 91.60% |
| 5000-10000 chars | 27 | 2.70% |
| 10000-inf chars | 5 | 0.50% |

### Theme Distribution
| Theme | Count | Percentage |
|-------|-------|------------|
| joy | 960 | 44.18% |
| anger | 539 | 24.80% |
| sadness | 427 | 19.65% |
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
| Engineer | 220 | 10.05% |
| Mixer | 355 | 16.21% |
| Vocalist | 311 | 14.20% |
| Instrumentalist | 259 | 11.83% |
| Recorder | 206 | 9.41% |

## Artist Analysis
| Metric | Value |
|--------|-------|
| Total artists | 943 |
| Artists with birth date | 332 |
| Birth date coverage (%) | 35.21% |
| Artists with country | 316 |
| Country coverage (%) | 33.51% |
| Artists with area | 323 |
| Area coverage (%) | 34.25% |

### Artist Country Distribution
| Country | Count | Percentage |
|---------|-------|------------|
| US | 255 | 80.70% |
| GB | 21 | 6.65% |
| CA | 11 | 3.48% |
| AU | 6 | 1.90% |
| KR | 3 | 0.95% |
| IE | 3 | 0.95% |
| DE | 2 | 0.63% |
| NO | 2 | 0.63% |
| SE | 2 | 0.63% |
| PR | 2 | 0.63% |

### Artist Birth Decade Distribution
| Decade | Count | Percentage |
|--------|-------|------------|
| 1900s | 1 | 0.30% |
| 1910s | 2 | 0.60% |
| 1920s | 1 | 0.30% |
| 1940s | 4 | 1.20% |
| 1950s | 2 | 0.60% |
| 1960s | 9 | 2.71% |
| 1970s | 40 | 12.05% |
| 1980s | 107 | 32.23% |
| 1990s | 108 | 32.53% |
| 2000s | 39 | 11.75% |
| 2010s | 19 | 5.72% |

## Label Analysis
| Metric | Value |
|--------|-------|
| Total record labels | 167 |
| Tracks with label | 378 |
| Total tracks | 2190 |
| Label coverage (%) | 17.26% |

### Top Record Labels
| Label | Tracks | Percentage |
|-------|--------|------------|
| WEA International Inc. | 36 | 9.52% |
| Big Machine Label Group, LLC | 33 | 8.73% |
| Atlantic Recording Corporation | 26 | 6.88% |
| Interscope Records | 25 | 6.61% |
| Young Money | 23 | 6.08% |
| Cash Money Records | 23 | 6.08% |
| Apollo A-1 LLC | 15 | 3.97% |
| Big Machine Records, LLC | 14 | 3.70% |
| RCA Records | 14 | 3.70% |
| Dreamville, Inc. | 12 | 3.17% |

## Ontology Utilization
| Metric | Value |
|--------|-------|
| Time ontology entities | 1108 |
| Time ontology relationships | 83274 |
