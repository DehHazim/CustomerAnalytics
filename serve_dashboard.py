from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import socket
import sys


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from customer_analytics.pipeline import run_pipeline


def find_port(start: int = 8000, end: int = 8010) -> int:
    for port in range(start, end + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            if probe.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise RuntimeError("No available port found between 8000 and 8010")


def main() -> None:
    result = run_pipeline()
    port = find_port()
    handler = partial(SimpleHTTPRequestHandler, directory=PROJECT_ROOT)
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)

    print("Customer Analytics dashboard is running.")
    print(f"Open: http://127.0.0.1:{port}/dashboard/")
    print(f"SQLite warehouse: {result['database']}")
    server.serve_forever()


if __name__ == "__main__":
    main()
