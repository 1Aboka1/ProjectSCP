from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from scp.models import (
    User, Supplier, Consumer,
    SupplierStaffMembership, SupplierConsumerLink, ConsumerContact
)
from scp.serializers import (
    SupplierConsumerLinkSerializer
)


class SupplierConsumerLinkTests(APITestCase):

    def setUp(self):
        # Supplier Owner (role: owner)
        self.supplier_owner = User.objects.create_user(
            username="supplierowner",
            password="pass123",
            role="owner"
        )

        # Create Supplier
        self.supplier = Supplier.objects.create(
            owner=self.supplier_owner,
            name="Test Supplier"
        )

        # IMPORTANT: Register the supplier owner as staff
        self.owner_membership = SupplierStaffMembership.objects.create(
            supplier=self.supplier,
            user=self.supplier_owner,
            role="owner",        # Must match model TextChoices
            is_active=True
        )

        # Consumer User
        self.consumer_user = User.objects.create_user(
            username="consumer1",
            password="pass123",
            role="consumer_contact"
        )

        # Create consumer organization
        self.consumer = Consumer.objects.create(
            name="Test Restaurant"
        )

        # Link user to the consumer
        self.consumer_contact = ConsumerContact.objects.create(
            consumer=self.consumer,
            user=self.consumer_user,
            is_primary=True
        )

    def authenticate(self, user):
        """Force authenticate for tests."""
        self.client.force_authenticate(user=user)

    # ------------------------
    # 1. Consumer sends request
    # ------------------------
    def test_consumer_sends_link_request(self):
        self.authenticate(self.consumer_user)

        url = reverse("link-list")
        body = {
                "supplier": self.supplier.id,
                "consumer": self.consumer.id
            }

        response = self.client.post(url, body, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        link = SupplierConsumerLink.objects.get(
            supplier=self.supplier, consumer=self.consumer
        )
        self.assertEqual(link.status, "pending")
    
    # ------------------------
    # 2. Duplicate request blocked
    # ------------------------
    def test_duplicate_link_request_rejected(self):
        SupplierConsumerLink.objects.create(
            supplier=self.supplier, consumer=self.consumer, status="pending"
        )

        self.authenticate(self.consumer_user)

        url = reverse("link-list")
        response = self.client.post(url, {"supplier": self.supplier.id}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ------------------------
    # 3. Supplier approves consumer
    # ------------------------
    def test_supplier_owner_approves_link(self):
        link = SupplierConsumerLink.objects.create(
            supplier=self.supplier,
            consumer=self.consumer,
            status="pending"
        )

        self.authenticate(self.supplier_owner)

        url = reverse("link-approve", args=[link.id])
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        link.refresh_from_db()
        self.assertEqual(link.status, "approved")

    # ------------------------
    # 4. Supplier blocks consumer
    # ------------------------
    def test_supplier_blocks_consumer(self):
        link = SupplierConsumerLink.objects.create(
            supplier=self.supplier,
            consumer=self.consumer,
            status="approved"
        )

        self.authenticate(self.supplier_owner)

        url = reverse("link-block", args=[link.id])
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        link.refresh_from_db()
        self.assertEqual(link.status, "blocked")

    # ------------------------
    # 5. Consumer views approved suppliers
    # ------------------------
    def test_view_consumer_links(self):
        link = SupplierConsumerLink.objects.create(
            supplier=self.supplier,
            consumer=self.consumer,
            status="approved"
        )

        self.authenticate(self.consumer_user)

        url = reverse("link-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serialized_link = SupplierConsumerLinkSerializer(link).data

        # response.data is usually a list for 'list' endpoint
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0], serialized_link)