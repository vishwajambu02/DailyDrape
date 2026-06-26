"""
Rename script for Daily Drape outfit photos.
Renames every file in static/outfits/ that starts with '..._sunny_...'
to use 'hot' instead, matching what app.py expects.

Usage:
    Place this script in your DailyDrape project root (same level as app.py)
    Run:  python rename_sunny_to_hot.py

It's safe to run multiple times — files already using 'hot' are skipped.
"""
import os

OUTFIT_FOLDER = os.path.join("static", "outfits")

def main():
    if not os.path.isdir(OUTFIT_FOLDER):
        print(f"❌ Folder not found: {OUTFIT_FOLDER}")
        print("   Run this script from your DailyDrape project root.")
        return

    renamed = 0
    skipped = 0

    for filename in os.listdir(OUTFIT_FOLDER):
        if "_sunny_" in filename:
            new_filename = filename.replace("_sunny_", "_hot_")
            old_path = os.path.join(OUTFIT_FOLDER, filename)
            new_path = os.path.join(OUTFIT_FOLDER, new_filename)

            if os.path.exists(new_path):
                print(f"⚠️  Skipped (target already exists): {filename}")
                skipped += 1
                continue

            os.rename(old_path, new_path)
            print(f"✅ {filename}  →  {new_filename}")
            renamed += 1
        else:
            skipped += 1

    print(f"\nDone. Renamed {renamed} file(s), skipped {skipped} file(s).")

if __name__ == "__main__":
    main()
    