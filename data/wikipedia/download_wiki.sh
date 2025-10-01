#!/usr/bin/env bash
set -euo pipefail

# Simple English Wikipedia dump base URL
BASE_URL="https://dumps.wikimedia.org/simplewiki/latest"

FILES=(
  "md5sums.txt"
  "simplewiki-latest-pages-articles-multistream.xml.bz2"
  "simplewiki-latest-pages-articles-multistream-index.txt.bz2"
  "simplewiki-latest-pages-articles-multistream.xml"
)

echo "📥 Downloading Simple English Wikipedia dump files into $(pwd)"

for f in "${FILES[@]}"; do
  echo "Downloading $f ..."
  curl -L -O "$BASE_URL/$f"
done

echo "✅ All files downloaded."

# Verify checksums
if command -v md5sum >/dev/null 2>&1; then
  echo "🔍 Verifying checksums..."
  md5sum -c md5sums.txt --ignore-missing
else
  echo "⚠️ md5sum not found, skipping checksum verification."
fi

echo "🎉 Done. Files are ready in $(pwd)"

