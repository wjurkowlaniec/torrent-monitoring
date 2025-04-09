#!/bin/bash

# serve_local.sh - Script to serve the torrent monitoring website locally
# Usage: ./serve_local.sh [port]
# Default port is 8000 if not specified

PORT=${1:-8000}
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1-2)

echo "🌐 Starting local web server on port $PORT..."
echo "📂 Serving from current directory"
echo "🔗 Access the website at: http://localhost:$PORT"
echo "🛑 Press Ctrl+C to stop the server"
echo ""

# Check Python version and use appropriate server command
if [[ $(echo "$PYTHON_VERSION >= 3.0" | bc) -eq 1 ]]; then
    # Python 3.x
    python3 -m http.server $PORT
else
    # Python 2.x (fallback)
    python -m SimpleHTTPServer $PORT
fi
