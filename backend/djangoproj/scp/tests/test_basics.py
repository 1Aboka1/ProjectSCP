from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from scp.models import ConsumerContact, OrderItem, SupplierStaffMembership, User, Supplier, Consumer, Product, Order, SupplierConsumerLink
from rest_framework.authtoken.models import Token

class SCPAPITestCase(APITestCase):
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

        # Register Supplier Owner as staff
        self.owner_membership = SupplierStaffMembership.objects.create(
            supplier=self.supplier,
            user=self.supplier_owner,
            role="owner",
            is_active=True
        )

        # Manager
        self.manager_user = User.objects.create_user(
            username="manager1",
            password="pass123",
            role="manager"
        )
        self.manager_membership = SupplierStaffMembership.objects.create(
            supplier=self.supplier,
            user=self.manager_user,
            role="manager",
            is_active=True
        )

        # Sales
        self.sales_user = User.objects.create_user(
            username="sales1",
            password="pass123",
            role="sales"
        )
        self.sales_membership = SupplierStaffMembership.objects.create(
            supplier=self.supplier,
            user=self.sales_user,
            role="sales",
            is_active=True
        )

        # Consumer User
        self.consumer_user = User.objects.create_user(
            username="consumer1",
            password="pass123",
            role="consumer_contact"
        )

        # Consumer Organization
        self.consumer = Consumer.objects.create(
            name="Consumer1"
        )

        # Link user to consumer
        self.consumer_contact = ConsumerContact.objects.create(
            consumer=self.consumer,
            user=self.consumer_user,
            is_primary=True
        )

        # Create approved link
        self.link = SupplierConsumerLink.objects.create(
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
        """Force authenticate for tests."""
        self.client.force_authenticate(user=user)

    # --------------------------
    # User tests
    # --------------------------
    def test_list_users(self):
        self.authenticate(self.supplier_owner)

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
        self.authenticate(self.supplier_owner)

        url = reverse('supplier-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.supplier.name, [s['name'] for s in response.data])

    def test_create_supplier(self):
        self.authenticate(self.supplier_owner)

        url = reverse('supplier-list')
        data = {"name": "NewSupplier"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Supplier.objects.filter(name="NewSupplier").exists())

    # --------------------------
    # Consumer tests
    # --------------------------
    def test_list_consumers(self):
        self.authenticate(self.supplier_owner)

        url = reverse('consumer-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.consumer.name, [c['name'] for c in response.data])

    # --------------------------
    # Product tests
    # --------------------------
    def test_list_products(self):
        self.authenticate(self.supplier_owner)

        url = reverse('product-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.product.name, [p['name'] for p in response.data])

    def test_create_product(self):
        self.authenticate(self.sales_user)

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
        self.authenticate(self.consumer_user)

        url = reverse('order-list')

        # Create an OrderItem payload
        items_data = [
            {
                "product": str(self.product.id),
                "quantity": 2,
            },
            {
                "product": str(self.product.id),
                "quantity": 3
            }
        ]

        data = {
            "supplier": str(self.supplier.id),
            "consumer": str(self.consumer.id),
            "placed_by": str(self.consumer_user.id),
            "status": "pending",
            "total_amount": 500,  # e.g., 2*100 + 3*100
            "items": items_data
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], "pending")
        self.assertEqual(len(response.data['items']), 2)


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
