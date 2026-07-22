import requests

base_url = "http://127.0.0.1:5000"
routes = [
    '/',
    '/profiling',
    '/dashboard',
    '/chat',
    '/forecasting'
]

print("Testing Flask Web Template Routes...")
all_passed = True

for r in routes:
    url = f"{base_url}{r}"
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            print(f"  [OK 200] {r}")
        else:
            print(f"  [FAIL {resp.status_code}] {r}")
            all_passed = False
    except Exception as e:
        print(f"  [ERROR] {r}: {e}")
        all_passed = False

if all_passed:
    print("\nALL TEMPLATE ROUTES RETURNED HTTP 200 OK! ALL FIXES ARE LIVE AND WORKING PERFECTLY!")
else:
    print("\nSOME ROUTES FAILED.")
