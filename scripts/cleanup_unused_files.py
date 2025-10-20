import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TARGET_FILES = [
    ROOT / "templates" / "create_trip.html",
    ROOT / "templates" / "create_trip_backup.html",
    ROOT / ".copilot-temp-delete-me",
    ROOT / "BUG_FIXES.md",
    ROOT / "DEBUG_TRIP_CREATION.md",
    ROOT / "DESIGN_IMPROVEMENTS.md",
    ROOT / "PROJECT_ANALYSIS.md",
    ROOT / "STYLING_GUIDE.md",
    ROOT / "TESTING_GUIDE.md",
]

TARGET_DIRS_EMPTY_ONLY = [
    ROOT / "handlers",
]

def safe_unlink(path: Path):
    try:
        if path.exists():
            path.unlink()
            print(f"Removed file: {path.relative_to(ROOT)}")
    except IsADirectoryError:
        # Skip directories here
        pass
    except Exception as e:
        print(f"Could not remove {path}: {e}")

def remove_empty_dir(path: Path):
    try:
        if path.exists() and path.is_dir() and not any(path.iterdir()):
            path.rmdir()
            print(f"Removed empty directory: {path.relative_to(ROOT)}")
    except Exception as e:
        print(f"Could not remove directory {path}: {e}")

def main():
    for p in TARGET_FILES:
        safe_unlink(p)

    for d in TARGET_DIRS_EMPTY_ONLY:
        remove_empty_dir(d)

if __name__ == "__main__":
    main()
