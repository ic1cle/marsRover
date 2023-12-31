#!/bin/bash
# Find the process ID of python3.5 marsRover.py
PID=$(pgrep -f "python3.5")

# Kill the process if it exists
if [ -n "$PID" ]; then
    kill -9 $PID
    echo "Process $PID killed."
else
    echo "Process not found."
fi