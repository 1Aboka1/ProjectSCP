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
    Complaint, Incident, Conversation, Message
)


class ComplaintsAndIncidentsTests(APITestCase):

    def setUp(self):
        # Users
        self.supplier_owner = User.objects.create_user(username="owner1", password="pass123", role="owner")
        self.manager = User.objects.create_user(username="manager1", password="pass123", role="manager")
        self.sales = User.objects.create_user(username="sales1", password="pass123", role="sales")
        self.consumer_user = User.objects.create_user(username="consumer1", password="pass123", role="consumer_contact")

        # Supplier & Staff
        self.supplier = Supplier.objects.create(owner=self.supplier_owner, name="Test Supplier")
        self.owner_staff = SupplierStaffMembership.objects.create(
            supplier=self.supplier, user=self.supplier_owner, role="owner", is_active=True
        )
        self.manager_staff = SupplierStaffMembership.objects.create(
            supplier=self.supplier, user=self.manager, role="manager", is_active=True
        )
        self.sales_staff = SupplierStaffMembership.objects.create(
            supplier=self.supplier, user=self.sales, role="sales", is_active=True
        )

        # Consumer & Contact
        self.consumer = Consumer.objects.create(name="Test Restaurant")
        self.consumer_contact = ConsumerContact.objects.create(
            consumer=self.consumer, user=self.consumer_user, is_primary=True
        )

        # Supplier-Consumer Link
        SupplierConsumerLink.objects.create(
            supplier=self.supplier, consumer=self.consumer, requested_by=self.sales, status="approved"
        )

        # Product & Category
        self.category = CatalogCategory.objects.create(supplier=self.supplier, name="Fruits", slug="fruits")
        self.product = Product.objects.create(
            supplier=self.supplier,
            category=self.category,
            name="Apple",
            unit="kg",
            price=100,
            stock=50,
            min_order_quantity=1
        )

        # Order & Item
        self.order = Order.objects.create(
            supplier=self.supplier,
            consumer=self.consumer,
            placed_by=self.consumer_user,
            status=Order.Status.PENDING,
            total_amount=200
        )
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2,
            unit_price=self.product.price,
            line_total=self.product.price * 2
        )

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def create_complaint(self):
        self.authenticate(self.consumer_user)
        url = reverse("complaint-list")
        payload = {
            "order": str(self.order.id),
            "order_item": str(self.order_item.id),
            "description": "Product damaged"
        }
        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        return Complaint.objects.first()

    def send_message(self, conversation, sender, text):
        self.authenticate(sender)
        url = reverse("conversation-send-message", args=[conversation.id])
        resp = self.client.post(url, {"text": text}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        return Message.objects.get(conversation=conversation, sender=sender)

    # -----------------------
    # Complaint creation tests
    # -----------------------
    def test_complaint_creates_conversation(self):
        complaint = self.create_complaint()
        supplier_staff_found = self.sales_staff  # pick_staff_for_handling would pick sales first
        conv = Conversation.objects.filter(consumer_contact=self.consumer_contact, complaint=complaint).first()
        self.assertIsNotNone(conv)
        self.assertIn(supplier_staff_found, conv.supplier_staff.all())
        self.assertEqual(conv.consumer_contact, self.consumer_contact)

    def test_consumer_can_send_message(self):
        complaint = self.create_complaint()
        conv = Conversation.objects.filter(consumer_contact=self.consumer_contact).first()
        msg = self.send_message(conv, self.consumer_user, "Hello, issue here.")
        self.assertEqual(msg.text, "Hello, issue here.")
        self.assertEqual(msg.sender, self.consumer_user)
        self.assertEqual(msg.conversation, conv)

    def test_sales_can_reply_message(self):
        complaint = self.create_complaint()
        conv = Conversation.objects.filter(consumer_contact=self.consumer_contact).first()
        msg = self.send_message(conv, self.sales, "We are looking into this issue.")
        self.assertEqual(msg.sender, self.sales)
        self.assertEqual(msg.conversation, conv)
        self.assertIn(self.sales_staff, conv.supplier_staff.all())
        
    # -----------------------
    # Escalation tests
    # -----------------------
    def test_escalation_flow_updates_assigned_to_and_conversation(self):
        complaint = self.create_complaint()

        # Initial assigned_to is sales
        complaint.assigned_to = self.sales
        complaint.save(update_fields=['assigned_to'])

        self.authenticate(self.sales)
        url = reverse("complaint-escalate", args=[complaint.id])
        resp = self.client.post(url, {}, format="json")  # next escalation
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        complaint.refresh_from_db()
        self.assertEqual(complaint.assigned_to, self.manager)
        conv = complaint.conversations.first()
        self.assertIn(self.manager_staff, conv.supplier_staff.all())

        # Escalate to owner
        self.authenticate(self.manager)
        resp = self.client.post(url, {}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        complaint.refresh_from_db()
        self.assertEqual(complaint.assigned_to, self.supplier_owner)
        self.assertIn(self.owner_staff, conv.supplier_staff.all())

    # -----------------------
    # Resolution tests
    # -----------------------
    def test_resolution_updates_assigned_to_and_status(self):
        complaint = self.create_complaint()
        complaint.assigned_to = self.sales
        complaint.save(update_fields=['assigned_to'])

        self.authenticate(self.sales)
        url = reverse("complaint-resolve", args=[complaint.id])
        payload = {"resolution": "Issue resolved, product replaced."}
        resp = self.client.post(url, payload, format="json")
        self.assertIn(resp.status_code, (status.HTTP_200_OK, status.HTTP_202_ACCEPTED, status.HTTP_204_NO_CONTENT))
        complaint.refresh_from_db()
        self.assertEqual(complaint.status, Complaint.Status.RESOLVED)
        self.assertEqual(complaint.resolution, "Issue resolved, product replaced.")
        self.assertEqual(complaint.assigned_to, self.sales)
        self.assertIsNotNone(complaint.resolved_at)