#!/bin/bash

# Define the input XML file

input_file="allI.mpd"

# Extract the media presentation duration in seconds
duration=$(grep -oP '(?<=mediaPresentationDuration=")[^"]*' "$input_file")
hours=$(echo "$duration" | grep -oP '(?<=PT)\d+(?=H)' || echo "0")
minutes=$(echo "$duration" | grep -oP '(?<=H)\d+(?=M)|(?<=PT)\d+(?=M)' || echo "0")
seconds=$(echo "$duration" | grep -oP '\d+\.\d+(?=S)|\d+(?=S)' || echo "0")
total_seconds=$(echo "$hours*3600 + $minutes*60 + $seconds" | bc)

# Process each video Representation
grep -oP '(?<=<Representation id=")\d+(?=.*mimeType="video)' "$input_file" | while read -r rep_id; do
echo $rep_id

    # Calculate the total bytes
    total_bytes=$(du -ab enc_allI_chunk-stream$rep_id* 2>/dev/null | awk '{total += $1} END {print total}')
    echo $total_bytes

    if [ -n "$total_bytes" ]; then
        # Calculate total bits and divide by total seconds to get the new bandwidth
        total_bits=$(echo "$total_bytes*8" | bc)
        new_bandwidth=$(echo "$total_bits/$total_seconds" | bc)
        echo "$new_bandwidth"

        # Update the XML file with the new bandwidth and keep the original bandwidth
        sed -i -r "/<Representation id=\"$rep_id\"/ s/(bandwidth=\")([0-9]+)/\1$new_bandwidth\" origbandwidth=\"\2/" "$input_file"
    fi
done

echo "File has been updated with new bandwidth values."

