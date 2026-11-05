"""
Service verification script.
Tests that port 8000 (Backend), port 3000 (Classroom), and port 3001 (Dashboard) respond correctly.
"""

import sys
import time
import urllib.request

ENDPOINTS = [
    ("Backend Health", "http://localhost:8000/health"),
    ("Backend Docs", "http://localhost:8000/docs"),
    ("Classroom Frontend", "http://localhost:3000/"),
    ("Learner Dashboard", "http://localhost:3001/"),
    ("Learner Summary API", "http://localhost:8000/learner/summary/demo_student"),
    ("Mock Lesson API", "http://localhost:8000/mock/lesson"),
]

def check_endpoint(name, url):
    try:
        t0 = time.time()
        req = urllib.request.Request(url, headers={"User-Agent": "Tester/1.0"})
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            elapsed = (time.time() - t0) * 1000
            content = resp.read()
            print(f"  [PASS] {name:<22} -> HTTP {resp.status} ({elapsed:.1f}ms, {len(content)} bytes)")
            return True
    except Exception as e:
        print(f"  [FAIL] {name:<22} -> ERROR: {e}")
        return False

def main():
    print("Testing AI Virtual Teacher Services:")
    all_ok = True
    for name, url in ENDPOINTS:
        ok = check_endpoint(name, url)
        if not ok:
            all_ok = False
    
    if all_ok:
        print("\nAll 6 endpoints verified healthy and responsive!")
        sys.exit(0)
    else:
        print("\nSome endpoints failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
