import sys
import signal
from waitress import serve
import main

def handler(signum, frame):
    sys.exit(1)

signal.signal(signal.SIGTERM, handler)
serve(main.app, host="0.0.0.0", port=5000)


