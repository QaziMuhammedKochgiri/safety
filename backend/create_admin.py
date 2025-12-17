"""
Create admin user for SafeChild Admin Panel
Run once to create initial admin account
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path
from passlib.context import CryptContext
import uuid

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_admin():
    """Create admin user"""
    print("--- Starting create_admin script ---")
    try:
        mongo_url = os.environ.get('MONGO_URL')
        if not mongo_url:
            print("❌ MONGO_URL environment variable not found.")
            return
            
        print(f"🔗 Connecting to MongoDB at: {mongo_url}")
        client = AsyncIOMotorClient(mongo_url)
        db = client[os.environ.get('DB_NAME', 'safechild')]
        
        # Test connection
        await client.admin.command('ping')
        print("✅ MongoDB connection successful.")

        # Admin credentials
        admin_email = "admin@safechild.mom"
        admin_password = "AdminPass2025!"  # Change this in production!
        
        # Check if admin exists
        print(f"🔍 Checking for existing admin: {admin_email}")
        existing_admin = await db.clients.find_one({"email": admin_email})
        if existing_admin:
            print(f"⚠️  Admin already exists: {admin_email}")
            return
        
        # Create admin user
        print("👤 Creating new admin user...")
        admin_user = {
            "id": str(uuid.uuid4()),
            "clientNumber": "SC2025ADMIN",
            "firstName": "Admin",
            "lastName": "SafeChild",
            "email": admin_email,
            "phone": "+9647700557879",
            "country": "Netherlands",
            "caseType": "admin",
            "hashedPassword": pwd_context.hash(admin_password),
            "role": "admin",
            "status": "active",
            "createdAt": asyncio.get_event_loop().time(),
            "updatedAt": asyncio.get_event_loop().time()
        }
        
        await db.clients.insert_one(admin_user)
        
        print("✅ Admin user created successfully!")
        print(f"   Email: {admin_email}")
        print(f"   Password: {admin_password}")
        print(f"   Client Number: SC2025ADMIN")
        print("\n⚠️  IMPORTANT: Change the password after first login!")
        
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
    finally:
        if 'client' in locals() and client:
            client.close()
            print("🚪 MongoDB connection closed.")
        print("--- Script finished ---")

if __name__ == "__main__":
    asyncio.run(create_admin())
