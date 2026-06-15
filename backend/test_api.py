import requests

def test():
    # Registration
    req = {
        "full_name": "Test User",
        "email": "Test@example.com",
        "password": "Password123!"
    }
    r = requests.post("http://localhost:8000/api/v1/auth/register", json=req)
    print("Register:", r.status_code, r.text)

    # Login
    req_login = {
        "email": "Test@example.com",
        "password": "Password123!"
    }
    r = requests.post("http://localhost:8000/api/v1/auth/login", json=req_login)
    print("Login:", r.status_code, r.text)

test()
