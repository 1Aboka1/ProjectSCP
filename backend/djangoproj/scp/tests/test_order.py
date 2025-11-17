from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from scp.models import (
    User, Supplier, Consumer, SupplierStaffMembership, ConsumerContact, SupplierConsumerLink,
    Product, Order, OrderItem
)
import uuid

class OrdersTests(APITestCase):

    def setUp(self):
        # Supplier Owner
        self.supplier_owner = User.objects.create_user(
            username="owner1", password="pass123", role="owner"
        )

        # Supplier
        self.supplier = Supplier.objects.create(owner=self.supplier_owner, name="Supplier1")

        # Supplier Staff
        self.sales_user = User.objects.create_user(username="sales1", password="pass123", role="sales")
        SupplierStaffMembership.objects.create(
            supplier=self.supplier, user=self.sales_user, role="sales", is_active=True
        )

        # Consumer User
        self.consumer_user = User.objects.create_user(
            username="consumer1", password="pass123", role="consumer_contact"
        )

        # Consumer organization
        self.consumer = Consumer.objects.create(name="Consumer1")

        # Link consumer user to consumer org
        self.consumer_contact = ConsumerContact.objects.create(
            consumer=self.consumer, user=self.consumer_user, is_primary=True
        )

        # Approved link
        self.link = SupplierConsumerLink.objects.create(
            supplier=self.supplier,
            consumer=self.consumer,
            requested_by=self.sales_user,
            status="approved"
        )

        # Product for Supplier
        self.product = Product.objects.create(
            supplier=self.supplier,
            name="Product1",
            unit="kg",
            price=100,
            stock=50
        )

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    # ----------------------------
    # Consumer tests
    # ----------------------------
    def test_consumer_can_create_order_to_linked_supplier(self):
        self.authenticate(self.consumer_user)
        url = reverse("order-list")
        payload = {
            "supplier": str(self.supplier.id),
            "consumer": str(self.consumer.id),
            "placed_by": str(self.consumer_user.id),
            "status": "pending",
            "total_amount": 200,
            "items": [
                {"product": str(self.product.id), "quantity": 2}
            ]
        }
        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        order = Order.objects.get(id=resp.data['id'])
        self.assertEqual(order.consumer, self.consumer)
        self.assertEqual(order.supplier, self.supplier)
        self.assertEqual(order.placed_by, self.consumer_user)
        self.assertEqual(order.items.count(), 1)

    def test_consumer_cannot_create_order_to_unlinked_supplier(self):
        # Another supplier not linked
        other_supplier = Supplier.objects.create(owner=self.supplier_owner, name="Supplier2")
        self.authenticate(self.consumer_user)
        url = reverse("order-list")
        payload = {
            "supplier": str(other_supplier.id),
            "consumer": str(self.consumer.id),
            "placed_by": str(self.consumer_user.id),
            "status": "pending",
            "total_amount": 100,
            "items": [{"product": str(self.product.id), "quantity": 1}]
        }
        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)  # Validation should fail

    def test_consumer_can_see_only_their_orders(self):
        # Create another order by different consumer
        other_consumer_user = User.objects.create_user(
            username="consumer2", password="pass123", role="consumer_contact"
        )
        other_consumer = Consumer.objects.create(name="Consumer2")
        other_link = SupplierConsumerLink.objects.create(
            supplier=self.supplier,
            consumer=other_consumer,
            requested_by=self.sales_user,
            status="approved"
        )
        self.authenticate(self.consumer_user)
        Order.objects.create(
            supplier=self.supplier,
            consumer=self.consumer,
            placed_by=self.consumer_user,
            status="pending",
            total_amount=100
        )
        Order.objects.create(
            supplier=self.supplier,
            consumer=other_consumer,
            placed_by=other_consumer_user,
            status="pending",
            total_amount=200
        )

        url = reverse("order-list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # Only one order visible to this consumer
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(str(resp.data[0]['consumer']), str(self.consumer.id))

    # ----------------------------
    # Supplier staff tests
    # ----------------------------
    def test_supplier_staff_can_see_orders_for_their_supplier(self):
        # Create orders for multiple suppliers
        self.authenticate(self.sales_user)
        Order.objects.create(
            supplier=self.supplier,
            consumer=self.consumer,
            placed_by=self.consumer_user,
            status="pending",
            total_amount=100
        )
        other_supplier = Supplier.objects.create(owner=self.supplier_owner, name="Supplier2")
        other_consumer = Consumer.objects.create(name="Consumer2")
        SupplierConsumerLink.objects.create(
            supplier=other_supplier, consumer=other_consumer, status="approved"
        )
        Order.objects.create(
            supplier=other_supplier,
            consumer=other_consumer,
            placed_by=self.consumer_user,
            status="pending",
            total_amount=200
        )

        url = reverse("order-list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # Only orders for this supplier
        for o in resp.data:
            self.assertEqual(str(o['supplier']), str(self.supplier.id))

    def test_supplier_cannot_create_order(self):
        self.authenticate(self.sales_user)
        url = reverse("order-list")
        payload = {
            "supplier": str(self.supplier.id),
            "consumer": str(self.consumer.id),
            "placed_by": str(self.sales_user.id),
            "status": "pending",
            "total_amount": 100,
            "items": [{"product": str(self.product.id), "quantity": 1}]
        }
        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    # ----------------------------
    # OrderItem tests
    # ----------------------------
    def test_order_items_are_created_with_order(self):
        self.authenticate(self.consumer_user)
        url = reverse("order-list")
        payload = {
            "supplier": str(self.supplier.id),
            "consumer": str(self.consumer.id),
            "placed_by": str(self.consumer_user.id),
            "status": "pending",
            "total_amount": 200,
            "items": [
                {"product": str(self.product.id), "quantity": 2}
            ]
        }
        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        order_id = resp.data['id']
        order = Order.objects.get(id=order_id)
        self.assertEqual(order.items.count(), 1)
        item = order.items.first()
        self.assertEqual(item.product, self.product)
        self.assertEqual(item.quantity, 2)
