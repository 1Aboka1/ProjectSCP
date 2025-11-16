from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
import uuid


# -----------------------------
# Custom User
# -----------------------------
class User(AbstractUser):
    """
    Single user model for all actors. Use `role` to separate capabilities.
    Link to Supplier / Consumer via membership models below.
    """
    class Roles(models.TextChoices):
        OWNER = "owner", "Supplier Owner"
        MANAGER = "manager", "Supplier Manager"
        SALES = "sales", "Sales Representative"
        CONSUMER_CONTACT = "consumer_contact", "Consumer Contact"
        PLATFORM_ADMIN = "platform_admin", "Platform Admin"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(max_length=32, choices=Roles.choices, null=True, blank=True)
    phone = models.CharField(max_length=32, blank=True, null=True)
    # optional: human-readable display name for contacts
    display_name = models.CharField(max_length=200, blank=True, null=True)

    # soft-delete
    is_active_user = models.BooleanField(default=True)

    class Meta:
        db_table = "auth_user"

    def __str__(self):
        return self.display_name or self.get_full_name() or self.username


# -----------------------------
# Organizations: Supplier & Consumer
# -----------------------------
class Supplier(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    legal_name = models.CharField(max_length=512, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    country = models.CharField(max_length=128, blank=True, null=True)
    city = models.CharField(max_length=128, blank=True, null=True)
    address = models.CharField(max_length=512, blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=32, blank=True, null=True)
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="owned_suppliers",
        null=True,
        blank=True
    )

    # KYB / verification
    is_verified = models.BooleanField(default=False)
    verification_status = models.CharField(
        max_length=32,
        choices=[("unsubmitted", "Unsubmitted"), ("pending", "Pending"), ("verified", "Verified"), ("rejected", "Rejected")],
        default="unsubmitted",
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    deleted = models.BooleanField(default=False)

    default_currency = models.CharField(max_length=8, default="KZT")
    languages = models.JSONField(default=list, blank=True)  # e.g. ["kk", "ru", "en"]

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class SupplierKYBDocument(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="kyb_documents")
    document = models.FileField(upload_to="kyb/%Y/%m/%d/")
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    uploaded_at = models.DateTimeField(default=timezone.now)
    note = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"KYB doc for {self.supplier.name} ({self.id})"


class Consumer(models.Model):
    """
    Institutional consumer: restaurant or hotel. Consumers are organizations that can have many user contacts.
    """
    class Types(models.TextChoices):
        RESTAURANT = "restaurant", "Restaurant"
        HOTEL = "hotel", "Hotel"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    consumer_type = models.CharField(max_length=32, choices=Types.choices, default=Types.RESTAURANT)
    address = models.CharField(max_length=512, blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=32, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    deleted = models.BooleanField(default=False)

    languages = models.JSONField(default=list, blank=True)

    def __str__(self):
        return self.name


class ConsumerContact(models.Model):
    consumer = models.ForeignKey(Consumer, on_delete=models.CASCADE, related_name="contacts")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="consumer_contacts")
    title = models.CharField(max_length=128, blank=True, null=True)
    is_primary = models.BooleanField(default=False)

    class Meta:
        unique_together = ("consumer", "user")

    def __str__(self):
        return f"{self.user} @ {self.consumer}"


# -----------------------------
# Supplier staff membership
# -----------------------------
class SupplierStaffMembership(models.Model):
    class StaffRole(models.TextChoices):
        OWNER = "owner", "Owner"
        MANAGER = "manager", "Manager"
        SALES = "sales", "Sales Representative"

    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="supplier_memberships")
    role = models.CharField(max_length=32, choices=StaffRole.choices)
    created_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("supplier", "user")

    def __str__(self):
        return f"{self.user} as {self.role} @ {self.supplier.name}"


# -----------------------------
# Linking model (Supplier <-> Consumer)
# -----------------------------
class SupplierConsumerLink(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        BLOCKED = "blocked", "Blocked"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="links")
    consumer = models.ForeignKey(Consumer, on_delete=models.CASCADE, related_name="links")
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="link_requests_made")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    # approval metadata
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="link_approvals")
    approved_at = models.DateTimeField(blank=True, null=True)

    blocked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="link_blocks")
    blocked_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ("supplier", "consumer")

    def approve(self, approver: models.Model):
        self.status = self.Status.APPROVED
        self.approved_by = approver
        self.approved_at = timezone.now()
        self.save()

    def reject(self, approver: models.Model, reason: str = ""):
        self.status = self.Status.REJECTED
        self.approved_by = approver
        self.note = reason
        self.approved_at = timezone.now()
        self.save()

    def block(self, by: models.Model, reason: str = ""):
        self.status = self.Status.BLOCKED
        self.blocked_by = by
        self.blocked_at = timezone.now()
        self.note = reason
        self.save()

    def __str__(self):
        return f"Link {self.supplier} <-> {self.consumer} ({self.status})"


# -----------------------------
# Catalog, Products, Inventory
# -----------------------------
class CatalogCategory(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="categories")
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="children")

    class Meta:
        unique_together = ("supplier", "slug")

    def __str__(self):
        return f"{self.supplier.name} / {self.name}"


class Product(models.Model):
    DELIVERY_OPTIONS = [
        ("delivery", "Delivery"),
        ("pickup", "Pickup"),
        ("both", "Delivery and Pickup"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="products")
    category = models.ForeignKey(CatalogCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")

    name = models.CharField(max_length=512)
    description = models.TextField(blank=True, null=True)

    # base unit (e.g. kg, liter, piece) and alternate units could be expanded later
    unit = models.CharField(max_length=64, help_text="Human-readable unit, e.g. kg, liter, piece")

    # pricing and inventory
    price = models.DecimalField(max_digits=12, decimal_places=2)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    stock = models.DecimalField(max_digits=14, decimal_places=3, default=0)  # allow fractional (kg/l)
    min_order_quantity = models.DecimalField(max_digits=12, decimal_places=3, default=1)

    is_active = models.BooleanField(default=True)
    delivery_option = models.CharField(max_length=16, choices=DELIVERY_OPTIONS, default="both")
    lead_time_days = models.PositiveIntegerField(default=0)

    # optional product images/files
    image = models.ImageField(upload_to="products/%Y/%m/%d/", blank=True, null=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("supplier", "name")

    @property
    def effective_price(self):
        if self.discount_percentage:
            return self.price * (1 - (self.discount_percentage / 100))
        return self.price

    def __str__(self):
        return f"{self.name} — {self.supplier.name}"


class ProductAttachment(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to="product_attachments/%Y/%m/%d/")
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    uploaded_at = models.DateTimeField(default=timezone.now)


# -----------------------------
# Orders & Order Items
# -----------------------------
class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="orders")
    consumer = models.ForeignKey(Consumer, on_delete=models.CASCADE, related_name="orders")
    placed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders_placed")

    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PENDING)
    note = models.TextField(blank=True, null=True)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    created_at = models.DateTimeField(default=timezone.now)
    accepted_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    # tracking fields (could be extended to shipment/fulfillment model)
    tracking_code = models.CharField(max_length=255, blank=True, null=True)
    estimated_delivery = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order {self.id} — {self.consumer.name} -> {self.supplier.name} [{self.status}]"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    line_total = models.DecimalField(max_digits=14, decimal_places=2)
    note = models.TextField(blank=True, null=True)

    # statuses to allow partial acceptance/cancellation at item level if needed
    is_accepted = models.BooleanField(default=False)
    is_cancelled = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # compute line total
        self.line_total = (self.unit_price or self.product.effective_price) * (self.quantity or 0)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} ({self.order.id})"


# -----------------------------
# Complaints & Escalation
# -----------------------------
class Complaint(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        IN_PROGRESS = "in_progress", "In Progress"
        RESOLVED = "resolved", "Resolved"
        ESCALATED = "escalated", "Escalated"
        CLOSED = "closed", "Closed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="complaints")
    order_item = models.ForeignKey(OrderItem, on_delete=models.SET_NULL, null=True, blank=True, related_name="complaints")
    filed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="complaints_filed")
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="complaints_assigned")

    status = models.CharField(max_length=32, choices=Status.choices, default=Status.OPEN)
    description = models.TextField()
    resolution = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(blank=True, null=True)

    # escalation trail: who it was escalated to (Manager/Owner)
    escalated_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="complaints_escalated")
    escalated_at = models.DateTimeField(blank=True, null=True)

    def escalate(self, to_user: models.Model):
        self.escalated_to = to_user
        self.escalated_at = timezone.now()
        self.status = self.Status.ESCALATED
        self.save()

    def mark_resolved(self, resolver: models.Model, resolution_text: str):
        self.resolution = resolution_text
        self.status = self.Status.RESOLVED
        self.resolved_at = timezone.now()
        self.assigned_to = resolver
        self.save()

    def __str__(self):
        return f"Complaint {self.id} — {self.order.id} ({self.status})"


# -----------------------------
# Incident Logging
# -----------------------------
class Incident(models.Model):
    # general-purpose incident log which may be tied to orders, products, or supplier-wide issues
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="incidents")
    consumer = models.ForeignKey(Consumer, on_delete=models.SET_NULL, null=True, blank=True, related_name="incidents")
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    title = models.CharField(max_length=512)
    description = models.TextField()
    status = models.CharField(max_length=32, default="open")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    exported = models.BooleanField(default=False)  # flag useful for logs/exports

    def __str__(self):
        return f"Incident {self.id}: {self.title} [{self.status}]"


# -----------------------------
# Chat / Messaging
# -----------------------------
class Conversation(models.Model):
    # Conversations are created only between a supplier and consumer after link approval
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="conversations")
    consumer = models.ForeignKey(Consumer, on_delete=models.CASCADE, related_name="conversations")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("supplier", "consumer")

    def __str__(self):
        return f"Conversation: {self.consumer.name} <-> {self.supplier.name}"


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    text = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)

    # attachments handled by Attachment model
    def __str__(self):
        return f"Message {self.id} by {self.sender}"


class Attachment(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to="chat_attachments/%Y/%m/%d/")
    filename = models.CharField(max_length=512, blank=True, null=True)
    uploaded_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Attachment {self.filename or self.file.name}"


# -----------------------------
# Ratings & Reviews (OPTIONAL)
# -----------------------------
class Rating(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="rating")
    score = models.PositiveSmallIntegerField()  # 1..5
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Rating {self.score} for {self.order.id}"


# -----------------------------
# Basic notification & audit models (minimal)
# -----------------------------
class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Notification for {self.user} — {self.title}"


class AuditLog(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=255)
    target_type = models.CharField(max_length=255, blank=True, null=True)
    target_id = models.CharField(max_length=255, blank=True, null=True)
    data = models.JSONField(blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Audit: {self.action} @ {self.timestamp}"


# -----------------------------
# Data retention hint
# -----------------------------
# For compliance, add retention policies in business logic / management commands. 
# Models can be soft-deleted (deleted flag) and archived to read-only storage as required.
