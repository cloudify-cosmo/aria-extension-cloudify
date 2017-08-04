#!/bin/bash

set -e

TEMP_DIR=/tmp
PYTHON_FILE_SERVER_ROOT="$TEMP_DIR/python-simple-http-webserver"
INDEX_PATH=index.html
IMAGE_PATH=images/aria-logo.png

if [ -d "$PYTHON_FILE_SERVER_ROOT" ]; then
	ctx logger info [ "Removing old web server root folder: $PYTHON_FILE_SERVER_ROOT." ]
	rm -rf "$PYTHON_FILE_SERVER_ROOT"
fi

ctx logger info [ "Creating web server root folder: $PYTHON_FILE_SERVER_ROOT." ]

mkdir -p "$PYTHON_FILE_SERVER_ROOT"
cd "$PYTHON_FILE_SERVER_ROOT"

ctx logger info [ "Downloading service template resources..." ]
ctx download-resource-and-render [ "$PYTHON_FILE_SERVER_ROOT/index.html" "$INDEX_PATH" ]
ctx download-resource [ "$PYTHON_FILE_SERVER_ROOT/aria-logo.png" "$IMAGE_PATH" ]
