import bcrypt
hashed = "$2b$12$Fh71r2oFTPBMNrSU5aUO1OAtE3DdC/lpx0bHw0w9T5tSp3y3akD4W".encode()
passwords = [
    "password", "password123", "Password123", "Password123!", "admin",
    "TestUser", "TestUser123", "test@example.com", "Test@example.com"
]
for p in passwords:
    if bcrypt.checkpw(p.encode(), hashed):
        print("FOUND:", p)
        break
else:
    print("Not found")
