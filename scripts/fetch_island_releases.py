from __future__ import annotations
import os, json, time, argparse, sys, traceback
from pathlib import Path
from typing import Iterator, Set, Dict, Any

import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = BASE_DIR / "env" / "discogs.env"
load_dotenv(ENV_FILE)

TOKEN = os.getenv("DISCOGS_TOKEN")
UA = os.getenv("USER_AGENT", "MusicDataProject/0.1 (+mailto:bhenzelc@gmail.com)")
ISLAND_LABEL_ID = int(os.getenv("ISLAND_LABEL_ID", "8377"))  # Island Records main id

RAW_RELEASES_DIR = BASE_DIR / "data" / "raw" / "island_releases"
RAW_RELEASES_DIR.mkdir(parents=True, exist_ok=True)

# include common Island variants so we validate after fetch
ISLAND_LABEL_IDS = {8377, 48794, 27385, 27585, 93244, 63313}

def make_session() -> requests.Session:
    if not TOKEN:
        raise RuntimeError(f"Missing DISCOGS_TOKEN (looked in {ENV_FILE}).")
    if not UA or "@" not in UA:
        # Discogs is picky about User-Agent; include contact info
        raise RuntimeError("USER_AGENT must be descriptive and include contact info, e.g. "
                           "'MusicDataProject/0.1 (+mailto:you@example.com)'.")
    s = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=1.5,
        status_forcelist=[429, 502, 503, 504],
        allowed_methods={"GET", "HEAD"},
        respect_retry_after_header=True,
    )
    ad = HTTPAdapter(max_retries=retries)
    s.mount("https://", ad)
    s.mount("http://", ad)
    s.headers.update({
        "User-Agent": UA,
        "Authorization": f"Discogs token={TOKEN}",
        "Accept": "application/json",
    })
    return s

SESSION = make_session()

def _polite_sleep(resp: requests.Response, floor_seconds: float = 1.0) -> None:
    """Sleep a bit to stay under rate limit using Discogs headers when present."""
    try:
        remaining = int(resp.headers.get("X-Discogs-Ratelimit-Remaining", "1"))
        reset = int(resp.headers.get("X-Discogs-Ratelimit-Reset", "1"))
        if remaining <= 1 and reset > 0:
            time.sleep(reset + 0.5)
            return
    except Exception:
        pass
    time.sleep(floor_seconds)

def label_release_ids(label_id: int, per_page: int = 100) -> Iterator[int]:
    """Yield unique 'release' ids for a label via /labels/{id}/releases."""
    page, seen = 1, set()
    while page <= 50: #while true:
        print(f"[IDS] label {label_id} page {page}", flush=True)
        r = SESSION.get(
            f"https://api.discogs.com/labels/{label_id}/releases",
            params={"page": page, "per_page": per_page},
            timeout=30,
        )
        r.raise_for_status()
        payload = r.json()
        rows = payload.get("releases") or []
        print(f"[IDS] got {len(rows)} rows", flush=True)
        for rec in rows:
            rid = rec.get("id")
            if isinstance(rid, int) and rid not in seen:
                seen.add(rid)
                yield rid
        pages = int((payload.get("pagination") or {}).get("pages") or 1)
        if page >= pages:
            print("[IDS] done", flush=True)
            break
        page += 1
        _polite_sleep(r)

def fetch_release_detail(release_id: int) -> Dict[str, Any]:
    """Fetch full release object via /releases/{id}."""
    r = SESSION.get(f"https://api.discogs.com/releases/{release_id}", timeout=30)
    r.raise_for_status()
    _polite_sleep(r)
    return r.json()

def already_downloaded(release_id: int) -> bool:
    return (RAW_RELEASES_DIR / f"{release_id}.json").exists()

def save_release_json(release_id: int, data: dict) -> Path:
    print("release")
    out = RAW_RELEASES_DIR / f"{release_id}.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return out

def is_island_release(detail: dict) -> bool:
    return any((lab.get("id") in ISLAND_LABEL_IDS) for lab in (detail.get("labels") or []))

def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label-id", type=int, default=ISLAND_LABEL_ID,
                    help="Discogs label id to ingest (default: 8377 Island Records)")
    ap.add_argument("--limit", type=int, default=0,
                    help="Stop after saving N new releases (0 = no limit)")
    args = ap.parse_args(argv)

    print(f"[BOOT] BASE_DIR={BASE_DIR}")
    print(f"[BOOT] RAW_RELEASES_DIR={RAW_RELEASES_DIR}")
    print(f"[BOOT] USER_AGENT ok={bool(UA)}  TOKEN ok={bool(TOKEN)}", flush=True)

    saved, skipped, errors = 0, 0, 0
    try:
        for rid in label_release_ids(args.label_id):
            if already_downloaded(rid):
                # fast resume
                print(f"[SKIP] {rid} exists", flush=True)
                skipped += 1
                continue
            try:
                detail = fetch_release_detail(rid)
            except requests.HTTPError as e:
                print(f"[HTTP] {rid}: {e}", flush=True)
                errors += 1
                continue

            if not is_island_release(detail):
                print(f"[SKIP] {rid} not Island after validate", flush=True)
                skipped += 1
                continue

            save_release_json(rid, detail)
            print(f"[OK] {rid}  {detail.get('title','?')}", flush=True)
            saved += 1
            if args.limit and saved >= args.limit:
                break
    except KeyboardInterrupt:
        print("\n[INTERRUPTED] stopping early", flush=True)
    finally:
        print(f"[SUMMARY] saved={saved} skipped={skipped} errors={errors}", flush=True)
    return 0 if errors == 0 else 1

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        traceback.print_exc()
        raise

