"""Disposable API/storage validation; no repository .env or real DB access."""
import os
import sys
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

temporary = tempfile.TemporaryDirectory(prefix="axyrel-image-tests-")
original_cwd = Path.cwd()
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.chdir(temporary.name)
os.environ.update(DATABASE_URL=f"sqlite:///{Path(temporary.name) / 'test.db'}",
                  SECRET_KEY="synthetic-image-test-secret-at-least-32-bytes", AXYREL_ENV="test")

from fastapi.testclient import TestClient
from PIL import Image
from backend.main import app
from backend.core.database import engine, SessionLocal
from backend.core.security import hash_password
from backend.models.base import Base
from backend.models.company import Company
from backend.models.user import User
from backend.models.customer import Customer
from backend.models.asset import Asset
from backend.services.profile_images import PrivateLocalImageStorage, get_image_storage, MAX_UPLOAD


def image_bytes(fmt="PNG", color="teal", size=(40, 30)):
    image = Image.new("RGB", size, color)
    exif = Image.Exif(); exif[270] = "Private synthetic metadata"
    stream = BytesIO(); image.save(stream, format=fmt, exif=exif)
    return stream.getvalue()


class ProfileImageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(engine)

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        engine.dispose()
        os.chdir(original_cwd)
        temporary.cleanup()

    def setUp(self):
        with SessionLocal() as db:
            for table in reversed(Base.metadata.sorted_tables):
                db.execute(table.delete())
            company = Company(id=uuid4(), name="Synthetic A", status="active")
            other = Company(id=uuid4(), name="Synthetic B", status="active")
            db.add_all([company, other]); db.flush()
            for email, role, tenant in [("owner", "admin", company), ("viewer", "technician", company), ("foreign", "admin", other)]:
                db.add(User(id=uuid4(), company=tenant, email=f"{email}@example.test", full_name=email,
                            role=role, password_hash=hash_password("synthetic-password")))
            customer = Customer(id=uuid4(), company_id=company.id, name="Synthetic Customer")
            db.add(customer); db.flush()
            asset = Asset(id=uuid4(), company_id=company.id, customer_id=customer.id, asset_type="Synthetic Device")
            db.add(asset); db.commit()
            self.company = company.id
            self.paths = [f"/api/v1/customers/{customer.id}/image", f"/api/v1/assets/{asset.id}/image"]
        self.store_folder = tempfile.TemporaryDirectory(dir=temporary.name)
        self.addCleanup(self.store_folder.cleanup)
        self.storage = PrivateLocalImageStorage(Path(self.store_folder.name))
        app.dependency_overrides[get_image_storage] = lambda: self.storage
        self.client = TestClient(app, raise_server_exceptions=False)
        self.headers = {}
        for name in ["owner", "viewer", "foreign"]:
            response = self.client.post("/api/v1/auth/login", data={"username": f"{name}@example.test", "password": "synthetic-password"})
            self.assertEqual(response.status_code, 200)
            self.headers[name] = {"Authorization": f"Bearer {response.json()['access_token']}"}

    def put(self, path, content, mime="image/png", who="owner"):
        return self.client.put(path, content=content, headers={**self.headers[who], "Content-Type": mime})

    def test_upload_display_replace_remove_all_formats(self):
        for path in self.paths:
            self.assertEqual(self.client.get(path, headers=self.headers["owner"]).status_code, 404)
            previous = None
            for fmt, mime, color in [("JPEG", "image/jpeg", "red"), ("PNG", "image/png", "green"), ("WEBP", "image/webp", "blue")]:
                self.assertEqual(self.put(path, image_bytes(fmt, color), mime).status_code, 204)
                response = self.client.get(path, headers=self.headers["viewer"])
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.headers["content-type"], "image/webp")
                self.assertIn("no-store", response.headers["cache-control"])
                self.assertEqual(response.headers["x-content-type-options"], "nosniff")
                with Image.open(BytesIO(response.content)) as output:
                    self.assertEqual(output.size, (40, 30))
                    self.assertFalse(output.getexif())
                    self.assertNotIn("xmp", output.info)
                    self.assertNotIn("icc_profile", output.info)
                self.assertNotEqual(response.content, previous); previous = response.content
            self.assertEqual(self.client.delete(path, headers=self.headers["owner"]).status_code, 204)
            self.assertEqual(self.client.get(path, headers=self.headers["owner"]).status_code, 404)
            self.assertEqual(self.client.delete(path, headers=self.headers["owner"]).status_code, 204)

    def test_invalid_content_mime_animation_dimensions_preserve_previous(self):
        animation = BytesIO()
        Image.new("RGB", (10, 10), "red").save(animation, format="WEBP", save_all=True,
            append_images=[Image.new("RGB", (10, 10), "blue")], duration=100)
        cases = [(b"<svg onload='alert(1)'/>", "image/svg+xml", 415), (b"not an image", "image/png", 422),
                 (image_bytes("JPEG"), "image/png", 422), (image_bytes(), "application/octet-stream", 415),
                 (image_bytes(size=(4097, 1)), "image/png", 422), (animation.getvalue(), "image/webp", 422),
                 (image_bytes()[:25], "image/png", 422)]
        for path in self.paths:
            self.assertEqual(self.put(path, image_bytes()).status_code, 204)
            before = self.client.get(path, headers=self.headers["owner"]).content
            for content, mime, status in cases:
                with self.subTest(path=path, mime=mime, status=status):
                    response = self.put(path, content, mime)
                    self.assertEqual(response.status_code, status, response.text)
                    self.assertNotIn(self.store_folder.name, response.text)
                    self.assertEqual(self.client.get(path, headers=self.headers["owner"]).content, before)

    def test_oversized_stream_rejected_without_content_length(self):
        for path in self.paths:
            def chunks():
                yield b"x" * MAX_UPLOAD
                yield b"x"
            self.assertEqual(self.put(path, chunks()).status_code, 413)
            self.assertEqual(self.client.get(path, headers=self.headers["owner"]).status_code, 404)

    def test_anonymous_and_viewer_writes_denied(self):
        for path in self.paths:
            for method in ["GET", "PUT", "DELETE"]:
                self.assertEqual(self.client.request(method, path).status_code, 401)
            self.assertEqual(self.put(path, image_bytes(), who="viewer").status_code, 403)
            self.assertEqual(self.client.delete(path, headers=self.headers["viewer"]).status_code, 403)

    def test_cross_tenant_all_operations_ignore_scope_overrides(self):
        for path in self.paths:
            self.assertEqual(self.put(path, image_bytes()).status_code, 204)
            for method in ["GET", "PUT", "DELETE"]:
                response = self.client.request(method, path, params={"company_id": str(self.company)},
                    headers={**self.headers["foreign"], "X-Company-ID": str(self.company), "Content-Type": "image/png"}, content=image_bytes())
                self.assertEqual(response.status_code, 404, response.text)
            self.assertEqual(self.client.get(path, headers=self.headers["owner"]).status_code, 200)

    def test_deleted_records_and_live_role_revocation(self):
        for path in self.paths:
            self.assertEqual(self.put(path, image_bytes()).status_code, 204)
            self.client.delete(path.removesuffix("/image"), headers=self.headers["owner"])
            for method in ["GET", "PUT", "DELETE"]:
                self.assertEqual(self.client.request(method, path, headers=self.headers["owner"]).status_code, 404)
        with SessionLocal() as db:
            from sqlalchemy import select
            user = db.scalar(select(User).where(User.email == "owner@example.test")); user.role = "technician"; db.commit()
        self.assertEqual(self.put(self.paths[0], image_bytes()).status_code, 403)

    def test_atomic_failure_keeps_old_image_and_removes_temporary(self):
        self.storage.replace("synthetic/image.webp", b"old")
        with patch("backend.services.profile_images.os.replace", side_effect=OSError("synthetic failure")):
            with self.assertRaises(OSError):
                self.storage.replace("synthetic/image.webp", b"new")
        self.assertEqual(self.storage.read("synthetic/image.webp"), b"old")
        self.assertEqual(len(list(Path(self.store_folder.name).rglob("*.*"))), 1)
        with self.assertRaises(ValueError):
            self.storage.read("../outside.webp")
        self.storage.replace("synthetic/oversized.webp", b"x" * (MAX_UPLOAD + 1))
        with self.assertRaises(OSError):
            self.storage.read("synthetic/oversized.webp")

    def test_bounded_output_and_api_storage_failure_hides_paths(self):
        for path in self.paths:
            self.assertEqual(self.put(path, image_bytes(size=(2048, 1024))).status_code, 204)
            with Image.open(BytesIO(self.client.get(path, headers=self.headers["owner"]).content)) as image:
                self.assertEqual(image.size, (1024, 512))
            with self.assertLogs("backend.api.errors", level="ERROR"), patch.object(self.storage, "replace", side_effect=OSError(self.store_folder.name)):
                response = self.put(path, image_bytes())
            self.assertEqual(response.status_code, 500)
            self.assertNotIn(self.store_folder.name, response.text)


if __name__ == "__main__":
    unittest.main()
