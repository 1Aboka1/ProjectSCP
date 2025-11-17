from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from scp.models import (
    User, Supplier, SupplierStaffMembership, Consumer, ConsumerContact,
    SupplierConsumerLink, Order, OrderItem, Complaint, Conversation, Message
)
from django.utils import timezone

class ChatSystemTests(APITestCase):
    def setUp(self):
        # ---------------------------
        # Users
        # ---------------------------
        self.supplier_owner = User.objects.create_user(
            username="owner1", password="pass123", role="owner"
        )
        self.manager = User.objects.create_user(
            username="manager1", password="pass123", role="manager"
        )
        self.sales = User.objects.create_user(
            username="sales1", password="pass123", role="sales"
        )
        self.consumer_user = User.objects.create_user(
            username="consumer1", password="pass123", role="consumer_contact"
        )

        # ---------------------------
        # Supplier & Staff
        # ---------------------------
        self.supplier = Supplier.objects.create(owner=self.supplier_owner, name="Supplier1")
        SupplierStaffMembership.objects.bulk_create([
            SupplierStaffMembership(supplier=self.supplier, user=self.supplier_owner, role="owner", is_active=True),
            SupplierStaffMembership(supplier=self.supplier, user=self.manager, role="manager", is_active=True),
            SupplierStaffMembership(supplier=self.supplier, user=self.sales, role="sales", is_active=True)
        ])

        # ---------------------------
        # Consumer & Link
        # ---------------------------
        self.consumer = Consumer.objects.create(name="Consumer1")
        ConsumerContact.objects.create(consumer=self.consumer, user=self.consumer_user, is_primary=True)
        SupplierConsumerLink.objects.create(
            supplier=self.supplier,
            consumer=self.consumer,
            requested_by=self.sales,
            status="approved"
        )

        # ---------------------------
        # Order & Item
        # ---------------------------
        self.order = Order.objects.create(
            supplier=self.supplier, consumer=self.consumer,
            placed_by=self.consumer_user, status="pending", total_amount=100
        )
        self.order_item = OrderItem.objects.create(
            order=self.order, product=None, quantity=1, unit_price=100, line_total=100
        )

    # ---------------------------
    # Helpers
    # ---------------------------
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
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        return Complaint.objects.first()

    # ---------------------------
    # Tests
    # ---------------------------
    def test_complaint_creates_conversation(self):
        """Filing a complaint should auto-create a conversation."""
        complaint = self.create_complaint()
        conv = Conversation.objects.filter(supplier=self.supplier, consumer=self.consumer).first()
        self.assertIsNotNone(conv)
        self.assertEqual(conv.supplier, self.supplier)
        self.assertEqual(conv.consumer, self.consumer)

    def test_consumer_can_send_message(self):
        """Consumer can post a message in conversation."""
        complaint = self.create_complaint()
        conv = Conversation.objects.get(supplier=self.supplier, consumer=self.consumer)
        self.authenticate(self.consumer_user)
        url = reverse("conversation-send-message", args=[str(conv.id)])
        payload = {"text": "Hello, I need help with my order."}
        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        msg = Message.objects.get(conversation=conv)
        self.assertEqual(msg.sender, self.consumer_user)
        self.assertEqual(msg.text, payload["text"])

    def test_sales_can_reply_message(self):
        """Sales staff can send messages to conversation."""
        complaint = self.create_complaint()
        conv = Conversation.objects.get(supplier=self.supplier, consumer=self.consumer)
        self.authenticate(self.sales)
        url = reverse("conversation-send-message", args=[str(conv.id)])
        payload = {"text": "We are looking into this issue."}
        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        msg = Message.objects.get(conversation=conv, sender=self.sales)
        self.assertEqual(msg.text, payload["text"])

    def test_non_participant_cannot_send_or_read(self):
        """Users not linked to conversation cannot see or send messages."""
        complaint = self.create_complaint()
        conv = Conversation.objects.get(supplier=self.supplier, consumer=self.consumer)
        outsider = User.objects.create_user(username="outsider", password="pass123", role="consumer_contact")
        self.authenticate(outsider)
        # Send message
        url = reverse("conversation-send-message", args=[str(conv.id)])
        resp = self.client.post(url, {"text": "Hi"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        # Get conversation
        url2 = reverse("conversation-detail", args=[str(conv.id)])
        resp2 = self.client.get(url2)
        self.assertEqual(resp2.status_code, status.HTTP_403_FORBIDDEN)

    def test_escalation_flow(self):
        """Messages can accompany escalation from Sales → Manager → Owner."""
        complaint = self.create_complaint()
        conv = Conversation.objects.get(supplier=self.supplier, consumer=self.consumer)
        # Sales escalates
        self.authenticate(self.sales)
        url = reverse("complaint-escalate", args=[str(complaint.id)])
        resp = self.client.post(url, {"to_user_id": str(self.manager.id)}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        complaint.refresh_from_db()
        self.assertEqual(complaint.status, Complaint.Status.ESCALATED)
        self.assertEqual(complaint.escalated_to, self.manager)
        # Manager escalates to owner
        self.authenticate(self.manager)
        resp2 = self.client.post(url, {"to_user_id": str(self.supplier_owner.id)}, format="json")
        self.assertEqual(resp2.status_code, status.HTTP_200_OK)
        complaint.refresh_from_db()
        self.assertEqual(complaint.escalated_to, self.supplier_owner)
        self.assertEqual(complaint.status, Complaint.Status.ESCALATED)

    def test_resolution_flow(self):
        """Sales resolves complaint, consumer cannot resolve."""
        complaint = self.create_complaint()
        self.authenticate(self.sales)
        url = reverse("complaint-resolve", args=[str(complaint.id)])
        resp = self.client.post(url, {"resolution": "Issue resolved"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        complaint.refresh_from_db()
        self.assertEqual(complaint.status, Complaint.Status.RESOLVED)
        self.assertEqual(complaint.assigned_to, self.sales)
        self.assertEqual(complaint.resolution, "Issue resolved")

        # Consumer cannot resolve
        self.authenticate(self.consumer_user)
        resp2 = self.client.post(url, {"resolution": "Trying to resolve"}, format="json")
        self.assertEqual(resp2.status_code, status.HTTP_403_FORBIDDEN)

    def test_message_ordering_and_read_flag(self):
        """Messages are chronological and unread by default."""
        complaint = self.create_complaint()
        conv = Conversation.objects.get(supplier=self.supplier, consumer=self.consumer)
        self.authenticate(self.consumer_user)
        # Create multiple messages
        texts = ["First", "Second", "Third"]
        for t in texts:
            self.client.post(reverse("conversation-send-message", args=[str(conv.id)]), {"text": t}, format="json")
        msgs = conv.messages.order_by("created_at")
        self.assertEqual([m.text for m in msgs], texts)
        for m in msgs:
            self.assertFalse(m.is_read)
