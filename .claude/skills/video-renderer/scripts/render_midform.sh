#!/bin/bash
# Render midform video (16:9 horizontal)
# Usage: ./render_midform.sh --bg bg.jpg --audio vo.mp3 --captions captions.srt --output output.mp4

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
    echo "Usage: render_midform.sh --bg BG --audio AUDIO [--captions CAPTIONS] --output OUTPUT"
    exit 1
fi

# Get audio duration
DURATION=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$AUDIO")

# Build filter complex
if [[ -n "$CAPTIONS" && -f "$CAPTIONS" ]]; then
    # With subtitles (soft subs via -c:s)
    ffmpeg -y \
        -loop 1 -i "$BG" \
        -i "$AUDIO" \
        -i "$CAPTIONS" \
        -filter_complex \
        "[0:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,format=yuv420p[bg]; \
         [1:a]loudnorm=I=-16:TP=-1.5:LRA=11[audio]" \
        -map "[bg]" -map "[audio]" -map 2 \
        -t "$DURATION" \
        -r 30 \
        -c:v libx264 -crf 19 -preset medium -pix_fmt yuv420p \
        -c:a aac -b:a 192k \
        -c:s mov_text \
        "$OUTPUT"
else
    # Without captions
    ffmpeg -y \
        -loop 1 -i "$BG" \
        -i "$AUDIO" \
        -filter_complex \
        "[0:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,format=yuv420p[bg]; \
         [1:a]loudnorm=I=-16:TP=-1.5:LRA=11[audio]" \
        -map "[bg]" -map "[audio]" \
        -t "$DURATION" \
        -r 30 \
        -c:v libx264 -crf 19 -preset medium -pix_fmt yuv420p \
        -c:a aac -b:a 192k \
        "$OUTPUT"
fi

# Output metadata
echo "{"
echo "  \"video_file\": \"$OUTPUT\","
echo "  \"resolution\": \"1920x1080\","
echo "  \"fps\": 30,"
echo "  \"duration_sec\": $DURATION,"
echo "  \"file_size_mb\": $(du -m "$OUTPUT" | cut -f1)"
echo "}"