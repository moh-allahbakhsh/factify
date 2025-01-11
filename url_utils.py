from urllib.parse import urlparse, urljoin

def standardize_url(url):
    """Standardizes a URL."""
    parsed_url = urlparse(url)
    standardized_url = urljoin(
        f"{parsed_url.scheme or 'https'}://",
        parsed_url.netloc,
        parsed_url.path
    )
    return standardized_url