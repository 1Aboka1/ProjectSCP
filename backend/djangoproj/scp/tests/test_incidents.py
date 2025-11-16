from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from scp.models import (
    User, Supplier, Consumer, Order,
    SupplierConsumerLink, Incident
)


class IncidentTests(APITestCase):
    def setUp(self):
        # Supplier roles
        self.owner = User.objects.create_user(username="owner", password="pass123", role="supplier_owner")
        self.manager = User.objects.create_user(username="manager", password="pass123", role="supplier_manager")
        self.sales = User.objects.create_user(username="sales", password="pass123", role="sales")

        self.supplier = Supplier.objects.create(name="FishCo", owner=self.owner)
        self.supplier.managers.add(self.manager)
        self.supplier.sales_reps.add(self.sales)

        # Consumer
        self.consumer_user = User.objects.create_user(username="consumer", password="pass123", role="consumer")
        self.consumer = Consumer.objects.create(user=self.consumer_user, name="Hotel One")

        # Link + Order
        SupplierConsumerLink.objects.create(
            supplier=self.supplier,
            consumer=self.consumer,
            status="approved"
        )

        self.order = Order.objects.create(
            supplier=self.supplier,
            consumer=self.consumer,
            status="submitted"
        )

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def test_consumer_creates_incident(self):
        self.authenticate(self.consumer_user)

        url = reverse("incident-list")
        body = {
            "order": self.order.id,
            "issue": "Product damaged during transport"
        }

        response = self.client.post(url, body, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        incident = Incident.objects.first()
        self.assertEqual(incident.status, "open")

    def test_sales_resolves_incident(self):
        incident = Incident.objects.create(order=self.order, issue="Wrong quantity")

        self.authenticate(self.sales)
        url = reverse("incident-resolve", args=[incident.id])

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        incident.refresh_from_db()
        self.assertEqual(incident.status, "resolved")

    def test_manager_escalates_incident(self):
        incident = Incident.objects.create(order=self.order, issue="Severe issue")

        self.authenticate(self.manager)
        url = reverse("incident-escalate", args=[incident.id])

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        incident.refresh_from_db()
        self.assertEqual(incident.status, "escalated")

    def test_list_all_incidents_for_supplier_staff(self):
        Incident.objects.create(order=self.order, issue="Minor issue")
        Incident.objects.create(order=self.order, issue="Another issue")

        self.authenticate(self.manager)

        url = reverse("incident-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
