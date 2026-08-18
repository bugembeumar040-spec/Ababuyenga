#!/usr/bin/env python3
"""
Batch image alignment and video rendering for scene sequences.
Aligns images per scene pack and creates a finished video.
"""

import os
import sys
from PIL import Image
import subprocess
from pathlib import Path
import json

def get_scene_metadata():
    """Define scene sequence and properties."""
    return {
        "scenes": [
            {
                "id": "01_opening",
                "name": "Opening - The Journal",
                "duration": 3.0,  # seconds per frame
                "description": "Handwritten journal with illustration"
            },
            {
                "id": "02_bindings",
                "name": "Bindings & Ribbons",
                "duration": 2.5,
                "description": "Book bindings detail transition"
            },
            {
                "id": "03_landscape",
                "name": "The Ancient Tree",
                "duration": 4.0,
                "description": "Main landscape with twisted tree"
            },
            {
                "id": "04_tunnel",
                "name": "Passage",
                "duration": 3.5,
                "description": "Dark archway leading through"
            },
            {
                "id": "05_detail",
                "name": "Journey",
                "duration": 3.0,
                "description": "Landscape detail and continuation"
            }
        ],
        "output": {
            "fps": 24,
            "resolution": "1920x1080",
            "format": "mp4",
            "codec": "libx264",
            "preset": "medium"
        }
    }

def normalize_image(input_path, output_path, target_size=(1920, 1080)):
    """Align and normalize image: resize, pad, and standardize."""
    if not os.path.exists(input_path):
        print(f"⚠️  Missing: {input_path}")
        return False

    img = Image.open(input_path).convert('RGB')

    # Calculate aspect ratio
    img_ratio = img.width / img.height
    target_ratio = target_size[0] / target_size[1]

    if img_ratio > target_ratio:
        # Image is wider - fit to width
        new_width = target_size[0]
        new_height = int(new_width / img_ratio)
    else:
        # Image is taller - fit to height
        new_height = target_size[1]
        new_width = int(new_height * img_ratio)

    # Resize
    img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Create canvas and center image
    canvas = Image.new('RGB', target_size, color=(245, 240, 235))  # Warm cream
    x = (target_size[0] - new_width) // 2
    y = (target_size[1] - new_height) // 2
    canvas.paste(img_resized, (x, y))

    canvas.save(output_path, quality=95)
    print(f"✓ Aligned: {os.path.basename(output_path)}")
    return True

def create_image_sequence(aligned_dir, fps=24, duration=3.0):
    """Create duplicate frames for video duration at target fps."""
    frame_count = int(fps * duration)
    image = Image.open(aligned_dir)

    frames = [image for _ in range(frame_count)]
    return frames

def batch_align_scenes(scene_meta):
    """Process all scenes: align images and prepare for video."""
    all_frames = []
    fps = scene_meta["output"]["fps"]

    for scene in scene_meta["scenes"]:
        scene_id = scene["id"]
        raw_dir = f"scenes/{scene_id}/raw"
        aligned_dir = f"scenes/{scene_id}/aligned"

        os.makedirs(aligned_dir, exist_ok=True)

        # Find images in raw directory
        images = sorted([f for f in os.listdir(raw_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])

        if not images:
            print(f"\n⚠️  No images in {raw_dir}")
            continue

        print(f"\n📦 Scene: {scene['name']}")

        for img_file in images:
            input_path = os.path.join(raw_dir, img_file)
            output_path = os.path.join(aligned_dir, img_file)

            if normalize_image(input_path, output_path):
                # Add frames for this image's duration
                frame_count = int(fps * scene["duration"])
                frames = create_image_sequence(output_path, fps, scene["duration"])
                all_frames.extend(frames)

    return all_frames

def render_video(frames, output_file, fps=24):
    """Render frame sequence to video file."""
    if not frames:
        print("❌ No frames to render!")
        return False

    temp_dir = "temp_frames"
    os.makedirs(temp_dir, exist_ok=True)

    print(f"\n🎬 Rendering {len(frames)} frames to video...")

    # Save frames
    for i, frame in enumerate(frames):
        frame.save(f"{temp_dir}/frame_{i:06d}.png")

    # Create video with ffmpeg
    cmd = [
        'ffmpeg', '-y',
        '-framerate', str(fps),
        '-i', f'{temp_dir}/frame_%06d.png',
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-preset', 'medium',
        output_file
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ ffmpeg error: {result.stderr}")
        return False

    print(f"✓ Video created: {output_file}")

    # Cleanup
    subprocess.run(['rm', '-rf', temp_dir])

    return True

def main():
    print("🎨 Batch Image Alignment & Video Renderer\n")

    scene_meta = get_scene_metadata()

    print("📋 Scene Configuration:")
    for scene in scene_meta["scenes"]:
        print(f"  • {scene['id']}: {scene['name']} ({scene['duration']}s)")

    print("\n⚙️  Aligning images per scene...")
    frames = batch_align_scenes(scene_meta)

    if frames:
        output_file = "output/aligned_storyboard.mp4"
        os.makedirs("output", exist_ok=True)

        if render_video(frames, output_file, scene_meta["output"]["fps"]):
            print(f"\n✨ Success! Video: {output_file}")
            print(f"   Frames: {len(frames)}")
            print(f"   FPS: {scene_meta['output']['fps']}")
            print(f"   Duration: {len(frames) / scene_meta['output']['fps']:.1f}s")
    else:
        print("❌ No images processed. Check scene/*/raw directories.")

if __name__ == "__main__":
    main()
