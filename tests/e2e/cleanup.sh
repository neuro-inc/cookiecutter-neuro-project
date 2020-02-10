#!/usr/bin/env bash

CURRENT_DIR="${BASH_SOURCE%/*}"
OUTPUT_DIR="$CURRENT_DIR/output"
JOBS_FILE="$OUTPUT_DIR/cleanup_jobs.txt"
STORAGE_FILE="$OUTPUT_DIR/cleanup_storage.txt"

echo "Cleaning up jobs..."

echo "Reading jobs file: $JOBS_FILE"
jobs=$([ -f $JOBS_FILE ] && cat $JOBS_FILE | tr -d "\r\\r" || true)
echo "About to kill $(wc -w <<< $jobs) jobs: $jobs"

echo "-------"
echo "Before:"
neuro -q ps
echo "-------"
neuro kill $jobs
echo "-------"
echo "After:"
neuro -q ps
echo "-------"
echo "Removing file $JOBS_FILE"
rm $JOBS_FILE
echo "OK"

echo "Cleaning up storage..."

echo "Reading storage file: $STORAGE_FILE"
dirs=$([ -f $STORAGE_FILE ] && cat $STORAGE_FILE | tr -d "\r\\r" || true)
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
