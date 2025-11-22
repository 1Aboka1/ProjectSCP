from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile

from scp.models import (
    User, Supplier, SupplierKYBDocument, SupplierStaffMembership
)


class SupplierKYBTests(APITestCase):

    def setUp(self):
        # Supplier owner (who uploads KYB)
        self.owner = User.objects.create_user(
            username="owner1", password="pass123", role="owner"
        )

        # Platform admin (who verifies suppliers)
        self.admin = User.objects.create_user(
            username="admin", password="pass123", role="platform_admin", is_staff=True
        )

        # Regular supplier (unverified initially)
        self.supplier = Supplier.objects.create(
            name="Test Supplier",
            owner=self.owner,
            verification_status="unsubmitted",
            is_verified=False
        )

        # Owner must be staff of this supplier
        SupplierStaffMembership.objects.create(
            supplier=self.supplier,
            user=self.owner,
            role="owner",
            is_active=True
        )

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    # ---------------------------------------------------------
    # 1) Supplier uploads KYB documents (allowed)
    # ---------------------------------------------------------
    def test_supplier_can_upload_kyb_documents(self):
        self.authenticate(self.owner)

        url = reverse("supplier-upload-kyb", args=[self.supplier.id])

        fake_file = SimpleUploadedFile(
            "kyb_doc.pdf",
            b"pdf file bytes",
            content_type="application/pdf"
        )

        payload = {
            "document": fake_file,
            "note": "Company registration certificate",
        }

        response = self.client.post(url, payload, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

        # Document actually saved
        self.assertEqual(SupplierKYBDocument.objects.count(), 1)
        doc = SupplierKYBDocument.objects.first()

        self.assertEqual(doc.supplier, self.supplier)
        self.assertEqual(doc.uploaded_by, self.owner)
        self.assertEqual(doc.note, "Company registration certificate")
        self.assertTrue(doc.document.name.startswith("kyb"))

    # ---------------------------------------------------------
    # 2) Non-staff cannot upload KYB
    # ---------------------------------------------------------
    def test_non_staff_cannot_upload_kyb(self):
        random_user = User.objects.create_user(
            username="random", password="pass123", role="consumer"
        )
        self.authenticate(random_user)

        url = reverse("supplier-upload-kyb", args=[self.supplier.id])

        fake_file = SimpleUploadedFile("fraud.pdf", b"x", content_type="application/pdf")

        response = self.client.post(url, {"document": fake_file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ---------------------------------------------------------
    # 3) Admin verifies supplier
    # (assuming PATCH is enough to update verification status)
    # ---------------------------------------------------------
    def test_admin_can_verify_supplier(self):
        self.authenticate(self.admin)

        url = reverse("supplier-detail", args=[self.supplier.id])
        payload = {
            "verification_status": "verified",
            "is_verified": True
        }

        response = self.client.patch(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.supplier.refresh_from_db()
        self.assertTrue(self.supplier.is_verified)
        self.assertEqual(self.supplier.verification_status, "verified")

    # ---------------------------------------------------------
    # 4) Supplier cannot self-verify
    # ---------------------------------------------------------
    def test_supplier_cannot_self_verify(self):
        self.authenticate(self.owner)

        url = reverse("supplier-detail", args=[self.supplier.id])
        payload = {
            "verification_status": "verified",
            "is_verified": True
        }

        response = self.client.patch(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # still unverified
        self.supplier.refresh_from_db()
        self.assertFalse(self.supplier.is_verified)
        self.assertEqual(self.supplier.verification_status, "unsubmitted")

    # ---------------------------------------------------------
    # 5) Admin can reject supplier
    # ---------------------------------------------------------
    def test_admin_can_reject_supplier(self):
        self.authenticate(self.admin)

        url = reverse("supplier-detail", args=[self.supplier.id])
        payload = {
            "verification_status": "rejected",
            "is_verified": False
        }

        response = self.client.patch(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.supplier.refresh_from_db()
        self.assertEqual(self.supplier.verification_status, "rejected")
        self.assertFalse(self.supplier.is_verified)

    # ---------------------------------------------------------
    # 6) Staff can list uploaded KYB documents (permissions)
    # ---------------------------------------------------------
    def test_staff_can_list_kyb_documents(self):
        # Upload 1 doc first
        SupplierKYBDocument.objects.create(
            supplier=self.supplier,
            uploaded_by=self.owner,
            document="kyb/test.pdf"
        )

        self.authenticate(self.owner)
        url = reverse("supplier-kyb-list")

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)

    def test_non_staff_cannot_list_kyb_documents(self):
        random_user = User.objects.create_user(
            username="rand", password="123"
        )
        self.authenticate(random_user)

        url = reverse("supplier-kyb-list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
