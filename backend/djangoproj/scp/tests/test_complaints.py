# scp/tests/test_complaints_incidents.py
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.utils import timezone

from scp.models import (
    User, Supplier, SupplierStaffMembership,
    Consumer, ConsumerContact, SupplierConsumerLink,
    Product, CatalogCategory,
    Order, OrderItem,
    Complaint, Incident
)


class ComplaintsAndIncidentsTests(APITestCase):
    """
    Comprehensive tests for:
      - Complaint creation (consumer)
      - Complaint escalation (manager/owner)
      - Complaint resolution (sales/manager/owner)
      - Model-level escalate() and mark_resolved()
      - Incident creation and updates
    """

    def setUp(self):
        # ---------- Users ----------
        # supplier owner
        self.supplier_owner = User.objects.create_user(
            username="owner1", password="pass123", role="owner"
        )
        # manager
        self.manager = User.objects.create_user(
            username="manager1", password="pass123", role="manager"
        )
        # sales rep
        self.sales = User.objects.create_user(
            username="sales1", password="pass123", role="sales"
        )
        # consumer contact (actual login user for consumer)
        self.consumer_user = User.objects.create_user(
            username="consumer1", password="pass123", role="consumer_contact"
        )

        # ---------- Supplier & Staff ----------
        self.supplier = Supplier.objects.create(
            owner=self.supplier_owner,
            name="Test Supplier"
        )
        # register staff memberships correctly
        SupplierStaffMembership.objects.create(
            supplier=self.supplier, user=self.supplier_owner, role="owner", is_active=True
        )
        SupplierStaffMembership.objects.create(
            supplier=self.supplier, user=self.manager, role="manager", is_active=True
        )
        SupplierStaffMembership.objects.create(
            supplier=self.supplier, user=self.sales, role="sales", is_active=True
        )

        # ---------- Consumer & Contact ----------
        self.consumer = Consumer.objects.create(name="Test Restaurant")
        self.consumer_contact = ConsumerContact.objects.create(
            consumer=self.consumer, user=self.consumer_user, is_primary=True
        )

        # ---------- Link (approved) ----------
        self.link = SupplierConsumerLink.objects.create(
            supplier=self.supplier,
            consumer=self.consumer,
            requested_by=self.sales,
            status=SupplierConsumerLink.Status.APPROVED
        )

        # ---------- Catalog / Product ----------
        self.category = CatalogCategory.objects.create(
            supplier=self.supplier, name="Fruits", slug="fruits"
        )
        self.product = Product.objects.create(
            supplier=self.supplier,
            category=self.category,
            name="Apple",
            unit="kg",
            price=100.00,
            stock=50,
            min_order_quantity=1
        )

        # ---------- Order & OrderItem ----------
        self.order = Order.objects.create(
            supplier=self.supplier,
            consumer=self.consumer,
            placed_by=self.consumer_user,
            status=Order.Status.PENDING,
            total_amount=200.00
        )
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2,
            unit_price=self.product.price,
            line_total=self.product.price * 2
        )

    def authenticate(self, user):
        """Force-auth helper - always pass a User instance."""
        self.client.force_authenticate(user=user)

    # -----------------------
    # Complaint creation tests
    # -----------------------
    def test_consumer_can_create_complaint_for_order_item(self):
        """Consumer user (consumer_contact) can file a complaint tied to an order item."""
        self.authenticate(self.consumer_user)

        url = reverse("complaint-list")
        payload = {
            "order": str(self.order.id),
            "order_item": str(self.order_item.id),
            "description": "Product arrived damaged"
        }

        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)

        # verify DB object
        c = Complaint.objects.get(order=self.order)
        self.assertEqual(c.filed_by, self.consumer_user)
        self.assertEqual(c.order_item, self.order_item)
        self.assertEqual(c.status, Complaint.Status.OPEN)
        self.assertIn("Product arrived damaged", c.description)

    def test_anonymous_cannot_create_complaint(self):
        """Unauthenticated requests are rejected."""
        url = reverse("complaint-list")
        payload = {"order": str(self.order.id), "description": "bad"}
        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    # -----------------------
    # Complaint escalation tests
    # -----------------------
    def test_manager_can_escalate_complaint(self):
        """Manager escalates complaint to owner via API (custom action expected)."""
        # create complaint
        complaint = Complaint.objects.create(
            order=self.order,
            order_item=self.order_item,
            filed_by=self.consumer_user,
            description="Wrong item"
        )

        self.authenticate(self.manager)

        # assume viewset defines @action(detail=True, methods=["post"]) named 'escalate'
        url = reverse("complaint-escalate", args=[str(complaint.id)])
        payload = {"to_user_id": str(self.supplier_owner.id)}

        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)

        complaint.refresh_from_db()
        self.assertEqual(complaint.status, Complaint.Status.ESCALATED)
        self.assertEqual(complaint.escalated_to, self.supplier_owner)
        self.assertIsNotNone(complaint.escalated_at)

    def test_non_staff_cannot_escalate(self):
        """Consumer cannot escalate complaints."""
        complaint = Complaint.objects.create(
            order=self.order, filed_by=self.consumer_user, description="Issue"
        )

        # authenticate as consumer_user (not staff)
        self.authenticate(self.consumer_user)

        url = reverse("complaint-escalate", args=[str(complaint.id)])
        resp = self.client.post(url, {"to_user": str(self.manager.id)}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    # -----------------------
    # Complaint resolution tests
    # -----------------------
    def test_sales_can_resolve_first_line_and_mark_resolved(self):
        """Sales rep resolves complaint using API action 'resolve' (custom)."""
        complaint = Complaint.objects.create(
            order=self.order, filed_by=self.consumer_user, description="Too few items"
        )

        self.authenticate(self.sales)

        url = reverse("complaint-resolve", args=[str(complaint.id)])
        payload = {"resolution": "Refund issued 10 USD"}

        resp = self.client.post(url, payload, format="json")
        # small safety: if view uses 200 or 202 or 204, allow 200
        self.assertIn(resp.status_code, (status.HTTP_200_OK, status.HTTP_202_ACCEPTED, status.HTTP_204_NO_CONTENT))

        complaint.refresh_from_db()
        self.assertEqual(complaint.status, Complaint.Status.RESOLVED)
        self.assertEqual(complaint.resolution, "Refund issued 10 USD")
        self.assertEqual(complaint.assigned_to, self.sales)
        self.assertIsNotNone(complaint.resolved_at)

    def test_cannot_resolve_without_resolution_text(self):
        """Resolver must provide 'resolution' text when resolving via API."""
        complaint = Complaint.objects.create(order=self.order, filed_by=self.consumer_user, description="Issue")

        self.authenticate(self.sales)
        url = reverse("complaint-resolve", args=[str(complaint.id)])
        resp = self.client.post(url, {}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    # -----------------------
    # Model-level methods (unit checks)
    # -----------------------
    def test_complaint_escalate_model_method(self):
        c = Complaint.objects.create(order=self.order, filed_by=self.consumer_user, description="A")
        c.escalate(self.manager)
        c.refresh_from_db()
        self.assertEqual(c.status, Complaint.Status.ESCALATED)
        self.assertEqual(c.escalated_to, self.manager)
        self.assertIsNotNone(c.escalated_at)

    def test_complaint_mark_resolved_model_method(self):
        c = Complaint.objects.create(order=self.order, filed_by=self.consumer_user, description="B")
        c.mark_resolved(self.sales, "done")
        c.refresh_from_db()
        self.assertEqual(c.status, Complaint.Status.RESOLVED)
        self.assertEqual(c.resolution, "done")
        self.assertEqual(c.assigned_to, self.sales)
        self.assertIsNotNone(c.resolved_at)

    # -----------------------
    # Incident tests
    # -----------------------
    def test_consumer_can_report_incident(self):
        self.authenticate(self.consumer_user)
        url = reverse("incident-list")
        payload = {"supplier": str(self.supplier.id), "title": "Spoiled food", "description": "Found spoilage"}
        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)

    def test_incident_update_status_and_export(self):
        inc = Incident.objects.create(supplier=self.supplier, title="X", description="Y", reported_by=self.supplier_owner)
        self.authenticate(self.manager)
        url = reverse("incident-detail", args=[str(inc.id)])
        resp = self.client.patch(url, {"status": "in_progress"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        inc.refresh_from_db()
        self.assertEqual(inc.status, "in_progress")

        # mark exported
        resp2 = self.client.patch(url, {"exported": True}, format="json")
        self.assertEqual(resp2.status_code, status.HTTP_200_OK)
        inc.refresh_from_db()
        self.assertTrue(inc.exported)
