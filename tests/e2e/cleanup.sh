#!/usr/bin/env bash

CURRENT_DIR="${BASH_SOURCE%/*}"
OUTPUT_DIR="$CURRENT_DIR/output"
STORAGE_FILE="$OUTPUT_DIR/cleanup_storage.txt"

echo "Cleaning up storage..."

echo "Reading storage file: $STORAGE_FILE"
dirs=$([ -f $STORAGE_FILE ] && cat $STORAGE_FILE | tr -d "\r" || true)
echo "About to remove $(wc -w <<< $dirs) directories: $dirs"

echo "-------"
echo "Before:"
neuro ls
echo "-------"
for d in $dirs; do neuro rm -r $d; done
echo "-------"
echo "Removing file $STORAGE_FILE"
rm $STORAGE_FILE
echo "OK"
