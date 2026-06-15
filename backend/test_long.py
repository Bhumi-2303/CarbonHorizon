import bcrypt
plain = "a" * 80
try:
    hashed = bcrypt.hashpw(plain.encode(), bcrypt.gensalt())
    print("Hashed successfully")
except Exception as e:
    print("Error:", type(e), e)
