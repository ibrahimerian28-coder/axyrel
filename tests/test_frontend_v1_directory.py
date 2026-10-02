"""Focused synthetic directory tests; reuse accepted isolated auth fixture."""
from uuid import uuid4
import test_task46_auth as fixture
from backend.models.user import User
from backend.models.company import Company


class FrontendDirectoryTests(fixture.Task46AuthTests):
    def test_directory_minimal_same_tenant_technicians_only(self):
        with self.Session() as db:
            company = Company(id=uuid4(), name="Directory foreign", status="active")
            db.add(company)
            db.add(User(id=uuid4(), company=company, email="foreign@synthetic.test", full_name="Foreign", password_hash="unused", role="technician"))
            db.commit()
        headers = {"Authorization": f"Bearer {self._login('admin@example.com')}"}
        response = self.client.get("/api/v1/technician-directory", headers=headers)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(response.json())
        self.assertTrue(all(set(row) == {"id", "display_name"} for row in response.json()))
        self.assertNotIn("Foreign", [row["display_name"] for row in response.json()])

    def test_directory_requires_auth_and_has_no_write(self):
        self.assertEqual(self.client.get("/api/v1/technician-directory").status_code, 401)
        self.assertEqual(self.client.post("/api/v1/technician-directory", json={}).status_code, 405)

    def test_existing_service_permissions_and_inactive_exclusion(self):
        with self.Session() as db:
            technician = db.query(User).filter(User.email == "technician@example.com").one()
            expected_id = str(technician.id)
            db.add(User(id=uuid4(), company_id=self.company_a, email="inactive-tech@synthetic.test", full_name="Inactive Tech", password_hash="unused", role="technician", is_active=False))
            db.commit()
        for email in ("admin@example.com", "manager@example.com", "technician@example.com"):
            response = self.client.get("/api/v1/technician-directory", headers={"Authorization": f"Bearer {self._login(email)}"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), [{"id": expected_id, "display_name": "Technician"}])
