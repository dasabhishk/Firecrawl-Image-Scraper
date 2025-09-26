import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from firecrawl_client import extract_image_urls_from_html


def test_extract_basic_img_src():
    html = '''
    <html>
        <body>
            <img src="/image1.jpg">
            <img src="https://example.com/image2.png">
        </body>
    </html>
    '''
    base_url = "https://example.com"
    urls = extract_image_urls_from_html(html, base_url)

    assert "https://example.com/image1.jpg" in urls
    assert "https://example.com/image2.png" in urls
    assert len(urls) == 2


def test_extract_data_src_attributes():
    html = '''
    <html>
        <body>
            <img data-src="/lazy-image.jpg">
            <img data-lazy-src="/another-lazy.png">
        </body>
    </html>
    '''
    base_url = "https://example.com"
    urls = extract_image_urls_from_html(html, base_url)

    assert "https://example.com/lazy-image.jpg" in urls
    assert "https://example.com/another-lazy.png" in urls
    assert len(urls) == 2


def test_extract_srcset_first_url():
    html = '''
    <html>
        <body>
            <img srcset="/small.jpg 480w, /medium.jpg 800w, /large.jpg 1200w">
            <source srcset="/webp-image.webp 1x, /webp-image-2x.webp 2x">
        </body>
    </html>
    '''
    base_url = "https://example.com"
    urls = extract_image_urls_from_html(html, base_url)

    assert "https://example.com/small.jpg" in urls
    assert "https://example.com/webp-image.webp" in urls
    assert len(urls) == 2


def test_extract_inline_style_backgrounds():
    html = '''
    <html>
        <body>
            <div style="background-image: url('/bg-image.jpg')"></div>
            <div style="background: url(pattern.png) no-repeat"></div>
        </body>
    </html>
    '''
    base_url = "https://example.com"
    urls = extract_image_urls_from_html(html, base_url)

    assert "https://example.com/bg-image.jpg" in urls
    assert "https://example.com/pattern.png" in urls
    assert len(urls) == 2


def test_extract_data_bg_attributes():
    html = '''
    <html>
        <body>
            <div data-bg="/hero-bg.jpg"></div>
            <section data-background-image="/section-bg.png"></section>
        </body>
    </html>
    '''
    base_url = "https://example.com"
    urls = extract_image_urls_from_html(html, base_url)

    assert "https://example.com/hero-bg.jpg" in urls
    assert "https://example.com/section-bg.png" in urls
    assert len(urls) == 2


def test_deduplicate_urls():
    html = '''
    <html>
        <body>
            <img src="/duplicate.jpg">
            <img src="/duplicate.jpg">
            <img data-src="/duplicate.jpg">
        </body>
    </html>
    '''
    base_url = "https://example.com"
    urls = extract_image_urls_from_html(html, base_url)

    assert "https://example.com/duplicate.jpg" in urls
    assert len(urls) == 1


def test_ignore_data_urls():
    html = '''
    <html>
        <body>
            <img src="data:image/png;base64,iVBORw0KGg...">
            <img src="/real-image.jpg">
        </body>
    </html>
    '''
    base_url = "https://example.com"
    urls = extract_image_urls_from_html(html, base_url)

    assert "https://example.com/real-image.jpg" in urls
    assert len(urls) == 1
    assert not any("data:" in url for url in urls)


def test_ignore_javascript_urls():
    html = '''
    <html>
        <body>
            <img src="javascript:void(0)">
            <img src="/valid-image.png">
        </body>
    </html>
    '''
    base_url = "https://example.com"
    urls = extract_image_urls_from_html(html, base_url)

    assert "https://example.com/valid-image.png" in urls
    assert len(urls) == 1
    assert not any("javascript:" in url for url in urls)


def test_handle_empty_html():
    urls = extract_image_urls_from_html("", "https://example.com")
    assert urls == []


def test_handle_no_images():
    html = '''
    <html>
        <body>
            <p>Just text content</p>
            <div>No images here</div>
        </body>
    </html>
    '''
    base_url = "https://example.com"
    urls = extract_image_urls_from_html(html, base_url)
    assert urls == []


def test_preserve_order():
    html = '''
    <html>
        <body>
            <img src="/first.jpg">
            <img src="/second.jpg">
            <img src="/third.jpg">
        </body>
    </html>
    '''
    base_url = "https://example.com"
    urls = extract_image_urls_from_html(html, base_url)

    assert urls[0] == "https://example.com/first.jpg"
    assert urls[1] == "https://example.com/second.jpg"
    assert urls[2] == "https://example.com/third.jpg"


def test_complex_real_world_example():
    html = '''
    <html>
        <body>
            <img src="/logo.svg" alt="Logo">
            <img data-src="/hero-image.jpg" class="lazy">
            <picture>
                <source srcset="/image.webp 1x, /image@2x.webp 2x" type="image/webp">
                <img src="/image.jpg" srcset="/image.jpg 1x, /image@2x.jpg 2x">
            </picture>
            <div style="background: url('/pattern.png') repeat-x"></div>
            <section data-bg="/section-bg.jpg"></section>
        </body>
    </html>
    '''
    base_url = "https://example.com"
    urls = extract_image_urls_from_html(html, base_url)

    expected_urls = {
        "https://example.com/logo.svg",
        "https://example.com/hero-image.jpg",
        "https://example.com/image.webp",
        "https://example.com/image.jpg",
        "https://example.com/pattern.png",
        "https://example.com/section-bg.jpg"
    }

    assert set(urls) == expected_urls