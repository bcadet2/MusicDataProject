#!/usr/bin/env python3
"""
Pipeline Runner

Orchestrates the execution of ETL pipeline steps defined in steps.py.

Usage:
    python pipelines/make_pipeline.py --list
    python pipelines/make_pipeline.py --only populate_seed_labels
    python pipelines/make_pipeline.py --from-step normalize_releases
    python pipelines/make_pipeline.py --from-step fetch_releases --to-step link_songs
    python pipelines/make_pipeline.py --force
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

# Import steps module
# Handles both: python pipelines/make_pipeline.py and python -m pipelines.make_pipeline
import sys
from pathlib import Path

_pipelines_dir = Path(__file__).resolve().parent
_project_root = _pipelines_dir.parent

# Ensure project root is in path for imports
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# Import steps (works because pipelines/ is in project root)
try:
    from pipelines import steps
except ImportError:
    # Fallback: if running directly from pipelines directory
    import steps


def _outputs_exist(required_outputs: tuple[Path, ...]) -> bool:
    """Check if all required output files exist."""
    if not required_outputs:
        return False
    return all(p.exists() for p in required_outputs)


def run_step(step: steps.Step, *, force: bool) -> int:
    """
    Execute a single pipeline step.
    
    Args:
        step: The Step object to execute
        force: If True, run even if outputs exist
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    # Skip if outputs exist and not forcing
    #TODO: Add a check to see if file has been updated in the last 24 hours or 
    # if not force and _outputs_exist(tuple(step.required_outputs)):
    #     print(f"[SKIP] {step.name} - outputs already exist")
    #     return 0

    # Check if script exists
    script_path = step.script_path
    if not script_path.exists():
        print(f"[FAIL] {step.name} - missing script: {script_path}")
        return 2

    # Build command
    cmd = [sys.executable, str(script_path), *step.args]
    print(f"[RUN ] {step.name}")
    print(f"       {' '.join(cmd)}")

    # Execute step
    t0 = time.time()
    proc = subprocess.run(cmd, cwd=script_path.parent.parent)
    dt = time.time() - t0

    # Check result
    if proc.returncode != 0:
        print(f"[FAIL] {step.name} - exit code: {proc.returncode}, time: {dt:.2f}s")
        return proc.returncode

    print(f"[OK  ] {step.name} - completed in {dt:.2f}s")
    return 0


def main(argv: list[str] | None = None) -> int:
    """
    Main entry point for pipeline runner.
    
    Args:
        argv: Command line arguments (for testing)
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    ap = argparse.ArgumentParser(
        description="Run ETL pipeline steps",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --list
  %(prog)s --only populate_seed_labels
  %(prog)s --from-step normalize_releases
  %(prog)s --from-step fetch_releases --to-step link_songs
  %(prog)s --force
        """
    )
    ap.add_argument(
        "--from-step",
        dest="from_step",
        default=None,
        help="Start pipeline from this step (inclusive)"
    )
    ap.add_argument(
        "--to-step",
        dest="to_step",
        default=None,
        help="End pipeline at this step (inclusive)"
    )
    ap.add_argument(
        "--only",
        dest="only",
        default=None,
        help="Run only this step"
    )
    ap.add_argument(
        "--force",
        action="store_true",
        help="Force re-execution even if outputs exist"
    )
    ap.add_argument(
        "--list",
        action="store_true",
        help="List all pipeline steps and exit"
    )
    
    args = ap.parse_args(argv)

    # Get pipeline steps
    pipe = steps.pipeline()

    # List steps and exit
    if args.list:
        print("\nPipeline Steps:")
        print("=" * 70)
        for i, s in enumerate(pipe, start=1):
            outputs_str = ", ".join(str(p.name) for p in s.required_outputs[:2])
            if len(s.required_outputs) > 2:
                outputs_str += f", ... ({len(s.required_outputs)} total)"
            print(f"{i:02d}. {s.name:30} {s.script:30}")
            if s.required_outputs:
                print(f"    Outputs: {outputs_str}")
            if s.args:
                print(f"    Args: {' '.join(s.args)}")
        print("=" * 70)
        return 0

    # Filter steps based on arguments
    if args.only:
        pipe = [s for s in pipe if s.name == args.only]
        if not pipe:
            print(f"[FAIL] Unknown step: {args.only}")
            return 2

    if args.from_step:
        try:
            start_idx = next(i for i, s in enumerate(pipe) if s.name == args.from_step)
            pipe = pipe[start_idx:]
        except StopIteration:
            print(f"[FAIL] Unknown from-step: {args.from_step}")
            return 2

    if args.to_step:
        try:
            end_idx = next(i for i, s in enumerate(pipe) if s.name == args.to_step)
            pipe = pipe[:end_idx + 1]
        except StopIteration:
            print(f"[FAIL] Unknown to-step: {args.to_step}")
            return 2

    # Execute pipeline steps
    if not pipe:
        print("[WARN] No steps to execute")
        return 0

    print(f"\nExecuting {len(pipe)} pipeline step(s)...")
    print("=" * 70)

    for step in pipe:
        rc = run_step(step, force=args.force)
        if rc != 0:
            print(f"\n[FAIL] Pipeline failed at step: {step.name}")
            return rc

    print("\n" + "=" * 70)
    print("[DONE] Pipeline finished successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())