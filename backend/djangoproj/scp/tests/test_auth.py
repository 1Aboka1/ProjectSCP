# scp/tests/test_user_registration.py
import uuid
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from scp.models import Consumer, ConsumerContact, User, Supplier, SupplierStaffMembership

class UserRegistrationTests(APITestCase):

    def setUp(self):
        # Create an existing supplier to test manager/sales registration
        self.existing_owner = User.objects.create_user(
            username="existing_owner",
            password="pass123",
            role="owner"
        )
        self.existing_supplier = Supplier.objects.create(
            name="Existing Supplier",
            owner=self.existing_owner
        )
        self.supplier = Supplier.objects.create(
            name="Test Supplier",
            owner=self.existing_owner
        )
        SupplierStaffMembership.objects.create(
            supplier=self.existing_supplier,
            user=self.existing_owner,
            role="owner"
        )

    # -------------------------
    # Consumer registration
    # -------------------------
    def test_consumer_contact_registration(self):
        url = reverse("user-register")
        payload = {
            "username": "consumer1",
            "email": "consumer1@example.com",
            "password": "pass123",
            "role": "consumer_contact",
            "display_name": "Consumer Contact",
            "consumer_name": "Apple Inc."
        }
        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(username="consumer1")
        self.assertEqual(user.role, "consumer_contact")
        self.assertFalse(Supplier.objects.filter(owner=user).exists())

    # -------------------------
    # Supplier Owner registration
    # -------------------------
    def test_supplier_owner_registration_creates_supplier(self):
        url = reverse("user-register")
        payload = {
            "username": "owner1",
            "email": "owner1@example.com",
            "password": "pass123",
            "role": "owner",
            "supplier_name": "New Supplier",
            "supplier_description": "Test supplier"
        }
        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(username="owner1")
        self.assertEqual(user.role, "owner")

        # Supplier should be created and linked
        supplier = Supplier.objects.get(owner=user)
        self.assertEqual(supplier.name, "New Supplier")
        self.assertEqual(supplier.description, "Test supplier")

        # Membership should exist
        membership = SupplierStaffMembership.objects.get(user=user, supplier=supplier)
        self.assertEqual(membership.role, "owner")

    def test_supplier_owner_registration_requires_supplier_name(self):
        url = reverse("user-register")
        payload = {
            "username": "owner2",
            "email": "owner2@example.com",
            "password": "pass123",
            "role": "owner"
        }
        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("supplier_name", resp.data)

    # -------------------------
    # Supplier Manager / Sales registration
    # -------------------------
    def test_sales_registration_to_existing_supplier(self):
        url = reverse("user-register")
        payload = {
            "username": "sales1",
            "email": "sales1@example.com",
            "password": "pass123",
            "role": "sales",
            "supplier_id": str(self.existing_supplier.id)
        }
        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(username="sales1")
        self.assertEqual(user.role, "sales")

        membership = SupplierStaffMembership.objects.get(user=user, supplier=self.existing_supplier)
        self.assertEqual(membership.role, "sales")

    def test_manager_registration_to_existing_supplier(self):
        url = reverse("user-register")
        payload = {
            "username": "manager1",
            "email": "manager1@example.com",
            "password": "pass123",
            "role": "manager",
            "supplier_id": str(self.existing_supplier.id)
        }
        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(username="manager1")
        self.assertEqual(user.role, "manager")

        membership = SupplierStaffMembership.objects.get(user=user, supplier=self.existing_supplier)
        self.assertEqual(membership.role, "manager")

    def test_sales_registration_requires_supplier_id(self):
        url = reverse("user-register")
        payload = {
            "username": "sales2",
            "email": "sales2@example.com",
            "password": "pass123",
            "role": "sales"
        }
        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("supplier_id", resp.data)

    def test_sales_registration_to_non_existing_supplier(self):
        url = reverse("user-register")
        payload = {
            "username": "sales3",
            "email": "sales3@example.com",
            "password": "pass123",
            "role": "sales",
            "supplier_id": "00000000-0000-0000-0000-000000000000"  # non-existent
        }
        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("supplier_id", resp.data)
    
    def test_register_owner_creates_supplier_and_membership(self):
        url = reverse("user-register")
        payload = {
            "username": "owner2",
            "password": "pass123",
            "role": "owner",
            "supplier_name": "New Supplier"
        }
        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(username="owner2")
        self.assertEqual(user.role, "owner")

        supplier = Supplier.objects.get(name="New Supplier")
        self.assertEqual(supplier.owner, user)

        membership = SupplierStaffMembership.objects.get(user=user, supplier=supplier)
        self.assertEqual(membership.role, "owner")

    # ------------------------
    # Sales / Manager Registration
    # ------------------------
    def test_register_sales_to_existing_supplier(self):
        url = reverse("user-register")
        payload = {
            "username": "sales1",
            "password": "pass123",
            "role": "sales",
            "supplier_id": str(self.supplier.id)
        }
        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(username="sales1")
        self.assertEqual(user.role, "sales")

        membership = SupplierStaffMembership.objects.get(user=user, supplier=self.supplier)
        self.assertEqual(membership.role, "sales")

    def test_register_manager_to_non_existing_supplier_fails(self):
        url = reverse("user-register")
        payload = {
            "username": "manager1",
            "password": "pass123",
            "role": "manager",
            "supplier_id": str(uuid.uuid4())  # random ID that doesn't exist
        }
        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("supplier_id", resp.data)

    # ------------------------
    # Consumer Contact Registration
    # ------------------------
    def test_register_consumer_contact_creates_consumer_and_contact(self):
        url = reverse("user-register")
        payload = {
            "username": "consumer1",
            "password": "pass123",
            "role": "consumer_contact",
            "consumer_name": "Test Restaurant"
        }
        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(username="consumer1")
        self.assertEqual(user.role, "consumer_contact")

        consumer = Consumer.objects.get(name="Test Restaurant")
        contact = ConsumerContact.objects.get(user=user, consumer=consumer)
        self.assertTrue(contact.is_primary)

    def test_register_consumer_contact_missing_consumer_name_fails(self):
        url = reverse("user-register")
        payload = {
            "username": "consumer2",
            "password": "pass123",
            "role": "consumer_contact"
        }
        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("consumer_name", resp.data)
