#!/usr/bin/env python3
"""
SafeChild Elderly User Test - Client Creation Script
Creates 20 test clients in MongoDB for E2E testing
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import Optional
import random
import string

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB connection
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "safechild")

# Test clients data
ELDERLY_TEST_CLIENTS = [
    {
        "id": "ELD-001",
        "firstName": "Helga",
        "lastName": "Muller",
        "age": 72,
        "device": "Samsung A14",
        "androidVersion": "13",
        "language": "de",
        "techLevel": "very_low",
        "specialCondition": "Gozluk, buyuk font",
        "phone": "+49151TEST0001",
        "email": "helga.muller@test.safechild.mom"
    },
    {
        "id": "ELD-002",
        "firstName": "Fatma",
        "lastName": "Yilmaz",
        "age": 68,
        "device": "Xiaomi Redmi 12",
        "androidVersion": "12",
        "language": "tr",
        "techLevel": "low",
        "specialCondition": "Okuma-yazma zayif",
        "phone": "+90532TEST0002",
        "email": "fatma.yilmaz@test.safechild.mom"
    },
    {
        "id": "ELD-003",
        "firstName": "Hans",
        "lastName": "Becker",
        "age": 75,
        "device": "Samsung A34",
        "androidVersion": "13",
        "language": "de",
        "techLevel": "medium",
        "specialCondition": "Isitme cihazi",
        "phone": "+49152TEST0003",
        "email": "hans.becker@test.safechild.mom"
    },
    {
        "id": "ELD-004",
        "firstName": "Hatice",
        "lastName": "Demir",
        "age": 70,
        "device": "Oppo A78",
        "androidVersion": "13",
        "language": "ku",  # Kurdish
        "techLevel": "very_low",
        "specialCondition": "Sadece Kurtce konusuyor",
        "phone": "+90533TEST0004",
        "email": "hatice.demir@test.safechild.mom"
    },
    {
        "id": "ELD-005",
        "firstName": "Werner",
        "lastName": "Schmidt",
        "age": 78,
        "device": "Nokia G22",
        "androidVersion": "12",
        "language": "de",
        "techLevel": "very_low",
        "specialCondition": "Parkinson (titreme)",
        "phone": "+49153TEST0005",
        "email": "werner.schmidt@test.safechild.mom"
    },
    {
        "id": "ELD-006",
        "firstName": "Emine",
        "lastName": "Kaya",
        "age": 65,
        "device": "Samsung A24",
        "androidVersion": "13",
        "language": "tr",
        "techLevel": "medium",
        "specialCondition": "WhatsApp biliyor",
        "phone": "+90534TEST0006",
        "email": "emine.kaya@test.safechild.mom"
    },
    {
        "id": "ELD-007",
        "firstName": "Gerhard",
        "lastName": "Weber",
        "age": 71,
        "device": "Motorola G54",
        "androidVersion": "13",
        "language": "de",
        "techLevel": "low",
        "specialCondition": "Buyuk parmak, kucuk buton",
        "phone": "+49154TEST0007",
        "email": "gerhard.weber@test.safechild.mom"
    },
    {
        "id": "ELD-008",
        "firstName": "Zehra",
        "lastName": "Arslan",
        "age": 74,
        "device": "Xiaomi Redmi Note 12",
        "androidVersion": "13",
        "language": "tr",
        "techLevel": "very_low",
        "specialCondition": "Telefon korkusu",
        "phone": "+90535TEST0008",
        "email": "zehra.arslan@test.safechild.mom"
    },
    {
        "id": "ELD-009",
        "firstName": "Ingrid",
        "lastName": "Fischer",
        "age": 69,
        "device": "Samsung A54",
        "androidVersion": "14",
        "language": "de",
        "techLevel": "medium",
        "specialCondition": "Teknoloji merakli",
        "phone": "+49155TEST0009",
        "email": "ingrid.fischer@test.safechild.mom"
    },
    {
        "id": "ELD-010",
        "firstName": "Mehmet",
        "lastName": "Ozturk",
        "age": 76,
        "device": "Huawei Nova Y61",
        "androidVersion": "12",
        "language": "tr",
        "techLevel": "low",
        "specialCondition": "Sadece arama yapar",
        "phone": "+90536TEST0010",
        "email": "mehmet.ozturk@test.safechild.mom"
    },
    {
        "id": "ELD-011",
        "firstName": "Ursula",
        "lastName": "Braun",
        "age": 73,
        "device": "Google Pixel 7a",
        "androidVersion": "14",
        "language": "de",
        "techLevel": "medium",
        "specialCondition": "Torun yardim ediyor",
        "phone": "+49156TEST0011",
        "email": "ursula.braun@test.safechild.mom"
    },
    {
        "id": "ELD-012",
        "firstName": "Ayse",
        "lastName": "Celik",
        "age": 80,
        "device": "Samsung A04",
        "androidVersion": "12",
        "language": "tr",
        "techLevel": "very_low",
        "specialCondition": "En yasli grupta",
        "phone": "+90537TEST0012",
        "email": "ayse.celik@test.safechild.mom"
    },
    {
        "id": "ELD-013",
        "firstName": "Dieter",
        "lastName": "Hoffmann",
        "age": 67,
        "device": "OnePlus Nord CE 3",
        "androidVersion": "13",
        "language": "de",
        "techLevel": "medium_high",
        "specialCondition": "Emekli muhendis",
        "phone": "+49157TEST0013",
        "email": "dieter.hoffmann@test.safechild.mom"
    },
    {
        "id": "ELD-014",
        "firstName": "Hacer",
        "lastName": "Sahin",
        "age": 71,
        "device": "Oppo A57",
        "androidVersion": "12",
        "language": "tr",
        "techLevel": "low",
        "specialCondition": "Sifre hatirlamiyor",
        "phone": "+90538TEST0014",
        "email": "hacer.sahin@test.safechild.mom"
    },
    {
        "id": "ELD-015",
        "firstName": "Monika",
        "lastName": "Wagner",
        "age": 66,
        "device": "Samsung A14",
        "androidVersion": "13",
        "language": "de",
        "techLevel": "medium",
        "specialCondition": "Avukat yonlendirmesi",
        "phone": "+49158TEST0015",
        "email": "monika.wagner@test.safechild.mom"
    },
    {
        "id": "ELD-016",
        "firstName": "Ibrahim",
        "lastName": "Aydogan",
        "age": 77,
        "device": "Xiaomi Poco M5",
        "androidVersion": "12",
        "language": "ar",  # Arabic
        "techLevel": "very_low",
        "specialCondition": "Arapca-Turkce karisik",
        "phone": "+90539TEST0016",
        "email": "ibrahim.aydogan@test.safechild.mom"
    },
    {
        "id": "ELD-017",
        "firstName": "Hildegard",
        "lastName": "Schneider",
        "age": 79,
        "device": "Nokia G42",
        "androidVersion": "13",
        "language": "de",
        "techLevel": "very_low",
        "specialCondition": "Artrit (eklem agrisi)",
        "phone": "+49159TEST0017",
        "email": "hildegard.schneider@test.safechild.mom"
    },
    {
        "id": "ELD-018",
        "firstName": "Gulsum",
        "lastName": "Yildiz",
        "age": 69,
        "device": "Realme C55",
        "androidVersion": "13",
        "language": "tr",
        "techLevel": "low",
        "specialCondition": "Kizi yardim ediyor",
        "phone": "+90540TEST0018",
        "email": "gulsum.yildiz@test.safechild.mom"
    },
    {
        "id": "ELD-019",
        "firstName": "Klaus",
        "lastName": "Richter",
        "age": 70,
        "device": "Samsung A34",
        "androidVersion": "13",
        "language": "de",
        "techLevel": "medium",
        "specialCondition": "Eski IT calisan",
        "phone": "+49160TEST0019",
        "email": "klaus.richter@test.safechild.mom"
    },
    {
        "id": "ELD-020",
        "firstName": "Sevim",
        "lastName": "Koc",
        "age": 82,
        "device": "Samsung A04e",
        "androidVersion": "12",
        "language": "tr",
        "techLevel": "very_low",
        "specialCondition": "EN ZOR CASE - en yasli, en dusuk spec",
        "phone": "+90541TEST0020",
        "email": "sevim.koc@test.safechild.mom"
    }
]

# Case types for random assignment
CASE_TYPES = [
    "Sorgerecht",      # Custody
    "Umgangsrecht",    # Visitation
    "Kindeswohl",      # Child welfare
    "Entfuhrung",      # Abduction
    "Entfremdung"      # Parental alienation
]


def generate_short_code(length: int = 6) -> str:
    """Generate a short alphanumeric code"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def generate_token() -> str:
    """Generate a unique token"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=32))


async def create_test_clients():
    """Create all test clients in MongoDB"""

    print("=" * 60)
    print("SafeChild Elderly User Test - Client Creation")
    print("=" * 60)
    print(f"MongoDB URL: {MONGO_URL}")
    print(f"Database: {DB_NAME}")
    print(f"Total clients to create: {len(ELDERLY_TEST_CLIENTS)}")
    print("=" * 60)

    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    # Collections
    clients_collection = db["clients"]
    collection_links_collection = db["collection_links"]

    # Clear existing test clients
    print("\n[1/4] Clearing existing test clients...")
    delete_result = await clients_collection.delete_many({"testId": {"$regex": "^ELD-"}})
    print(f"      Deleted {delete_result.deleted_count} existing test clients")

    delete_links = await collection_links_collection.delete_many({"testId": {"$regex": "^ELD-"}})
    print(f"      Deleted {delete_links.deleted_count} existing test links")

    # Create new clients
    print("\n[2/4] Creating test clients...")
    created_clients = []

    for i, client_data in enumerate(ELDERLY_TEST_CLIENTS, 1):
        # Generate unique codes
        short_code = generate_short_code()
        token = generate_token()

        # Create client document
        client_doc = {
            "testId": client_data["id"],
            "firstName": client_data["firstName"],
            "lastName": client_data["lastName"],
            "email": client_data["email"],
            "phone": client_data["phone"],
            "language": client_data["language"],
            "caseType": random.choice(CASE_TYPES),
            "status": "active",
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow(),
            # Test metadata
            "testMetadata": {
                "age": client_data["age"],
                "device": client_data["device"],
                "androidVersion": client_data["androidVersion"],
                "techLevel": client_data["techLevel"],
                "specialCondition": client_data["specialCondition"],
                "isTestClient": True,
                "testScenario": "elderly_user_test"
            }
        }

        # Insert client
        result = await clients_collection.insert_one(client_doc)
        client_id = str(result.inserted_id)

        # Create collection link
        link_doc = {
            "clientId": client_id,
            "testId": client_data["id"],
            "shortCode": short_code,
            "token": token,
            "status": "pending",
            "createdAt": datetime.utcnow(),
            "expiresAt": None,  # No expiry for test
            "linkUrl": f"https://safechild.mom/c/{short_code}",
            "downloadUrl": f"https://safechild.mom/api/collection/download-apk/{short_code}",
            "testMetadata": {
                "isTestLink": True,
                "testScenario": "elderly_user_test"
            }
        }

        await collection_links_collection.insert_one(link_doc)

        created_clients.append({
            "testId": client_data["id"],
            "name": f"{client_data['firstName']} {client_data['lastName']}",
            "clientId": client_id,
            "shortCode": short_code,
            "token": token,
            "linkUrl": link_doc["linkUrl"],
            "downloadUrl": link_doc["downloadUrl"],
            "language": client_data["language"],
            "device": client_data["device"],
            "techLevel": client_data["techLevel"]
        })

        print(f"      [{i:2d}/20] Created: {client_data['id']} - {client_data['firstName']} {client_data['lastName']}")

    # Print summary
    print("\n[3/4] Test Client Summary")
    print("=" * 100)
    print(f"{'ID':<10} {'Name':<25} {'Device':<20} {'Tech Level':<12} {'Short Code':<10} {'Link URL'}")
    print("-" * 100)

    for c in created_clients:
        print(f"{c['testId']:<10} {c['name']:<25} {c['device']:<20} {c['techLevel']:<12} {c['shortCode']:<10} {c['linkUrl']}")

    print("=" * 100)

    # Save to file for other scripts
    print("\n[4/4] Saving client data to file...")

    import json
    output_file = os.path.join(os.path.dirname(__file__), "test_clients_data.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(created_clients, f, indent=2, ensure_ascii=False)

    print(f"      Saved to: {output_file}")

    # Close connection
    client.close()

    print("\n" + "=" * 60)
    print("TEST CLIENT CREATION COMPLETE!")
    print(f"Total created: {len(created_clients)} clients")
    print("=" * 60)

    return created_clients


if __name__ == "__main__":
    asyncio.run(create_test_clients())
