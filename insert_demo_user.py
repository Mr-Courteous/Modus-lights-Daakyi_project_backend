import pymongo
from bson.objectid import ObjectId
import sys
sys.path.append('.')  # Ensure backend modules are importable

from mvp1_auth import MVP1AuthService

# MongoDB connection (update db name if needed)
client = pymongo.MongoClient("mongodb://root:rootpassword@localhost:27017/admin?authSource=admin")
db = client["admin"]  # Use the correct database name
users = db["users"]

# Demo user credentials
username = "demo"
email = "demo@demo.com"
password = "demopassword"
role = "admin"  # Change to another valid role if needed
full_name = "Demo User"

# Hash password using your app's logic
hashed_password = MVP1AuthService.hash_password(password)

demo_user = {
    "_id": ObjectId(),
    "username": username,
    "email": email,
    "password_hash": hashed_password,
    "role": role,
    "full_name": full_name,
    "active": True
}

if not users.find_one({"username": username}):
    users.insert_one(demo_user)
    print("Demo user inserted.")
else:
    print("Demo user already exists.")
