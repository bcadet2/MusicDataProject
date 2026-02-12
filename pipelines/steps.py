"""
Pipeline Steps Definition

Defines the Step dataclass and pipeline() function that returns
the ordered list of pipeline steps to execute.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

BASE_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = BASE_DIR / "scripts"
DATA_DIR = BASE_DIR / "data"

SEED_LABELS_CSV = DATA_DIR / "seeds" / "seed_labels.csv"
STAGED_DIR = DATA_DIR / "staged"
RELEASES_CSV = STAGED_DIR / "releases.csv"
LABELS_CSV = STAGED_DIR / "labels.csv"


@dataclass(frozen=True)
class Step:
    """Represents a single pipeline step."""
    name: str
    script: str
    args: Sequence[str] = field(default_factory=tuple)
    required_outputs: Sequence[Path] = field(default_factory=tuple)

    @property
    def script_path(self) -> Path:
        """Return the full path to the script."""
        return SCRIPTS_DIR / self.script


def pipeline() -> list[Step]:
    """
    Define the ETL pipeline steps in execution order.
    
    Returns:
        List of Step objects in execution order
    """
    return [
        # # Step 1: Populate seed labels
        # Step(
        #     name="populate_seed_labels",
        #     script="populate_seed_labels.py",
        #     args=(),
        #     required_outputs=(SEED_LABELS_CSV,),
        # ),

        # # Step 2: Fetch releases for all labels in seed_labels.csv
        # Step(
        #     name="fetch_releases",
        #     script="fetch_releases.py",
        #     args=(),
        #     required_outputs=(),  # Multiple files, hard to validate
        # ),

        # # Step 3: Normalize releases (generic, processes all labels from seed_labels.csv)
        # Step(
        #     name="normalize_releases",
        #     script="normalize_releases.py",
        #     args=(),
        #     required_outputs=(),  # Multiple files, hard to validate
        # ),

        # Step 4: Build releases dimension
        Step(
            name="releases_dimension",
            script="releases_dimension.py",
            args=(),
            required_outputs=(
                STAGED_DIR / "releases.csv",
                STAGED_DIR / "labels.csv",
            ),
        )
        #,

        # # Step 5: Link songs with artist keys
        # Step(
        #     name="link_songs",
        #     script="link_songs.py",
        #     args=(),
        #     required_outputs=(
        #         STAGED_DIR / "island_songs_linked_enhanced.csv",
        #     ),
        # ),

        # # Step 6: Link collaborations with artist and song keys
        # Step(
        #     name="link_collaborations",
        #     script="link_collaborations.py",
        #     args=(),
        #     required_outputs=(
        #         STAGED_DIR / "island_song_collaborators_enhanced.csv",
        #     ),
        # ),

        # # Step 7: Load to Neon database
        # Step(
        #     name="load_releases_to_neon",
        #     script="load_releases_to_neon.py",
        #     args=(),
        #     required_outputs=(),  # Database operations, no file outputs
        # ),

        # # Step 8: Create warehouse views
        # Step(
        #     name="create_warehouse_views",
        #     script="create_warehouse_views.py",
        #     args=(),
        #     required_outputs=(),  # Database operations, no file outputs
        # ),
    ]