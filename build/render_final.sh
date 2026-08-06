#!/bin/bash
# Final composite: base cut + caption layer (streamed as raw RGBA) + mix.
set -e
cd "$(dirname "$0")"
mkdir -p ../out

render () {   # $1 = audio track, $2 = output
  python3 render_overlay.py | ffmpeg -v error -y \
    -i base.mp4 \
    -f rawvideo -pix_fmt rgba -s 1080x1920 -r 24 -i - \
    -i "$1" \
    -filter_complex "[0:v][1:v]overlay=0:0:format=auto,
                     fade=t=in:st=0:d=0.125,
                     fade=t=out:st=58.2:d=0.3,
                     format=yuv420p[v]" \
    -map "[v]" -map 2:a \
    -c:v libx264 -profile:v high -level 4.0 -preset slow -crf 17 \
    -x264-params "keyint=48:min-keyint=24:scenecut=0" \
    -r 24 -c:a aac -b:a 192k -ar 48000 -ac 2 \
    -movflags +faststart -shortest "$2"
}

render media/mix.wav      ../out/deadbeat_short.mp4
render media/mix_nosfx.wav ../out/deadbeat_short_vo-only.mp4

# thumbnail candidates: the DEADBEAT frame and the isolated card
ffmpeg -v error -y -i ../out/deadbeat_short.mp4 -ss 6.0 -frames:v 1 -q:v 2 ../out/thumb_deadbeat.jpg
ffmpeg -v error -y -i base.mp4 -ss 16.6 -frames:v 1 -q:v 2 ../out/thumb_card.jpg

for f in ../out/deadbeat_short.mp4 ../out/deadbeat_short_vo-only.mp4; do
  echo "== $f"
  ffprobe -v error -show_entries format=duration,size,bit_rate \
    -show_entries stream=codec_name,width,height,r_frame_rate,nb_frames,channels,sample_rate \
    -of default=nw=1 "$f" | tr '\n' ' '; echo
done
