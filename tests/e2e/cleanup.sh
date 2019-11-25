#!/usr/bin/env bash

set -euo pipefail
IFS=$'\n\t'

readonly ARGS="$@"
readonly PROGNAME=$(basename $0)

readonly CURRENT_DIR="${BASH_SOURCE%/*}"
readonly OUTPUT_DIR="$CURRENT_DIR/output"
readonly JOBS_FILE="$OUTPUT_DIR/cleanup_jobs.txt"
readonly STORAGE_FILE="$OUTPUT_DIR/cleanup_storage.txt"

cleanup_jobs() {
  echo "Cleaning up jobs..."

  echo "Reading jobs file: $JOBS_FILE"
  local jobs=$([ -f "$JOBS_FILE" ] && cat "$JOBS_FILE" || true)
  echo "About to kill $(wc -w <<<"$jobs") jobs: $jobs"

  echo "-------"
  echo "Before:"
  neuro ps
  echo "-------"
  neuro kill "$jobs"
  echo "-------"
  echo "After:"
  neuro ps
  echo "-------"
  echo "Removing file $JOBS_FILE"
  rm "$JOBS_FILE"
  echo "OK"
}

cleanup_storage() {
  echo "Cleaning up storage..."

  echo "Reading storage file: $STORAGE_FILE"
  local dirs=$([ -f "$STORAGE_FILE" ] && cat "$STORAGE_FILE" || true)
  echo "About to remove $(wc -w <<<"$dirs") directories: $dirs"

  echo "-------"
  echo "Before:"
  neuro ls
  echo "-------"
  for d in $dirs; do neuro rm -r "$d"; done
  echo "-------"
  echo "After:"
  neuro ls
  echo "-------"
  echo "Removing file $STORAGE_FILE"
  rm "$STORAGE_FILE"
  echo "OK"
}

main() {
  if [ "${ARGS[0]}" == "jobs" ]; then
    cleanup_jobs
  elif [ "${ARGS[0]}" == "storage" ]; then
    cleanup_storage
  else
    echo "Usage: $PROGNAME [ jobs | storage ] "
    exit 1
  fi
}

main
