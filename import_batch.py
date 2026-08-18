#!/usr/bin/env python3
"""
Import and organize batch images from source to scene packs.
Usage: python import_batch.py <source_dir>
"""

import sys
import os
import shutil
from pathlib import Path

def organize_batch(source_dir):
    """Organize batch of images into scene structure."""
    if not os.path.isdir(source_dir):
        print(f"❌ Source directory not found: {source_dir}")
        return False

    source_path = Path(source_dir)
    images = sorted(source_path.glob("*.jpg")) + sorted(source_path.glob("*.png"))

    if not images:
        print(f"❌ No images found in {source_dir}")
        return False

    print(f"📸 Found {len(images)} images\n")

    # Map images to scenes based on order
    scene_mapping = [
        ("01_opening", "Opening - The Journal"),
        ("02_bindings", "Bindings & Ribbons"),
        ("03_landscape", "The Ancient Tree"),
        ("04_tunnel", "Passage"),
        ("05_detail", "Journey")
    ]

    for idx, img_file in enumerate(images):
        if idx < len(scene_mapping):
            scene_id, scene_name = scene_mapping[idx]
            dest_dir = Path(f"scenes/{scene_id}/raw")
            dest_path = dest_dir / img_file.name

            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(img_file, dest_path)

            print(f"✓ {img_file.name}")
            print(f"  → scenes/{scene_id}/raw/")
            print(f"  Scene: {scene_name}\n")
        else:
            print(f"⚠️  Skipped (no scene): {img_file.name}")

    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python import_batch.py <source_directory>")
        print("Example: python import_batch.py ./downloads")
        sys.exit(1)

    source = sys.argv[1]
    if organize_batch(source):
        print("✨ Import complete! Run: python align_and_render.py")
    else:
        sys.exit(1)
