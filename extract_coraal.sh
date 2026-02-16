#!/usr/bin/env bash

DATA_DIR="./"   # change if needed
cd "$DATA_DIR" || exit 1

echo "Starting CORAAL extraction (flattening data/ folders)..."

for file in *.tar.gz; do
    [ -e "$file" ] || continue

    basename="${file%.tar.gz}"

    # Component = prefix before first underscore
    component="${basename%%_*}"

    echo "Processing $file → $component/"

    mkdir -p "$component"

    # Extract
    tar -xzf "$file" -C "$component"

    # After extraction, flatten any */data/ directories
    find "$component" -type d -name "data" | while read -r datadir; do
        echo "Flattening $datadir"
        mv "$datadir"/* "$component"/
        rmdir "$datadir"
    done
done

echo "Done."
