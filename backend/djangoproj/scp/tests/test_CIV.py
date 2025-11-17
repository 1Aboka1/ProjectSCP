from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from scp.models import (
    User, Supplier, SupplierStaffMembership,
    Consumer, ConsumerContact, SupplierConsumerLink,
    CatalogCategory, Product
)

class CatalogTests(APITestCase):
    def setUp(self):
        # -----------------------------
        # Users
        # -----------------------------
        self.owner = User.objects.create_user(username="owner1", password="pass123", role="owner")
        self.manager = User.objects.create_user(username="manager1", password="pass123", role="manager")
        self.sales = User.objects.create_user(username="sales1", password="pass123", role="sales")
        self.consumer_user = User.objects.create_user(username="consumer1", password="pass123", role="consumer_contact")

        # -----------------------------
        # Supplier & Staff
        # -----------------------------
        self.supplier = Supplier.objects.create(name="Supplier1", owner=self.owner)
        self.owner_membership = SupplierStaffMembership.objects.create(
            supplier=self.supplier, user=self.owner, role="owner", is_active=True
        )
        self.manager_membership = SupplierStaffMembership.objects.create(
            supplier=self.supplier, user=self.manager, role="manager", is_active=True
        )
        self.sales_membership = SupplierStaffMembership.objects.create(
            supplier=self.supplier, user=self.sales, role="sales", is_active=True
        )

        # -----------------------------
        # Consumer & link
        # -----------------------------
        self.consumer = Consumer.objects.create(name="Consumer1")
        self.consumer_contact = ConsumerContact.objects.create(
            consumer=self.consumer, user=self.consumer_user, is_primary=True
        )
        self.link = SupplierConsumerLink.objects.create(
            supplier=self.supplier, consumer=self.consumer,
            requested_by=self.sales, status="approved"
        )

        # -----------------------------
        # Initial category and product
        # -----------------------------
        self.category = CatalogCategory.objects.create(
            supplier=self.supplier, name="Fruits", slug="fruits"
        )
        self.product = Product.objects.create(
            supplier=self.supplier,
            category=self.category,
            name="Apple",
            unit="kg",
            price=10,
            stock=100,
            min_order_quantity=1
        )

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    # -----------------------------
    # Supplier perspective tests
    # -----------------------------

    def test_supplier_owner_creates_category(self):
        self.authenticate(self.owner)
        url = reverse("category-list")
        data = {"supplier": str(self.supplier.id), "name": "Vegetables", "slug": "vegetables"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Vegetables")

    def test_supplier_manager_edits_product(self):
        self.authenticate(self.manager)
        url = reverse("product-detail", args=[self.product.id])
        data = {"price": 12, "stock": 90}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(float(self.product.price), 12)
        self.assertEqual(float(self.product.stock), 90)

    def test_supplier_sales_views_category_list(self):
        self.authenticate(self.sales)
        url = reverse("category-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 1)

    # -----------------------------
    # Consumer perspective tests
    # -----------------------------

    def test_consumer_views_supplier_catalog(self):
        self.authenticate(self.consumer_user)
        url = reverse("product-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Consumer should only see products of suppliers they are linked to
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Apple")

    def test_consumer_cannot_edit_product(self):
        self.authenticate(self.consumer_user)
        url = reverse("product-detail", args=[self.product.id])
        data = {"price": 5}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_consumer_cannot_create_category(self):
        self.authenticate(self.consumer_user)
        url = reverse("category-list")
        data = {"supplier": str(self.supplier.id), "name": "Beverages", "slug": "beverages"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # -----------------------------
    # Misc
    # -----------------------------

    def test_supplier_effective_price_property(self):
        self.product.discount_percentage = 10
        self.product.save()
        self.assertEqual(float(self.product.effective_price), 9)
