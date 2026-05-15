import requests
res = requests.post("http://localhost:7000/auth/login", json={"username": "admin", "password": "admin123"})
if "token" not in res.json():
    print("Login failed:", res.text)
    exit(1)
token = res.json()["token"]
headers = {"Authorization": f"Bearer {token}"}
print("STATS:", requests.get("http://localhost:7000/stats", headers=headers).text)
print("ANTENNES:", requests.get("http://localhost:7000/antennes", headers=headers).text[:200])
print("PREDICT:", requests.get("http://localhost:7000/predict", headers=headers).text[:200])
