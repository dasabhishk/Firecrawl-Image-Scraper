import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
from typing import List, Set

class FirecrawlClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.firecrawl.dev/v2"

    def scrape_images(self, url: str, timeout: int = 30) -> List[str]:
        if not self.api_key:
            raise ValueError("API key is required")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "url": url,
            "formats": ["html"]
        }

        try:
            response = requests.post(
                f"{self.base_url}/scrape",
                headers=headers,
                json=payload,
                timeout=timeout
            )

            if response.status_code == 401:
                raise ValueError("401 Unauthorized: Invalid API key")
            elif response.status_code == 429:
                raise ValueError("429 Too Many Requests: Rate limit exceeded")
            elif response.status_code != 200:
                raise ValueError(f"HTTP {response.status_code}: {response.text[:200]}")

            data = response.json()

            if not data.get("success"):
                raise ValueError(f"API error: {data.get('error', 'Unknown error')}")

            html_content = data.get("data", {}).get("html", "")

            if not html_content:
                return []

            return extract_image_urls_from_html(html_content, url)

        except requests.Timeout:
            raise ValueError("Request timeout: Page took too long to respond")
        except requests.RequestException as e:
            raise ValueError(f"Network error: {str(e)}")


def extract_image_urls_from_html(html: str, base_url: str) -> List[str]:
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    image_urls: Set[str] = set()

    for img in soup.find_all("img"):
        src = img.get("src")
        if src:
            image_urls.add(src)

        data_src = img.get("data-src")
        if data_src:
            image_urls.add(data_src)

        data_lazy_src = img.get("data-lazy-src")
        if data_lazy_src:
            image_urls.add(data_lazy_src)

        srcset = img.get("srcset")
        if srcset:
            first_url = srcset.split(",")[0].strip()
            url_part = first_url.split(" ")[0]
            if url_part:
                image_urls.add(url_part)

    for source in soup.find_all("source"):
        srcset = source.get("srcset")
        if srcset:
            first_url = srcset.split(",")[0].strip()
            url_part = first_url.split(" ")[0]
            if url_part:
                image_urls.add(url_part)

    style_pattern = re.compile(r'url\(["\']?([^)"\']+)["\']?\)', re.IGNORECASE)
    for element in soup.find_all(style=True):
        style = element.get("style", "")
        matches = style_pattern.findall(style)
        for match in matches:
            if any(ext in match.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp']):
                image_urls.add(match)

    for element in soup.find_all(attrs={"data-bg": True}):
        data_bg = element.get("data-bg")
        if data_bg:
            image_urls.add(data_bg)

    for element in soup.find_all(attrs={"data-background-image": True}):
        bg_image = element.get("data-background-image")
        if bg_image:
            image_urls.add(bg_image)

    absolute_urls: List[str] = []
    seen: Set[str] = set()

    for url in image_urls:
        url = url.strip()
        if not url or url.startswith("data:") or url.startswith("javascript:"):
            continue

        try:
            absolute_url = urljoin(base_url, url)
            normalized_url = urlparse(absolute_url)._replace(fragment="").geturl()

            if normalized_url not in seen:
                seen.add(normalized_url)
                absolute_urls.append(normalized_url)
        except Exception:
            continue

    return absolute_urls