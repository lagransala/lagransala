#!/usr/bin/env python3
"""
Clear all file cache for the application.

Usage:
    python scripts/clear_cache.py

This script deletes all contents of the .cache/ directory at the project root.
"""

from pathlib import Path

# (label, directory) of every file cache used by the application
CACHE_DIRS = [
    ("fetch", ".cache/fetch"),
    ("extract", ".cache/extract"),
    ("groq chat completion", ".cache/groq_chat_completion"),
]


def cache_status(cache_dir):
    # Don't instantiate FileCacheBackend here: it creates the directory.
    cache_path = Path(cache_dir)
    if not cache_path.exists():
        return {
            "exists": False,
            "file_count": 0,
            "total_size": 0,
        }
    files = list(cache_path.glob("*.json"))
    file_count = len(files)
    total_size = sum(f.stat().st_size for f in files)
    return {
        "exists": True,
        "file_count": file_count,
        "total_size": total_size,
    }


def print_status():
    print("\nCache status:")
    statuses = [
        (label, cache_dir, cache_status(cache_dir)) for label, cache_dir in CACHE_DIRS
    ]
    total_size = sum(status["total_size"] for _, _, status in statuses)
    print(f"-  Total size: {total_size / 1024 / 1024:.1f} MB")

    for label, cache_dir, status in statuses:
        print(f"- {cache_dir} - {label}")
        if not status["exists"]:
            print("  - cache directory does not exist.")
            continue
        print(f"  - files: {status['file_count']}")
        if status["total_size"] < 1024:
            print(f"  - total size: {status['total_size']} B")
        elif status["total_size"] < 1024 * 1024:
            print(f"  - total size: {status['total_size'] / 1024:.0f} KB")
        else:
            print(f"  - total size: {status['total_size'] / 1024 / 1024:.1f} MB")


def clear_cache_dir(cache_dir):
    cache_path = Path(cache_dir)
    if not cache_path.exists():
        print(f"[skip] cache directory {cache_dir} does not exist.")
        return
    count = 0
    for file in cache_path.glob("*.json"):
        try:
            file.unlink()
            count += 1
        except Exception as e:
            print(f"[error] could not delete {file}: {e}")
    print(f"Cleared {count} cache files in {cache_dir}")


def main():
    print_status()
    resp = (
        input("\nDo you want to clear ALL cache files listed above? [y/N]: ")
        .strip()
        .lower()
    )
    if resp not in ("y", "yes"):
        print("Aborted. No cache was deleted.")
        return
    for _, cache_dir in CACHE_DIRS:
        clear_cache_dir(cache_dir)


if __name__ == "__main__":
    main()
