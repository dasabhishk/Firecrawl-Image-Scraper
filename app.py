import streamlit as st
import validators
import requests
from firecrawl_client import FirecrawlClient
from cache_utils import get_cached_result, set_cached_result

st.set_page_config(
    page_title="Image Link Scraper",
    page_icon="📷",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp {
        background-color: #0E1117;
    }
    .main {
        padding-top: 2rem;
    }
    h1 {
        color: #FAFAFA;
        font-weight: 500;
        margin-bottom: 2rem;
    }
    .stButton > button {
        background-color: #262730;
        color: #FAFAFA;
        border: 1px solid #3A3B45;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background-color: #3A3B45;
        border-color: #4A4B55;
    }
    .stTextInput > div > div > input {
        background-color: #262730;
        color: #FAFAFA;
        border: 1px solid #3A3B45;
    }
    /* Fix password field eye icon alignment */
    .stTextInput button {
        margin-top: 0 !important;
        height: 100% !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    .stTextArea > div > div > textarea {
        background-color: #262730;
        color: #FAFAFA;
        border: 1px solid #3A3B45;
        font-family: monospace;
    }
    .copy-button {
        margin-top: 1rem;
    }
    .error-message {
        color: #FF4B4B;
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: rgba(255, 75, 75, 0.1);
        border: 1px solid rgba(255, 75, 75, 0.3);
    }
    .success-message {
        color: #00FF88;
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: rgba(0, 255, 136, 0.1);
        border: 1px solid rgba(0, 255, 136, 0.3);
    }
    .status-ready {
        color: #00FF88;
        padding: 0.5rem;
        border-radius: 0.3rem;
        background-color: rgba(0, 255, 136, 0.1);
        border: 1px solid rgba(0, 255, 136, 0.2);
        font-size: 0.85rem;
        margin-top: 0.5rem;
    }
    .status-error {
        color: #FF4B4B;
        padding: 0.5rem;
        border-radius: 0.3rem;
        background-color: rgba(255, 75, 75, 0.1);
        border: 1px solid rgba(255, 75, 75, 0.2);
        font-size: 0.85rem;
        margin-top: 0.5rem;
    }
    .status-checking {
        color: #FFA500;
        padding: 0.5rem;
        border-radius: 0.3rem;
        background-color: rgba(255, 165, 0, 0.1);
        border: 1px solid rgba(255, 165, 0, 0.2);
        font-size: 0.85rem;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "api_key_validated" not in st.session_state:
    st.session_state.api_key_validated = False
if "validated_key" not in st.session_state:
    st.session_state.validated_key = ""

def validate_api_key(api_key):
    if not api_key:
        return False, "No API key provided"

    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        test_payload = {
            "url": "https://example.com",
            "formats": ["html"]
        }

        response = requests.post(
            "https://api.firecrawl.dev/v2/scrape",
            headers=headers,
            json=test_payload,
            timeout=5
        )

        if response.status_code == 200:
            return True, "Connection successful"
        elif response.status_code == 401:
            return False, "Invalid API key"
        elif response.status_code == 429:
            return True, "API key valid (rate limited)"
        else:
            return False, f"Error: {response.status_code}"

    except requests.Timeout:
        return False, "Connection timeout"
    except requests.RequestException:
        return False, "Connection failed"

with st.sidebar:
    st.markdown("### Configuration")
    api_key = st.text_input(
        "Firecrawl API Key",
        value=st.session_state.api_key,
        type="password",
        placeholder="Enter your API key",
        help="Your Firecrawl API key will not be stored",
        key="api_key_input"
    )

    if api_key != st.session_state.api_key:
        st.session_state.api_key = api_key
        # Only reset validation if it's actually a different key
        if api_key != st.session_state.validated_key:
            st.session_state.api_key_validated = False

    if api_key:
        # Check if this exact key has already been validated successfully
        if api_key == st.session_state.validated_key and st.session_state.api_key_validated:
            # Skip validation - we already know this key works
            st.markdown('<div class="status-ready">API key validated (cached)<br/>Ready to begin scraping</div>', unsafe_allow_html=True)
        elif not st.session_state.api_key_validated:
            # Need to validate this key
            with st.spinner("Validating API key..."):
                is_valid, message = validate_api_key(api_key)
                st.session_state.api_key_validated = is_valid

                if is_valid:
                    # Store the successfully validated key
                    st.session_state.validated_key = api_key
                    st.markdown(f'<div class="status-ready">{message}<br/>Ready to begin scraping</div>', unsafe_allow_html=True)
                else:
                    # Clear validated key on failure
                    st.session_state.validated_key = ""
                    st.markdown(f'<div class="status-error">{message}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-ready">API key validated<br/>Ready to begin scraping</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-error">API key required</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    ### About
    Extract all image URLs from any webpage using the Firecrawl API.

    **Features:**
    - Extracts from `src`, `data-src`, `srcset`, etc.
    - Converts relative URLs to absolute
    - Caches results for 10 minutes
    - One-click copy to clipboard
    """)

st.title("Image Link Scraper")

with st.form("scrape_form"):
    url_input = st.text_input(
        "Enter URL to scrape",
        placeholder="https://example.com",
        help="Enter the full URL of the webpage to scrape images from"
    )

    submit_button = st.form_submit_button("Extract Images", use_container_width=False)

if submit_button:
    if not st.session_state.api_key:
        st.markdown('<div class="error-message">Please enter your Firecrawl API key in the sidebar</div>', unsafe_allow_html=True)
    elif not url_input:
        st.markdown('<div class="error-message">Please enter a URL to scrape</div>', unsafe_allow_html=True)
    elif not validators.url(url_input):
        st.markdown('<div class="error-message">Please enter a valid URL</div>', unsafe_allow_html=True)
    else:
        cache_key = f"{st.session_state.api_key[:8]}:{url_input}"
        cached_result = get_cached_result(cache_key)

        if cached_result:
            image_urls = cached_result
            st.markdown('<div class="success-message">Results loaded from cache</div>', unsafe_allow_html=True)
        else:
            with st.spinner("Scraping webpage..."):
                try:
                    client = FirecrawlClient(st.session_state.api_key)
                    image_urls = client.scrape_images(url_input)

                    if image_urls:
                        set_cached_result(cache_key, image_urls)
                        st.markdown(f'<div class="success-message">Found {len(image_urls)} unique image(s)</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="error-message">No images found on this page</div>', unsafe_allow_html=True)

                except ValueError as e:
                    error_msg = str(e)
                    if "401" in error_msg:
                        st.markdown('<div class="error-message">Invalid API key. Please check your credentials.</div>', unsafe_allow_html=True)
                    elif "429" in error_msg:
                        st.markdown('<div class="error-message">Rate limit exceeded. Please try again later.</div>', unsafe_allow_html=True)
                    elif "timeout" in error_msg.lower():
                        st.markdown('<div class="error-message">Request timed out. The page may be too large or slow to load.</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="error-message">Error: {error_msg}</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.markdown(f'<div class="error-message">Unexpected error: {str(e)}</div>', unsafe_allow_html=True)
                    image_urls = []

        if "image_urls" in locals() and image_urls:
            st.markdown("### Extracted Image URLs")

            col1, col2 = st.columns([3, 1])

            with col2:
                try:
                    from st_copy_to_clipboard import st_copy_to_clipboard
                    st_copy_to_clipboard(
                        "\n".join(image_urls),
                        "Copy All URLs",
                        key="copy_button"
                    )
                except ImportError:
                    st.download_button(
                        label="Download URLs",
                        data="\n".join(image_urls),
                        file_name="image_urls.txt",
                        mime="text/plain"
                    )

            urls_text = "\n".join(image_urls)
            st.text_area(
                "Image URLs (one per line)",
                value=urls_text,
                height=400,
                disabled=False,
                label_visibility="collapsed"
            )