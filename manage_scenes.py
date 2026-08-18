#!/usr/bin/env python3
"""Scene pack management and batch organization."""

import os
import shutil
from pathlib import Path

def setup_scenes():
    """Initialize scene pack structure."""
    scenes = [
        ("01_opening", "Opening - The Journal", "Handwritten journal with illustration"),
        ("02_bindings", "Bindings & Ribbons", "Book bindings detail transition"),
        ("03_landscape", "The Ancient Tree", "Main landscape with twisted tree"),
        ("04_tunnel", "Passage", "Dark archway leading through"),
        ("05_detail", "Journey", "Landscape detail and continuation")
    ]

    print("📁 Scene Pack Structure\n")

    for scene_id, name, desc in scenes:
        raw_path = Path(f"scenes/{scene_id}/raw")
        aligned_path = Path(f"scenes/{scene_id}/aligned")

        raw_path.mkdir(parents=True, exist_ok=True)
        aligned_path.mkdir(parents=True, exist_ok=True)

        print(f"✓ {scene_id}/")
        print(f"  ├─ raw/      (place your images here)")
        print(f"  ├─ aligned/  (auto-generated)")
        print(f"  └─ {name}")
        print(f"     {desc}\n")

def list_images():
    """Show current image inventory."""
    print("\n📸 Image Inventory\n")

    total_images = 0
    for scene_dir in sorted(Path("scenes").iterdir()):
        if scene_dir.is_dir():
            raw_dir = scene_dir / "raw"
            if raw_dir.exists():
                images = list(raw_dir.glob("*.jpg")) + list(raw_dir.glob("*.png"))
                count = len(images)
                total_images += count

                status = "✓" if count > 0 else "○"
                print(f"{status} {scene_dir.name}: {count} image(s)")
                for img in sorted(images):
                    print(f"   → {img.name}")

    print(f"\nTotal: {total_images} images ready")
    return total_images > 0

def show_commands():
    """Display usage commands."""
    print("\n🚀 Next Steps:\n")
    print("1. Place images in scenes/XX_name/raw/ directories")
    print("2. Run: python align_and_render.py")
    print("3. Video output: output/aligned_storyboard.mp4\n")

if __name__ == "__main__":
    setup_scenes()
    if list_images():
        print("\n✨ Ready to render!")
    show_commands()
