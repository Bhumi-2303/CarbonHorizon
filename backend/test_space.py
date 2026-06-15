import bcrypt
plain = "password123"
hashed = bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()
hashed_space = hashed + " "

try:
    print(bcrypt.checkpw(plain.encode(), hashed_space.encode()))
except Exception as e:
    print("Error:", e)
