#!/bin/bash
set -e
set -o pipefail

# Specify the file containing the URLs
url_file="urls.txt"

# Read each line of the file
while IFS= read -r url
do
    # Generate a filename by replacing all non-alphanumeric characters with _
    filename=$(echo "$url" | sed 's/[^a-zA-Z0-9]/_/g')

    # Append the hash of the URL to the filename to avoid collisions
    hash=$(echo -n "$url" | sha256sum | cut -d' ' -f1)
    filename="${filename}_${hash}.json"

    # Run your Python script and redirect its output to a file
    python3 main.py --json "$url" > "$filename"
done < "$url_file"
