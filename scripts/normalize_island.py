from __future__ import annotations
import csv, json
from pathlib import Path
from typing import Iterable
import re
import json

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_RELEASES_DIR = BASE_DIR / "data" / "raw" / "island_releases"
STAGED_DIR = BASE_DIR / "data" / "staged"
STAGED_DIR.mkdir(parents=True, exist_ok=True)

# Output files
SONGS_CSV = STAGED_DIR / "songs.csv"
COLLABS_CSV = STAGED_DIR / "song_collaborators.csv"
ARTISTS_CSV = STAGED_DIR / "artists.csv"
#TODO, normalize island labels
LABELS_CSV = STAGED_DIR / "labels.csv"
# TODO, normalize island releases
# RELEASES_CSV = STAGED_DIR / "releases.csv"

# Output files for Island Records only
ISLAND_SONGS_CSV = STAGED_DIR / "island_songs.csv"
ISLAND_COLLABS_CSV = STAGED_DIR / "island_song_collaborators.csv"
ISLAND_ARTISTS_CSV = STAGED_DIR / "island_artists.csv"
#TODO, normalize island labels
# ISLAND_LABELS_CSV = STAGED_DIR / "island_labels.csv"
# TODO, normalize island releases
# ISLAND_RELEASES_CSV = STAGED_DIR / "island_releases.csv"

# Regex to filter for Island Records
ISLAND_LABEL_RE = re.compile(
    r"\bIsland\s+Records(?:\s+(?:Group|UK|U\.?S\.?A?|America|Limited|Ltd\.?|LLC|Inc\.?|Recordings))?\b"
    r"|"
    r"\bIsland\s+Def\s+Jam\b",
    re.I
)
NOT_GEO_RE = re.compile(r"(?:Rhode|Long)\s+Island\s+Records", re.I)


# todo: add more roles as we see patterns
ROLE_MAP = {
    "main_artist": ["Main Artist", "Lead Artist", "Artist"],
    "guest_vocalist": ["Guest Vocals", "Featuring", "Ft.", "Feat.", "With"],
    "backup_vocalist": ["Backing Vocals", "Background Vocals", "Harmony Vocals"],
    "writer": ["Written-By", "Lyrics By", "Composer", "Music By", "Words By"],
    "producer": ["Producer", "Produced By", "Co-Producer", "Executive Producer"],
    "instrumentalist": ["Guitar", "Bass", "Drums", "Piano", "Keyboards", "Saxophone", "Trumpet"],
    "engineer": ["Engineer", "Recording Engineer", "Mixing Engineer", "Mastering Engineer"]
}

def iter_release_files() -> Iterable[Path]:
    yield from RAW_RELEASES_DIR.glob("*.json")

def normalize_role(raw_role: str) -> str:
    """Map raw Discogs role to category."""
    if not raw_role:
        return "main_artist"
    
    role_lower = raw_role.lower()
    for category, variants in ROLE_MAP.items():
        for variant in variants:
            if variant.lower() in role_lower:
                return category
    return "other"

def use_regex(input_text):
    pattern = re.compile(r"Island Records", re.IGNORECASE)
    return pattern.match(input_text)

def main():
    # Open writers
    with SONGS_CSV.open("w", newline="", encoding="utf-8") as f_songs, \
         COLLABS_CSV.open("w", newline="", encoding="utf-8") as f_collabs, \
         ARTISTS_CSV.open("w", newline="", encoding="utf-8") as f_art, \
         ISLAND_SONGS_CSV.open("w", newline="", encoding="utf-8") as f_island_songs, \
         ISLAND_COLLABS_CSV.open("w", newline="", encoding="utf-8") as f_island_collabs, \
         ISLAND_ARTISTS_CSV.open("w", newline="", encoding="utf-8") as f_island_art:
        # Open writers
        songs_w = csv.writer(f_songs)
        coll_w = csv.writer(f_collabs)
        art_w  = csv.writer(f_art)
        island_songs_w = csv.writer(f_island_songs)
        island_coll_w = csv.writer(f_island_collabs)
        island_art_w = csv.writer(f_island_art)

        # Write headers
        songs_w.writerow(["song_id","release_id","track_position","title","duration","main_artist"])
        coll_w.writerow(["song_id","person_name","raw_role","role_category","is_main_artist","is_guest"])
        art_w.writerow(["person_name","artist_type","first_appearance_release"])

        # Write headers for Island Records 
        island_songs_w.writerow(["song_id","release_id","track_position","title","duration","main_artist"])
        island_coll_w.writerow(["song_id","person_name","raw_role","role_category","is_main_artist","is_guest"])
        island_art_w.writerow(["person_name","artist_type","first_appearance_release"])


        seen_artists = set()
        song_seq, island_song_seq, island_releases, skipped_releases = 0, 0, 0, 0
        
        for path in iter_release_files():
            with path.open(encoding="utf-8") as f:
                rel = json.load(f)

            release_id = rel.get("id")
            
            # Filter for Island Records only
            labels = rel.get("labels", [])
            is_island_release = any(
                label.get("name", "").lower() == "island records" 
                for label in labels
            )
            if not is_island_release:
                is_island_release = ISLAND_LABEL_RE.search(rel.get("title", ""))
            if not is_island_release:
                is_island_release = NOT_GEO_RE.search(rel.get("title", ""))

            labels = rel.get("labels", [])
            is_island_release = any(
                (name := label.get("name", "")) 
                and ISLAND_LABEL_RE.search(name) 
                and not NOT_GEO_RE.search(name)
                for label in labels
            )
            
            if not is_island_release:
                skipped_releases += 1
                continue
                
            island_releases += 1
            if is_island_release:
                print(f"[OK] {release_id} is an Island Records release")
                # island_songs_w.writerow([song_id, release_id, position, title, duration, main_artist])
                island_releases += 1
                song_seq += 1
                tracklist = rel.get("tracklist") or []
                
                # Get main artist from release level
                main_artist = ""
                release_artists = rel.get("artists") or []
                if release_artists:
                    main_artist = (release_artists[0].get("name") or "").strip()
                
                for track in tracklist:
                    # Use track position for song_id
                    position = (track.get("position") or "").strip()
                    song_id = f"{release_id}_{position}"

                    title = (track.get("title") or "").strip()
                    duration = (track.get("duration") or "").strip()
                    
                    island_songs_w.writerow([song_id, release_id, position, title, duration, main_artist])

                    
                    # Extract main artists as collaborators (from release level)
                    for artist in release_artists:
                        name = (artist.get("name") or "").strip()
                        if not name:
                            continue
                        island_coll_w.writerow([song_id, name, "", "main_artist", True, False])
                        if name not in seen_artists:
                            island_art_w.writerow([name, "main_artist", release_id])
                            seen_artists.add(name)

                    # Extract extraartists (credits)
                    extras = track.get("extraartists") or []
                    for ea in extras:
                        name = (ea.get("name") or "").strip()
                        role = (ea.get("role") or "").strip()
                        if not name:
                            continue
                        role_cat = normalize_role(role)
                        is_guest = role_cat in ["guest_vocalist", "guest_writer"]
                        island_coll_w.writerow([song_id, name, role, role_cat, False, is_guest])
                        if name not in seen_artists:
                            island_art_w.writerow([name, role_cat, release_id])
                            seen_artists.add(name)

    print(f"\n=== ISLAND RECORDS FILTERING RESULTS ===")
    print(f"Island Records releases processed: {island_releases}")
    print(f"Non-Island releases skipped: {skipped_releases}")
    print(f"Total songs extracted: {song_seq}")
    print(f"Unique artists found: {len(seen_artists)}")
    print(f"\n[OK] wrote:\n - {ISLAND_SONGS_CSV}\n - {ISLAND_COLLABS_CSV}\n - {ISLAND_ARTISTS_CSV}")

if __name__ == "__main__":
    main()
