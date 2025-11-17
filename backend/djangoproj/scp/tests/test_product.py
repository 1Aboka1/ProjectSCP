from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from scp.models import (
    User,
    Supplier,
    SupplierStaffMembership,
    Consumer,
    ConsumerContact,
    SupplierConsumerLink,
    Product,
    ProductAttachment,
)


class ProductViewSetTests(APITestCase):

    def setUp(self):
        # Supplier Owner
        self.supplier_owner = User.objects.create_user(
            username="owner1",
            password="pass123",
            role="owner"
        )

        # Supplier
        self.supplier = Supplier.objects.create(
            owner=self.supplier_owner,
            name="Supplier1"
        )

        # Staff memberships
        SupplierStaffMembership.objects.create(
            supplier=self.supplier,
            user=self.supplier_owner,
            role="owner",
            is_active=True
        )

        self.manager_user = User.objects.create_user(
            username="manager1",
            password="pass123",
            role="manager"
        )
        SupplierStaffMembership.objects.create(
            supplier=self.supplier,
            user=self.manager_user,
            role="manager",
            is_active=True
        )

        self.sales_user = User.objects.create_user(
            username="sales1",
            password="pass123",
            role="sales"
        )
        SupplierStaffMembership.objects.create(
            supplier=self.supplier,
            user=self.sales_user,
            role="sales",
            is_active=True
        )

        # Consumer + Contact
        self.consumer_user = User.objects.create_user(
            username="consumer1",
            password="pass123",
            role="consumer_contact"
        )

        self.consumer = Consumer.objects.create(name="Consumer1")

        ConsumerContact.objects.create(
            consumer=self.consumer,
            user=self.consumer_user,
            is_primary=True
        )

        # Supplier-Consumer Approved Link
        SupplierConsumerLink.objects.create(
            supplier=self.supplier,
            consumer=self.consumer,
            requested_by=self.sales_user,
            status="approved"
        )

        # Product
        self.product = Product.objects.create(
            supplier=self.supplier,
            name="Product1",
            unit="kg",
            price=100,
            stock=50
        )

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    # -----------------------------------------------------------------------------
    # LIST PRODUCTS
    # -----------------------------------------------------------------------------

    def test_consumer_can_list_products_from_linked_supplier(self):
        self.authenticate(self.consumer_user)

        url = reverse("product-list")
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["id"], str(self.product.id))

    def test_consumer_cannot_see_unlinked_supplier_products(self):
        # Create another unlinked supplier + product
        other_supplier_owner = User.objects.create_user("own2", "pass123")
        other_supplier = Supplier.objects.create(
            owner=other_supplier_owner,
            name="OTHER"
        )
        Product.objects.create(
            supplier=other_supplier,
            name="HiddenProduct",
            unit="item",
            price=10,
            stock=5,
        )

        self.authenticate(self.consumer_user)

        url = reverse("product-list")
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)  # Consumer sees only supplier1 products

    def test_supplier_staff_can_list_all_products(self):
        self.authenticate(self.manager_user)

        url = reverse("product-list")
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)

    # -----------------------------------------------------------------------------
    # CREATE / UPDATE / DELETE
    # -----------------------------------------------------------------------------

    def test_consumer_cannot_create_product(self):
        self.authenticate(self.consumer_user)

        url = reverse("product-list")
        payload = {
            "supplier": str(self.supplier.id),
            "name": "X",
            "unit": "kg",
            "price": 10,
            "stock": 5,
        }

        resp = self.client.post(url, payload)
        self.assertEqual(resp.status_code, 403)

    def test_supplier_staff_can_create_product(self):
        self.authenticate(self.manager_user)

        url = reverse("product-list")
        payload = {
            "supplier": str(self.supplier.id),
            "name": "Created",
            "unit": "kg",
            "price": 111,
            "stock": 22,
        }

        resp = self.client.post(url, payload)
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["name"], "Created")

    def test_supplier_staff_can_update_product(self):
        self.authenticate(self.manager_user)
        url = reverse("product-detail", args=[self.product.id])

        resp = self.client.patch(url, {"price": 777})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(float(resp.data["price"]), 777)

    def test_consumer_cannot_update_product(self):
        self.authenticate(self.consumer_user)
        url = reverse("product-detail", args=[self.product.id])

        resp = self.client.patch(url, {"price": 123})
        self.assertEqual(resp.status_code, 403)

    def test_supplier_staff_can_delete_product(self):
        self.authenticate(self.manager_user)
        url = reverse("product-detail", args=[self.product.id])

        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, 204)

    def test_consumer_cannot_delete_product(self):
        self.authenticate(self.consumer_user)
        url = reverse("product-detail", args=[self.product.id])

        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, 403)

    # -----------------------------------------------------------------------------
    # ADJUST STOCK ACTION
    # -----------------------------------------------------------------------------

    def test_supplier_staff_can_adjust_stock(self):
        self.authenticate(self.manager_user)
        url = reverse("product-adjust-stock", args=[self.product.id])

        resp = self.client.post(url, {"delta": 10})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(float(resp.data["stock"]), 60)

    def test_consumer_cannot_adjust_stock(self):
        self.authenticate(self.consumer_user)
        url = reverse("product-adjust-stock", args=[self.product.id])

        resp = self.client.post(url, {"delta": 10})
        self.assertEqual(resp.status_code, 403)

    # -----------------------------------------------------------------------------
    # PRODUCT ATTACHMENT
    # -----------------------------------------------------------------------------

    def test_supplier_staff_can_create_attachment(self):
        self.authenticate(self.sales_user)
        url = reverse("product-attachment-list")

        payload = {
            "product": str(self.product.id),
            "url": "https://example.com/manual.pdf"
        }

        resp = self.client.post(url, payload)
        self.assertEqual(resp.status_code, 201)

    def test_consumer_cannot_create_attachment(self):
        self.authenticate(self.consumer_user)
        url = reverse("product-attachment-list")

        payload = {
            "product": str(self.product.id),
            "url": "https://example.com/manual.pdf"
        }

        resp = self.client.post(url, payload)
        self.assertEqual(resp.status_code, 403)
