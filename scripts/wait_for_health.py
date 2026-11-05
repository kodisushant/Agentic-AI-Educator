"""
Wait for backend /health endpoint to respond with status 200.
Cross-platform helper used by start_all.bat and start_all.sh.
"""

import sys
import time
import urllib.request
import json

DEFAULT_URL = "http://localhost:8000/health"
DEFAULT_TIMEOUT = 30.0


def wait_for_health(url=DEFAULT_URL, timeout=DEFAULT_TIMEOUT):
    start = time.time()
    print(f"Waiting for backend at {url} to become ready...", end="", flush=True)

    while time.time() - start < timeout:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "HealthCheck/1.0"})
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    print(f" ONLINE! (mode: {'MOCK' if data.get('mock_mode') else 'REAL'})")
                    return True
        except Exception:
            pass

        print(".", end="", flush=True)
        time.sleep(1.0)

    print("\n[ERROR] Timed out waiting for backend to start.")
    return False


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL
    timeout = float(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_TIMEOUT
    success = wait_for_health(url, timeout)
    sys.exit(0 if success else 1)
