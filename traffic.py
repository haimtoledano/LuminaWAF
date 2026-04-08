import requests, time

try:
    res = requests.post('http://localhost:8555/api/virtual-servers/', json={
        'name':'Demo Site', 
        'ingress_port':8005, 
        'backend_target':'example.com:80', 
        'waf_mode':'Blocking', 
        'protection_sqli':True, 
        'protection_xss':True, 
        'log_retention_days':7
    })
    print("Created VS:", res.status_code)
except Exception as e:
    print(e)

time.sleep(2) # Map envoy
try:
    requests.post('http://localhost:8005/login', data='{"username":"admin", "password":"password123"}', headers={'Content-Type':'application/json'})
    requests.post('http://localhost:8005/submit', data='<script>alert("xss")</script>', headers={'Content-Type':'text/plain'})
    requests.get('http://localhost:8005/?id=1%20UNION%20SELECT%20NULL')
except Exception as e:
    print("Error doing requests", e)
