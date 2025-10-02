import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def make_session(user_agent: str, token: str) -> requests.Session:
    """Build a requests.Session with retry/backoff + headers preloaded."""
    session = requests.Session()

    # --- retry policy ---
    retries = Retry(
        total=5,                       # max attempts
        backoff_factor=1.5,            # exponential backoff: 1.5s, 3s, 4.5s...
        status_forcelist=[429, 502, 503, 504],
        allowed_methods=["GET", "HEAD"],
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    # --- default headers ---
    session.headers.update({
        "User-Agent": user_agent,
        "Authorization": f"Discogs token={token}",
    })

    return session

