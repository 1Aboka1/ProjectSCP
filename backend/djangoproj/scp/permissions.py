from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import serializers, permissions
from rest_framework.permissions import IsAuthenticated, BasePermission, SAFE_METHODS
from rest_framework.routers import DefaultRouter
from django.conf import settings
from django.contrib.auth import authenticate
from rest_framework.permissions import AllowAny

from .models import (
    User, Supplier, SupplierKYBDocument, Consumer, ConsumerContact,
    SupplierStaffMembership, SupplierConsumerLink, CatalogCategory, Product,
    ProductAttachment, Order, OrderItem, Complaint, Incident,
    Conversation, Message, Attachment, Notification, AuditLog
)

# -------------------------------
# Permissions
# -------------------------------

class IsSupplierStaff(BasePermission):
    """
    Allow access if user is staff of the supplier (owner/manager/sales).
    Expect view to set .get_supplier() or use supplier lookup from request data.
    """
    def has_permission(self, request, view):
        user = request.user
        # safe methods allowed for authenticated users for many endpoints; enforce object-level where needed
        if user and user.is_authenticated and user.role in ["owner", "manager", "sales"]:
            return True
        return False

    def has_object_permission(self, request, view, obj):
        # Try direct supplier
        supplier = getattr(obj, 'supplier', None)

        # If obj has order, get supplier from order
        if supplier is None and hasattr(obj, 'order'):
            supplier = getattr(obj.order, 'supplier', None)

        if supplier is None:
            return False

        return (
            SupplierStaffMembership.objects.filter(supplier=supplier, user=request.user, is_active=True).exists()
            or request.user.role == 'platform_admin'
        )
    
class IsOwnerOrManager(BasePermission):
    def has_object_permission(self, request, view, obj):
        # obj expected Supplier
        if not isinstance(obj, Supplier):
            return False
        return SupplierStaffMembership.objects.filter(supplier=obj, user=request.user, role__in=['owner','manager']).exists() or (request.user.role == 'platform_admin')

class IsLinkedConsumerAndSupplierStaff(BasePermission):
    """
    Ensures consumer is linked/approved to supplier before viewing catalog/orders.
    """
    
    def has_permission(self, request, view):
        user = request.user

        # Only authenticated users
        if not user or not user.is_authenticated:
            return False

        # Supplier staff can view but not create
        if request.method in SAFE_METHODS:
            return True

        # For POST (creating incident)
        if request.method == 'POST':
            # Get all consumer instances for this user
            consumer_contacts = ConsumerContact.objects.filter(user=user)
            consumer_ids = consumer_contacts.values_list('consumer_id', flat=True)

            # Get supplier ID from request data
            supplier_id = request.data.get('supplier')
            if not supplier_id:
                return False

            # Check if there's an approved link for this consumer(s)
            is_linked = SupplierConsumerLink.objects.filter(
                consumer_id__in=consumer_ids,
                supplier_id=supplier_id,
                status=SupplierConsumerLink.Status.APPROVED
            ).exists()

            return is_linked

        # Deny all other methods
        return False

    def has_object_permission(self, request, view, obj):
        # allow supplier staff
        if SupplierStaffMembership.objects.filter(
            supplier=obj.supplier, user=request.user, is_active=True
        ).exists():
            return True

        # allow linked consumer
        linked = SupplierConsumerLink.objects.filter(
            consumer__in=ConsumerContact.objects.filter(user=request.user).values_list('consumer', flat=True),
            supplier=obj.supplier,
            status='approved'
        ).exists()
        return linked

class IsConversationParticipant(BasePermission):
    """
    Only supplier staff or consumer linked to the conversation can read/write messages.
    """
    def has_object_permission(self, request, view, obj):
        # obj is Conversation
        user = request.user
        if hasattr(user, 'role'):
            if user.role in ['owner', 'manager', 'sales']:
                return obj.supplier.staff_members.filter(user=user, is_active=True).exists()
            if user.role == 'consumer_contact':
                return obj.consumer.contacts.filter(user=user).exists()
        return False

class IsPlatformAdminOrSuperUser(permissions.BasePermission):
    """
    Allows access only to users whose `role` is 'platform_admin' or to Django superusers.
    """

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        # Allow Django superuser always
        if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
            return True

        # Role-based check (platform_admin)
        return getattr(user, "role", None) == "platform_admin"

    def has_object_permission(self, request, view, obj):
        # same behavior for object-level checks
        return self.has_permission(request, view)    