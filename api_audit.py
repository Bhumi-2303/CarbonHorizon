import os
import re

print("==== FRONTEND APIs ====")
for root, _, files in os.walk("frontend/src/api"):
    for f in files:
        if f.endswith(".ts"):
            with open(os.path.join(root, f), "r") as file:
                content = file.read()
                # Find all apiClient.post, .get, etc.
                matches = re.findall(r'apiClient\.(get|post|put|patch|delete)\(([^,]+)', content)
                if matches:
                    print(f"--- {f} ---")
                    for method, url in matches:
                        print(f"{method.upper()} {url.strip()}")

print("\n==== BACKEND APIs ====")
for root, _, files in os.walk("backend/app/routes"):
    for f in files:
        if f.endswith(".py"):
            with open(os.path.join(root, f), "r") as file:
                content = file.read()
                matches = re.findall(r'@router\.(get|post|put|patch|delete)\("([^"]+)"', content)
                if matches:
                    print(f"--- {f} ---")
                    for method, url in matches:
                        print(f"{method.upper()} {url}")
