#!/bin/bash
# Render shorts video (9:16 vertical)
# Usage: ./render_shorts.sh --bg bg.jpg --audio vo.mp3 --captions captions.ass --output output.mp4

set -e

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --bg) BG="$2"; shift 2;;
        --audio) AUDIO="$2"; shift 2;;
        --captions) CAPTIONS="$2"; shift 2;;
        --output) OUTPUT="$2"; shift 2;;
        *) echo "Unknown option: $1"; exit 1;;
    esac
done

# Validate inputs
if [[ -z "$BG" || -z "$AUDIO" || -z "$OUTPUT" ]]; then
    echo "Usage: render_shorts.sh --bg BG --audio AUDIO [--captions CAPTIONS] --output OUTPUT"
    exit 1
fi

# Get audio duration
DURATION=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$AUDIO")

# Build filter complex
if [[ -n "$CAPTIONS" && -f "$CAPTIONS" ]]; then
    # With captions (burn-in)
    ffmpeg -y \
        -loop 1 -i "$BG" \
        -i "$AUDIO" \
        -filter_complex \
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,format=yuv420p[bg]; \
         [1:a]loudnorm=I=-16:TP=-1.5:LRA=11[audio]; \
         [bg]ass=$CAPTIONS[video]" \
        -map "[video]" -map "[audio]" \
        -t "$DURATION" \
        -r 30 \
        -c:v libx264 -crf 19 -preset medium -pix_fmt yuv420p \
        -c:a aac -b:a 160k \
        "$OUTPUT"
else
    # Without captions
    ffmpeg -y \
        -loop 1 -i "$BG" \
        -i "$AUDIO" \
        -filter_complex \
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,format=yuv420p[bg]; \
         [1:a]loudnorm=I=-16:TP=-1.5:LRA=11[audio]" \
        -map "[bg]" -map "[audio]" \
        -t "$DURATION" \
        -r 30 \
        -c:v libx264 -crf 19 -preset medium -pix_fmt yuv420p \
        -c:a aac -b:a 160k \
        "$OUTPUT"
fi

# Output metadata
echo "{"
echo "  \"video_file\": \"$OUTPUT\","
echo "  \"resolution\": \"1080x1920\","
echo "  \"fps\": 30,"
echo "  \"duration_sec\": $DURATION,"
echo "  \"file_size_mb\": $(du -m "$OUTPUT" | cut -f1)"
echo "}"