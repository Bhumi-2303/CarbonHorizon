from pydantic import BaseModel, EmailStr
class UserInfo(BaseModel):
    email: EmailStr

user = UserInfo(email="Test.User@Example.COM")
print("Parsed email:", user.email)
