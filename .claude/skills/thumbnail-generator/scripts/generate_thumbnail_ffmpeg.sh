#!/bin/bash
# Generate thumbnail using ffmpeg + ImageMagick
# Usage: ./generate_thumbnail_ffmpeg.sh --cover cover.jpg --text "Hook Text" --output thumb.jpg

set -e

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --cover) COVER="$2"; shift 2;;
        --text) TEXT="$2"; shift 2;;
        --output) OUTPUT="$2"; shift 2;;
        --bg-color) BG_COLOR="$2"; shift 2;;
        *) echo "Unknown option: $1"; exit 1;;
    esac
done

# Defaults
BG_COLOR="${BG_COLOR:-#1a1a2e}"
TEXT_COLOR="#ffffff"
FONT="Arial-Bold"

# Validate inputs
if [[ -z "$COVER" || -z "$TEXT" || -z "$OUTPUT" ]]; then
    echo "Usage: generate_thumbnail_ffmpeg.sh --cover COVER --text TEXT --output OUTPUT"
    exit 1
fi

# Create temporary directory
TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT

# Step 1: Create background (1280x720)
convert -size 1280x720 "xc:$BG_COLOR" "$TMPDIR/bg.png"

# Step 2: Resize and position book cover (left 40% = 512px width)
convert "$COVER" \
    -resize 450x630 \
    -gravity center \
    -background transparent \
    -extent 450x630 \
    "$TMPDIR/cover_resized.png"

# Step 3: Create text image (right 60%)
convert -size 700x600 "xc:$BG_COLOR" \
    -font "$FONT" \
    -pointsize 80 \
    -fill "$TEXT_COLOR" \
    -gravity center \
    -annotate 0 "$TEXT" \
    "$TMPDIR/text.png"

# Step 4: Composite everything
convert "$TMPDIR/bg.png" \
    "$TMPDIR/cover_resized.png" -geometry +30+45 -composite \
    "$TMPDIR/text.png" -geometry +530+60 -composite \
    -quality 90 \
    "$OUTPUT"

# Output metadata
SIZE=$(stat -f%z "$OUTPUT" 2>/dev/null || stat -c%s "$OUTPUT")
echo "{"
echo "  \"thumbnail_file\": \"$OUTPUT\","
echo "  \"hook_text\": \"$TEXT\","
echo "  \"resolution\": \"1280x720\","
echo "  \"file_size_bytes\": $SIZE,"
echo "  \"method\": \"ffmpeg+imagemagick\""
echo "}"