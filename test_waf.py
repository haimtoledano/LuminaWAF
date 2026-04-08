import urllib.request
import urllib.error
import urllib.parse
import json

base_url = "http://localhost:8001/api/docs"

tests = [
    ("1. Standard Traffic", base_url, None),
    ("2. SQL Injection Payload", base_url + "?q=" + urllib.parse.quote("' OR 1=1 --"), None),
    ("3. XSS Payload", base_url + "?data=" + urllib.parse.quote("<script>alert('xss')</script>"), None),
]

print("Starting WAF Envoy Tests against localhost:8001...")
for name, url, data in tests:
    try:
        req = urllib.request.Request(url, data=data)
        response = urllib.request.urlopen(req)
        print(f"[PASS] {name} -> HTTP {response.status}")
        # Note: WAF blocks usually return 403, standard traffic returns 200
    except urllib.error.HTTPError as e:
        print(f"[BLOCKED] {name} -> HTTP {e.code}")
    except urllib.error.URLError as e:
        print(f"[ERROR] {name} -> Failed: {e.reason}")
    except Exception as e:
        print(f"[FATAL ERROR] {name} -> {e}")
