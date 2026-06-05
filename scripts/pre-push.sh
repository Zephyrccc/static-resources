#!/bin/sh
#
# Git pre-push hook to convert images to WebP
# Calls the Node.js conversion script
#

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(git rev-parse --show-toplevel)"

# Run the Node.js conversion script
echo "Running pre-push image conversion..."
node "$REPO_DIR/scripts/convert-to-webp.js"

if [ $? -eq 0 ]; then
    echo "Image conversion completed successfully."
    exit 0
else
    echo "Warning: Image conversion encountered errors, but continuing with push."
    exit 0
fi