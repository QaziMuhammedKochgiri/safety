import pytest
import asyncio
import os
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from dotenv import load_dotenv

# Load environment variables before any application imports
load_dotenv()

from backend import get_db
from backend.server import app
from backend.models import Client
from backend.auth import get_password_hash, create_access_token

@pytest.fixture
def mock_forensic_file(tmp_path):
    """Creates a temporary mock forensic file for testing uploads."""
    file_path = tmp_path / "mock_forensic.db"
    file_path.write_text("This is a mock forensic database file content.")
    return file_path

@pytest.fixture(scope="session", autouse=True)
async def seed_landmark_cases(db_connection: AsyncIOMotorDatabase):
    """Seed the database with landmark cases for the entire test session."""
    await db_connection.landmark_cases.delete_many({})
    await db_connection.landmark_cases.insert_many([
        {
            "caseNumber": "LC2023001",
            "title": "Major Cyberbullying Case",
            "summary": "A landmark ruling on social media harassment.",
            "url": "https://example.com/case/lc2023001"
        },
        {
            "caseNumber": "LC2023002",
            "title": "Online Predator Prosecution",
            "summary": "Key legal precedents for prosecuting online predators.",
            "url": "https://example.com/case/lc2023002"
        }
    ])

# Prevent the app's lifespan from running during tests


@pytest.fixture(scope="session")
def event_loop_policy():
    """Return the event loop policy."""
    return asyncio.get_event_loop_policy()

@pytest_asyncio.fixture(scope="session")
async def db_connection() -> AsyncIOMotorDatabase:
    """Create a session-scoped asynchronous database connection."""
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = client[os.environ['DB_NAME']]
    yield db
    client.close()

@pytest_asyncio.fixture(scope="session")
async def async_client() -> AsyncClient:
    """Create a session-scoped async client."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

@pytest_asyncio.fixture(scope="function", autouse=True)
async def clear_database(db_connection: AsyncIOMotorDatabase):
    """Clear the database before each test."""
    for collection in await db_connection.list_collection_names():
        if collection not in ["landmark_cases", "clients"]:
            await db_connection[collection].delete_many({})
    yield
    # After each test, clear the data again (except for collections managed by session-scoped fixtures)
    for collection in await db_connection.list_collection_names():
        if collection not in ["landmark_cases", "clients"]:
            await db_connection[collection].delete_many({})


@pytest_asyncio.fixture(scope="session")
def override_get_db(db_connection: AsyncIOMotorDatabase):
    """Override the get_db dependency to use the test database."""
    async def _override_get_db():
        return db_connection
    return _override_get_db

@pytest_asyncio.fixture(scope="session", autouse=True)
def apply_db_override(override_get_db):
    """Apply the database override to the app."""
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()



@pytest_asyncio.fixture(scope="session")
async def create_admin_user_fixture(db_connection: AsyncIOMotorDatabase):
    """Ensure an admin user exists once per session."""
    admin_user_client_number = "ADM2025001"
    admin_email = "testadmin@example.com"

    # Ensure admin user is deleted before creation to handle potential stale data from previous runs
    await db_connection.clients.delete_many({"clientNumber": admin_user_client_number})

    admin_user = Client(
        clientNumber=admin_user_client_number,
        firstName="Admin",
        lastName="User",
        email=admin_email,
        phone="123456789",
        country="Testland",
        caseType="Admin",
        hashedPassword=get_password_hash("testadminpass"),
        role="admin"
    )
    await db_connection.clients.insert_one(admin_user.model_dump())
    return admin_user

@pytest_asyncio.fixture(scope="session")
async def test_client_token(async_client: AsyncClient, db_connection: AsyncIOMotorDatabase) -> dict:
    """Create a test client and return their token (runs once per session)."""
    client_email = "testclient@example.com"
    client_password = "testclientpass"

    await db_connection.clients.delete_many({"email": client_email}) # Ensure client is deleted before creation

    register_data = {
        "firstName": "Test", "lastName": "Client", "email": client_email,
        "password": client_password, "phone": "1234567890",
        "country": "Testland", "caseType": "General"
    }
    response = await async_client.post("/api/auth/register", json=register_data)

    if response.status_code != 200:
        # If already registered from a previous run, try to log in
        if "Email already registered" in response.text:
            login_data = {"email": client_email, "password": client_password}
            response = await async_client.post("/api/auth/login", json=login_data)
            if response.status_code != 200:
                raise Exception(f"Failed to login test client after registration attempt: {response.text}")
        else:
            raise Exception(f"Failed to register test client: {response.text}")

    login_data = {"email": client_email, "password": client_password}
    response = await async_client.post("/api/auth/login", json=login_data)
    assert response.status_code == 200
    token_data = response.json()
    return {"access_token": token_data["access_token"], "client_number": token_data["clientNumber"], "email": client_email}

@pytest_asyncio.fixture(scope="session")
async def admin_token_fixture(async_client: AsyncClient, create_admin_user_fixture: Client, db_connection: AsyncIOMotorDatabase) -> str:
    """Logs in as admin and returns their JWT token (runs once per session)."""
    admin_user = create_admin_user_fixture # Use the already created admin user

    found_admin_in_db = await db_connection.clients.find_one({"clientNumber": admin_user.clientNumber})

    if not found_admin_in_db:
        raise Exception("Admin user not found in database. Check create_admin_user_fixture.")

    login_data = {
        "email": admin_user.email,
        "password": "testadminpass"  # Default password set in create_admin_user_fixture
    }
    response = await async_client.post("/api/auth/login", json=login_data)
    if response.status_code != 200:
        raise Exception(f"Failed to log in as admin: {response.text}")
    return response.json()["access_token"]