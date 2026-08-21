"""Create an initial Axyrel company and administrator from the terminal."""
from __future__ import annotations

import getpass
from uuid import uuid4

from sqlalchemy import func, select

from backend.core.database import SessionLocal
from backend.core.security import hash_password
from backend.models.company import Company
from backend.models.user import User


def main() -> None:
    company_name = input("Company name: ").strip()
    email = input("Admin email: ").strip().lower()
    full_name = input("Admin full name: ").strip()
    password = getpass.getpass("Admin password: ")
    confirmation = getpass.getpass("Confirm password: ")

    if not company_name or not email or not full_name:
        raise SystemExit("Company name, email, and full name are required.")
    if password != confirmation:
        raise SystemExit("Passwords do not match.")
    if len(password) < 8:
        raise SystemExit("Password must contain at least 8 characters.")

    with SessionLocal() as db:
        existing = db.scalar(select(User).where(func.lower(User.email) == email.lower()))
        if existing is not None:
            raise SystemExit("A user with this email already exists.")

        company = Company(id=uuid4(), name=company_name)
        user = User(
            id=uuid4(),
            company=company,
            email=email,
            full_name=full_name,
            password_hash=hash_password(password),
            role="admin",
            is_active=True,
        )
        db.add_all([company, user])
        db.commit()

        print(f"Created company: {company.id}")
        print(f"Created admin user: {user.id}")


if __name__ == "__main__":
    main()
