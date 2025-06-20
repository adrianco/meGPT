#!/bin/bash

# Check if an author argument is provided
if [ $# -ne 1 ]; then
    echo "Usage: $0 <author_name>"
    echo "Example: $0 virtual_adrianco"
    exit 1
fi

AUTHOR=$1
CSV_FILE="authors/${AUTHOR}/published_content.csv"
OUTPUT_DIR="downloads/${AUTHOR}/video"

# Check if the CSV file exists
if [ ! -f "$CSV_FILE" ]; then
    echo "Error: Cannot find published_content.csv at ${CSV_FILE}"
    exit 1
fi

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Check if yt-dlp is installed
if ! command -v yt-dlp &> /dev/null; then
    echo "Error: yt-dlp is not installed. Please install it first:"
    echo "pip install yt-dlp"
    exit 1
fi

echo "Processing YouTube videos with subkind 'transcript' for author: ${AUTHOR}"
echo "Reading from: ${CSV_FILE}"
echo "Saving to: ${OUTPUT_DIR}"
echo

# Use Python to properly parse the CSV file and output in a shell-safe format
python3 -c '
import csv
import sys

with open(sys.argv[1], "r") as f:
    reader = csv.reader(f)
    next(reader)  # Skip header
    for row in reader:
        if len(row) >= 6:  # Ensure we have all required fields
            # Print fields separated by a character unlikely to appear in the data
            print("␟".join(row))
' "$CSV_FILE" | while IFS="␟" read -r kind subkind what where published url; do
    # Check if this is a YouTube entry with subkind "transcript"
    if [ "$kind" = "youtube" ] && [ "$subkind" = "transcript" ]; then
        echo "Processing: $what"
        echo "URL: $url"
        
        # Download using yt-dlp's default filename convention
        echo "Downloading to: $OUTPUT_DIR"
        yt-dlp \
            -P "$OUTPUT_DIR" \
            --embed-thumbnail \
            --embed-metadata \
            --no-overwrites \
            --download-archive "$OUTPUT_DIR/downloaded.txt" \
            "$url"
        
        echo "----------------------------------------"
    fi
done

echo "Download process completed!"
echo "Videos have been saved to: $OUTPUT_DIR" 