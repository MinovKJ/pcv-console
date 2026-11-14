"""
Seed script: creates default admin user in MySQL and inserts synthetic alert
documents in MongoDB. Run once after `docker compose up`.

Usage:
    python scripts/seed_db.py
"""
import asyncio
import sys
import os
import secrets

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.mysql import AsyncSessionLocal, create_all_tables
from app.db.mongo import get_mongo_db
from app.db.models.user import User, UserRole
from app.auth.utils import hash_password
from tests.fixtures.synthetic_alerts import SYNTHETIC_ALERTS
from sqlalchemy import select
from datetime import datetime, timezone
import uuid


async def seed_mysql():
    await create_all_tables()

    admin_pass = os.getenv("SEED_ADMIN_PASSWORD") or secrets.token_urlsafe(16)
    analyst_pass = os.getenv("SEED_ANALYST_PASSWORD") or secrets.token_urlsafe(16)

    async with AsyncSessionLocal() as db:
        # Create admin user
        result = await db.execute(select(User).where(User.username == "admin"))
        if not result.scalar_one_or_none():
            admin = User(
                username="admin",
                email="admin@pcvconsole.local",
                hashed_password=hash_password(admin_pass),
                role=UserRole.admin,
            )
            db.add(admin)

        # Create analyst user
        result = await db.execute(select(User).where(User.username == "analyst1"))
        if not result.scalar_one_or_none():
            analyst = User(
                username="analyst1",
                email="analyst1@pcvconsole.local",
                hashed_password=hash_password(analyst_pass),
                role=UserRole.analyst,
            )
            db.add(analyst)

        await db.commit()
        print("\n=======================================================")
        print(" [MySQL] Initial Users Provisioned:")
        print(f" -> admin:    username='admin'    password='{admin_pass}' (role: admin)")
        print(f" -> analyst1: username='analyst1' password='{analyst_pass}' (role: analyst)")
        print(" Store these credentials securely; change upon first login.")
        print("=======================================================\n")


async def seed_mongo():
    mongo = get_mongo_db()
    alerts = mongo["alerts"]

    for alert in SYNTHETIC_ALERTS:
        alert_id = str(uuid.uuid4())
        await alerts.insert_one({
            "_id": alert_id,
            "submitted_by": 1,
            "submitted_at": datetime.now(timezone.utc),
            "graph": alert["graph"],
            "label": alert["label"],
        })
        print(f"[MongoDB] Inserted synthetic alert: {alert['label']} ({alert_id})")


async def main():
    print("Seeding PCV Console databases...")
    await seed_mysql()
    await seed_mongo()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())

