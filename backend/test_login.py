import sys
import bcrypt

hashed = "$2b$12$Fh71r2oFTPBMNrSU5aUO1OAtE3DdC/lpx0bHw0w9T5tSp3y3akD4W"
password = "password123"

# verify_password logic from security.py
def verify_password(plain: str, hashed: str) -> bool:
    print(f"DEBUG: plain={plain}")
    print(f"DEBUG: hashed={hashed}")
    print(f"DEBUG: hashed length={len(hashed)}")
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception as e:
        print(f"EXCEPTION: {e}")
        return False

print(f"Valid: {verify_password(password, hashed)}")
