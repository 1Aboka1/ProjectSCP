from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from scp.views import pick_staff_for_handling
from scp.models import (
    Product, User, Supplier, SupplierStaffMembership, Consumer, ConsumerContact,
    SupplierConsumerLink, Order, OrderItem, Complaint, Conversation, Message
)
from django.utils import timezone

class ChatSystemTests(APITestCase):
    # ---------------------------
    # Setup (your existing code)
    # ---------------------------
    def setUp(self):
        # Users
        self.supplier_owner = User.objects.create_user(username="owner1", password="pass123", role="owner")
        self.manager = User.objects.create_user(username="manager1", password="pass123", role="manager")
        self.sales = User.objects.create_user(username="sales1", password="pass123", role="sales")
        self.consumer_user = User.objects.create_user(username="consumer1", password="pass123", role="consumer_contact")

        # Supplier & Staff
        self.supplier = Supplier.objects.create(owner=self.supplier_owner, name="Supplier1")
        [self.owner_staff, self.manager_staff, self.sales_staff] = SupplierStaffMembership.objects.bulk_create([
            SupplierStaffMembership(supplier=self.supplier, user=self.supplier_owner, role="owner", is_active=True),
            SupplierStaffMembership(supplier=self.supplier, user=self.manager, role="manager", is_active=True),
            SupplierStaffMembership(supplier=self.supplier, user=self.sales, role="sales", is_active=True)
        ])

        # Consumer & Link
        self.consumer = Consumer.objects.create(name="Consumer1")
        self.consumer_contact = ConsumerContact.objects.create(consumer=self.consumer, user=self.consumer_user, is_primary=True)
        SupplierConsumerLink.objects.create(
            supplier=self.supplier,
            consumer=self.consumer,
            requested_by=self.sales,
            status="approved"
        )

        # Order & Product
        self.order = Order.objects.create(
            supplier=self.supplier, consumer=self.consumer,
            placed_by=self.consumer_user, status="pending", total_amount=100
        )
        self.product = Product.objects.create(
            supplier=self.supplier,
            name="Test Product",
            unit="kg",
            price=100,
            stock=50
        )

        # OrderItem
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=1,
            unit_price=100,
            line_total=100
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
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        return Complaint.objects.first()

    def send_message(self, conversation, sender, text):
        self.authenticate(sender)
        url = reverse("conversation-send-message", args=[str(conversation.id)])
        payload = {"text": text}
        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        return Message.objects.get(conversation=conversation, sender=sender)

    # ---------------------------
    # Tests
    # ---------------------------
    def test_complaint_creates_conversation(self):
        complaint = self.create_complaint()
        staff_for_handling = pick_staff_for_handling(self.supplier)

        conv = Conversation.objects.filter(
            supplier_staff__in=[staff_for_handling],
            consumer_contact=self.consumer_contact
        ).first()

        self.assertIsNotNone(conv)
        self.assertIn(staff_for_handling, conv.supplier_staff.all())
        self.assertEqual(conv.consumer_contact, self.consumer_contact)

    def test_consumer_can_send_message(self):
        complaint = self.create_complaint()

        conv = Conversation.objects.get(
            supplier_staff__in=[self.sales_staff],
            consumer_contact=self.consumer_contact
        )

        msg = self.send_message(conv, self.consumer_user, "Hello, issue here.")
        self.assertEqual(msg.text, "Hello, issue here.")
        self.assertEqual(msg.sender, self.consumer_user)
        self.assertEqual(msg.conversation, conv)

    def test_sales_can_reply_message(self):
        complaint = self.create_complaint()

        conv = Conversation.objects.get(
            supplier_staff__in=[self.sales_staff],
            consumer_contact=self.consumer_contact
        )

        msg = self.send_message(conv, self.sales, "We are looking into this issue.")
        self.assertEqual(msg.sender, self.sales)
        self.assertEqual(msg.conversation, conv)

    def test_non_participant_cannot_send_or_read(self):
        complaint = self.create_complaint()

        conv = Conversation.objects.get(
            supplier_staff__in=[self.sales_staff],
            consumer_contact=self.consumer_contact
        )

        stranger = User.objects.create_user(
            username="stranger",
            password="pass",
            role="consumer_contact"
        )

        self.authenticate(stranger)
        url = reverse("conversation-send-message", args=[conv.id])
        resp = self.client.post(url, {"text": "Hi"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_escalation_flow(self):
        complaint = self.create_complaint()

        # 🔼 Sales → Manager
        self.authenticate(self.sales)
        url = reverse("complaint-escalate", args=[complaint.id])
        payload = {"to_user_id": str(self.manager.id)}
        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        complaint.refresh_from_db()
        self.assertEqual(complaint.status, Complaint.Status.ESCALATED)
        self.assertEqual(complaint.escalated_to, self.manager)

        # 🔼 Manager → Owner
        self.authenticate(self.manager)
        payload = {"to_user_id": str(self.supplier_owner.id)}
        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        complaint.refresh_from_db()
        self.assertEqual(complaint.escalated_to, self.supplier_owner)

    def test_resolution_flow(self):
        complaint = self.create_complaint()

        self.authenticate(self.sales)
        url = reverse("complaint-resolve", args=[complaint.id])
        payload = {"resolution": "Issue resolved, product replaced."}
        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        complaint.refresh_from_db()
        self.assertEqual(complaint.status, Complaint.Status.RESOLVED)
        self.assertEqual(complaint.resolution, "Issue resolved, product replaced.")
        self.assertEqual(complaint.assigned_to, self.sales)

    def test_message_ordering_and_read_flag(self):
        complaint = self.create_complaint()

        conv = Conversation.objects.get(
            supplier_staff__in=[self.sales_staff],
            consumer_contact=self.consumer_contact
        )

        m1 = self.send_message(conv, self.consumer_user, "First message")
        m2 = self.send_message(conv, self.sales, "Second message")
        m3 = self.send_message(conv, self.manager, "Third message")

        msgs = conv.messages.order_by("created_at")
        self.assertEqual(list(msgs), [m1, m2, m3])

        # Mark first message as read
        m1.is_read = True
        m1.save()
        self.assertTrue(Message.objects.get(pk=m1.id).is_read)
