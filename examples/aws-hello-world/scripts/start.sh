#!/bin/bash

set -e

TEMP_DIR=/tmp
PYTHON_FILE_SERVER_ROOT="$TEMP_DIR/python-simple-http-webserver"
PID_FILE=server.pid
PORT=$(ctx node properties port)
URL="http://localhost:$PORT"

ctx logger info [ "Starting web server at: $PYTHON_FILE_SERVER_ROOT." ]

cd "$PYTHON_FILE_SERVER_ROOT"
nohup python -m SimpleHTTPServer "$PORT" > /dev/null 2>&1 &
echo $! > "$PID_FILE"

server_is_up() {
	if which wget >/dev/null; then
		if wget "$URL" >/dev/null; then
			return 0
		fi
	elif which curl >/dev/null; then
		if curl "$URL" >/dev/null; then
			return 0
		fi
	else
		ctx logger error [ "Both curl and wget were not found in path." ]
		exit 1
	fi
	return 1
}

ctx logger info [ "Waiting for web server to launch on port $PORT..." ]
STARTED=false
for i in $(seq 1 15)
do
	if server_is_up; then
		ctx logger info [ "Web server is up." ]
		STARTED=true
    	break
	else
		ctx logger info [ "Web server not up. waiting 1 second." ]
		sleep 1
	fi
done

if [ "$STARTED" = false ]; then
	ctx logger error [ "Web server did not start within 15 seconds." ]
	exit 1
fi
