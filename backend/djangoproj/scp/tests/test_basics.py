from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from scp.models import User, Supplier, Consumer, Product, Order, SupplierConsumerLink
from rest_framework.authtoken.models import Token

class SCPAPITestCase(APITestCase):
    def setUp(self):
        # Create Users
        self.owner = User.objects.create_user(username="owner1", password="pass123", role="owner")
        self.manager = User.objects.create_user(username="manager1", password="pass123", role="manager")
        self.sales = User.objects.create_user(username="sales1", password="pass123", role="sales")
        self.consumer_user = User.objects.create_user(username="consumer1", password="pass123", role="consumer_contact")

        # Create Supplier & Consumer
        self.supplier = Supplier.objects.create(name="Supplier1")
        self.consumer = Consumer.objects.create(name="Consumer1")

        # Create a link
        self.link = SupplierConsumerLink.objects.create(
            supplier=self.supplier,
            consumer=self.consumer,
            requested_by=self.sales,
            status="approved"
        )

        # Create Product
        self.product = Product.objects.create(
            supplier=self.supplier,
            name="Product1",
            unit="kg",
            price=100,
            stock=50
        )

        # Login owner to get token
        self.client.login(username="owner1", password="pass123")

    # --------------------------
    # User tests
    # --------------------------
    def test_list_users(self):
        url = reverse('user-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 4)  # At least the 4 users created

    def test_create_user(self):
        url = reverse('user-list')
        data = {"username": "newuser", "password": "newpass123", "role": "sales"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="newuser").exists())

    # --------------------------
    # Supplier tests
    # --------------------------
    def test_list_suppliers(self):
        url = reverse('supplier-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.supplier.name, [s['name'] for s in response.data])

    def test_create_supplier(self):
        url = reverse('supplier-list')
        data = {"name": "NewSupplier"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Supplier.objects.filter(name="NewSupplier").exists())

    # --------------------------
    # Consumer tests
    # --------------------------
    def test_list_consumers(self):
        url = reverse('consumer-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.consumer.name, [c['name'] for c in response.data])

    # --------------------------
    # Product tests
    # --------------------------
    def test_list_products(self):
        url = reverse('product-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.product.name, [p['name'] for p in response.data])

    def test_create_product(self):
        url = reverse('product-list')
        data = {
            "supplier": str(self.supplier.id),
            "name": "Product2",
            "unit": "kg",
            "price": 50,
            "stock": 10
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Product.objects.filter(name="Product2").exists())

    # --------------------------
    # Order tests
    # --------------------------
    def test_create_order(self):
        url = reverse('order-list')
        data = {
            "supplier": str(self.supplier.id),
            "consumer": str(self.consumer.id),
            "placed_by": str(self.consumer_user.id),
            "status": "pending",
            "total_amount": 100
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['status'], "pending")

    # --------------------------
    # Link tests
    # --------------------------
    def test_list_links(self):
        url = reverse('supplierconsumerlink-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(str(self.link.id), [str(l['id']) for l in response.data])

    # --------------------------
    # Edge cases: Permissions / Invalid input
    # --------------------------
    def test_create_user_without_role(self):
        url = reverse('user-list')
        data = {"username": "no_role_user", "password": "pass123"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(User.objects.get(username="no_role_user"))

    def test_invalid_product_creation(self):
        url = reverse('product-list')
        data = {"supplier": "invalid_id", "name": ""}
        response = self.client.post(url, data)
