"""
batch_local_files.py — Process local archive text files (medium/blogger) into OKF docs.

Usage:
    python batch_local_files.py <input_dir> <output_dir> [options]

Options:
    --author TEXT     Author display name (default: Adrian Cockcroft)
    --workers N       Parallel workers (default: 4)
    --no-llm          Skip LLM enrichment
    --anthropic-key   Anthropic API key
    --verbose         Verbose output
    --limit N         Process only first N files (for testing)
"""

import argparse
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


def process_file(file_path: Path, output_dir: Path, opts: argparse.Namespace) -> dict:
    python = sys.executable
    script = str(Path(__file__).parent / "processors" / "story_processor_v2.py")

    argv = [python, script, str(file_path), str(output_dir)]

    if opts.author:
        argv += ["--author", opts.author]
    if opts.anthropic_key:
        argv += ["--anthropic-key", opts.anthropic_key]
    if opts.no_llm:
        argv.append("--no-llm")
    if opts.verbose:
        argv.append("--verbose")

    try:
        result = subprocess.run(argv, capture_output=True, text=True, timeout=60)
        return {
            "file": file_path.name,
            "status": "done" if result.returncode == 0 else "error",
            "reason": result.stderr[-200:] if result.returncode != 0 else "",
        }
    except subprocess.TimeoutExpired:
        return {"file": file_path.name, "status": "error", "reason": "timeout"}
    except Exception as e:
        return {"file": file_path.name, "status": "error", "reason": str(e)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir", help="Directory with .txt files")
    parser.add_argument("output_dir", help="OKF output directory")
    parser.add_argument("--author", default="Adrian Cockcroft")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--no-llm", action="store_true")
    parser.add_argument("--anthropic-key", default=os.environ.get("ANTHROPIC_API_KEY"))
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    opts = parser.parse_args()

    input_dir = Path(opts.input_dir)
    output_dir = Path(opts.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find all text files, skip very short ones (likely comments/stubs)
    files = sorted(p for p in input_dir.glob("*.txt") if p.stat().st_size > 500)
    if opts.limit:
        files = files[: opts.limit]

    print(f"Processing {len(files)} files from {input_dir} → {output_dir}")
    print(f"Workers: {opts.workers}")
    print()

    n_done = n_error = 0
    with ThreadPoolExecutor(max_workers=opts.workers) as pool:
        futures = {pool.submit(process_file, f, output_dir, opts): f for f in files}
        for i, future in enumerate(as_completed(futures), 1):
            res = future.result()
            if res["status"] == "done":
                n_done += 1
                if opts.verbose:
                    print(f"  [{i}/{len(files)}] ✓ {res['file'][:60]}")
            else:
                n_error += 1
                print(f"  [{i}/{len(files)}] ✗ {res['file'][:60]} — {res['reason'][:80]}")

            if i % 20 == 0 or i == len(files):
                print(f"Progress: {i}/{len(files)} — done={n_done} errors={n_error}")

    print(f"\nDone: {n_done} processed, {n_error} errors")


if __name__ == "__main__":
    main()
