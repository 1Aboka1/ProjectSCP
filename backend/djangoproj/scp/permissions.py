from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated, BasePermission, SAFE_METHODS
from rest_framework.routers import DefaultRouter
from django.conf import settings
from django.contrib.auth import authenticate
from rest_framework.permissions import AllowAny

from .models import (
    User, Supplier, SupplierKYBDocument, Consumer, ConsumerContact,
    SupplierStaffMembership, SupplierConsumerLink, CatalogCategory, Product,
    ProductAttachment, Order, OrderItem, Complaint, Incident,
    Conversation, Message, Attachment, Rating, Notification, AuditLog
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
        # safe methods allowed for authenticated users for many endpoints; enforce object-level where needed
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # obj may be Supplier or model with .supplier
        supplier = getattr(obj, 'supplier', obj if isinstance(obj, Supplier) else None)
        if supplier is None:
            return False
        return SupplierStaffMembership.objects.filter(supplier=supplier, user=request.user, is_active=True).exists() or (request.user.role == 'platform_admin')

class IsOwnerOrManager(BasePermission):
    def has_object_permission(self, request, view, obj):
        # obj expected Supplier
        if not isinstance(obj, Supplier):
            return False
        return SupplierStaffMembership.objects.filter(supplier=obj, user=request.user, role__in=['owner','manager']).exists() or (request.user.role == 'platform_admin')

class IsLinkedConsumer(BasePermission):
    """
    Ensures consumer is linked/approved to supplier before viewing catalog/orders.
    """
    def has_permission(self, request, view):
        # For list operations, rely on querysets; for object-level, check below
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # obj may be Supplier or Product or Order
        supplier = None
        if isinstance(obj, Supplier):
            supplier = obj
        else:
            supplier = getattr(obj, 'supplier', None)
        if supplier is None:
            return False
        # find consumer(s) for request.user
        # user -> ConsumerContact -> Consumer
        contacts = ConsumerContact.objects.filter(user=request.user).values_list('consumer_id', flat=True)
        return SupplierConsumerLink.objects.filter(supplier=supplier, consumer_id__in=contacts, status=SupplierConsumerLink.Status.APPROVED).exists()
