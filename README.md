# Image Link Scraper

A minimal Streamlit application that scrapes image URLs from webpages using the Firecrawl API.

## Features

- Extracts image URLs from various HTML attributes (`src`, `data-src`, `data-lazy-src`, `srcset`)
- Converts relative URLs to absolute URLs
- Deduplicates results while preserving order
- Caches results for 10 minutes (per API key + URL combination)
- Dark minimal UI design
- One-click copy to clipboard functionality
- Download URLs as text file (fallback when clipboard not available)

## Installation

1. Clone this repository or download the files

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the application:
```bash
streamlit run app.py
```

2. The app will open in your browser at `http://localhost:8501`

3. Enter your Firecrawl API key in the sidebar (get one at https://firecrawl.dev)

4. Enter the URL of the webpage you want to scrape

5. Click "Extract Images" to scrape the page

6. Use "Copy All URLs" button to copy all image URLs to clipboard, or download as text file

## Running Tests

Run the unit tests with pytest:
```bash
pytest tests/test_extract.py
```

Or with verbose output:
```bash
pytest tests/test_extract.py -v
```

## Deployment Notes

- When deployed publicly with HTTPS, the clipboard copy functionality will work seamlessly
- On HTTP or localhost, the clipboard feature may fall back to file download depending on browser security settings
- API keys are kept in session state only and never persisted to disk

## Project Structure

```
.
├── app.py                  # Main Streamlit application
├── firecrawl_client.py     # Firecrawl API wrapper and image extraction logic
├── cache_utils.py          # In-memory TTL cache implementation
├── requirements.txt        # Python dependencies
├── README.md              # This file
└── tests/
    └── test_extract.py    # Unit tests for image extraction
```

## Security Notes

- API keys are stored in session state only (not persisted)
- The application masks API keys in the UI (password input field)
- No logging of sensitive information

## Requirements

- Python 3.8+
- Firecrawl API key (https://firecrawl.dev)
- Internet connection

## Error Handling

The application handles common errors gracefully:
- Invalid or missing API key (401)
- Rate limiting (429)
- Network timeouts
- Invalid URLs
- Pages with no images