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

from .serializers import (
    UserReadSerializer, UserWriteSerializer, SupplierSerializer, OrderSerializer,
    RatingSerializer, MessageSerializer, ProductSerializer, AuditLogSerializer, ConsumerSerializer,
    IncidentSerializer, ComplaintSerializer, OrderItemSerializer, AttachmentSerializer,
    OrderCreateSerializer, ConversationSerializer, NotificationSerializer, SupplierKYBSerializer,
    CatalogCategorySerializer, ConsumerContactSerializer, ProductAttachmentSerializer, SupplierConsumerLinkSerializer,
    SupplierStaffMembershipSerializer, SupplierStaffMembership
)

from .permissions import (
    IsAuthenticated, IsConversationParticipant, IsLinkedConsumerAndSupplierStaff, IsOwnerOrManager, IsSupplierStaff
)

# -------------------------------
# ViewSets
# -------------------------------

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return UserReadSerializer
        return UserWriteSerializer
    # permission_classes = []  # Keep open for registration

    # Registration
    @action(detail=False, methods=['post'], url_path='register')
    def register(self, request):
        data = request.data
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            user.set_password(data['password'])  # hash password
            user.save()
            return Response(self.get_serializer(user).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Login
    @action(detail=False, methods=['post'], url_path='login')
    def login(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user:
            # If you use token auth:
            from rest_framework.authtoken.models import Token
            token, created = Token.objects.get_or_create(user=user)
            return Response({'token': token.key})
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        supplier = serializer.save()
        # create membership for creator as owner if user is set
        if self.request.user.is_authenticated:
            SupplierStaffMembership.objects.create(supplier=supplier, user=self.request.user, role='owner')

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsOwnerOrManager])
    def create_staff(self, request, pk=None):
        supplier = self.get_object()
        user_id = request.data.get('user_id')
        role = request.data.get('role', 'sales')
        user = get_object_or_404(User, pk=user_id)
        membership, created = SupplierStaffMembership.objects.get_or_create(supplier=supplier, user=user, defaults={'role': role})
        if not created:
            membership.role = role
            membership.is_active = True
            membership.save()
        return Response(SupplierStaffMembershipSerializer(membership).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsOwnerOrManager])
    def remove_staff(self, request, pk=None):
        supplier = self.get_object()
        membership_id = request.data.get('membership_id')
        membership = get_object_or_404(SupplierStaffMembership, pk=membership_id, supplier=supplier)
        membership.is_active = False
        membership.save()
        return Response({'detail': 'membership deactivated'})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsOwnerOrManager])
    def upload_kyb(self, request, pk=None):
        supplier = self.get_object()
        serializer = SupplierKYBSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(uploaded_by=request.user, supplier=supplier)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SupplierKYBDocumentViewSet(viewsets.ModelViewSet):
    queryset = SupplierKYBDocument.objects.all()
    serializer_class = SupplierKYBSerializer
    permission_classes = [IsAuthenticated, IsSupplierStaff]

class ConsumerViewSet(viewsets.ModelViewSet):
    queryset = Consumer.objects.all()
    serializer_class = ConsumerSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def add_contact(self, request, pk=None):
        consumer = self.get_object()
        user_id = request.data.get('user_id')
        user = get_object_or_404(User, pk=user_id)
        contact, created = ConsumerContact.objects.get_or_create(consumer=consumer, user=user, defaults={'is_primary': request.data.get('is_primary', False), 'title': request.data.get('title','')})
        return Response(ConsumerContactSerializer(contact).data)

class ConsumerContactViewSet(viewsets.ModelViewSet):
    queryset = ConsumerContact.objects.all()
    serializer_class = ConsumerContactSerializer
    permission_classes = [IsAuthenticated]

class SupplierStaffMembershipViewSet(viewsets.ModelViewSet):
    queryset = SupplierStaffMembership.objects.all()
    serializer_class = SupplierStaffMembershipSerializer
    permission_classes = [IsAuthenticated, IsSupplierStaff]

class LinkViewSet(viewsets.ModelViewSet):
    queryset = SupplierConsumerLink.objects.all()
    serializer_class = SupplierConsumerLinkSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        # consumer triggers link request
        data = request.data.copy()
        # if user is consumer contact, attach requested_by
        data['requested_by'] = request.user.pk
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save(requested_by=request.user)
        return Response(self.get_serializer(obj).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsSupplierStaff])
    def approve(self, request, pk=None):
        link = self.get_object()
        if link.status != SupplierConsumerLink.Status.PENDING:
            return Response({'detail':'Link not pending'}, status=status.HTTP_400_BAD_REQUEST)
        link.approve(approver=request.user)
        return Response(self.get_serializer(link).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsSupplierStaff])
    def reject(self, request, pk=None):
        link = self.get_object()
        reason = request.data.get('reason','')
        link.reject(approver=request.user, reason=reason)
        return Response(self.get_serializer(link).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsSupplierStaff])
    def block(self, request, pk=None):
        link = self.get_object()
        reason = request.data.get('reason','')
        link.block(by=request.user, reason=reason)
        return Response(self.get_serializer(link).data)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = CatalogCategory.objects.all()
    serializer_class = CatalogCategorySerializer
    permission_classes = [IsAuthenticated, IsSupplierStaff]

class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # Platform admin sees everything
        if user.role == "platform_admin":
            return Product.objects.select_related("supplier").all()

        # Supplier staff sees only their supplier’s products
        supplier_ids = SupplierStaffMembership.objects.filter(
            user=user,
            is_active=True
        ).values_list("supplier_id", flat=True)

        if supplier_ids.exists():
            return Product.objects.select_related("supplier").filter(
                supplier_id__in=supplier_ids
            )

        # Consumer: get linked suppliers
        consumer_ids = ConsumerContact.objects.filter(
            user=user,
            is_primary=True
        ).values_list("consumer_id", flat=True)

        # find links for these consumers
        linked_supplier_ids = SupplierConsumerLink.objects.filter(
            consumer_id__in=consumer_ids,
            status=SupplierConsumerLink.Status.APPROVED,
        ).values_list("supplier_id", flat=True)

        return Product.objects.select_related("supplier").filter(
            supplier_id__in=linked_supplier_ids
        )

    def get_permissions(self):
        # Safe methods allowed to all authenticated users (supplier staff or linked consumers)
        if self.request.method in SAFE_METHODS:
            return [IsAuthenticated()]
        # Unsafe methods require supplier staff
        return [IsAuthenticated(), IsSupplierStaff()]

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsSupplierStaff])
    def adjust_stock(self, request, pk=None):
        product = self.get_object()
        delta = float(request.data.get('delta', 0))
        product.stock = float(product.stock) + delta
        product.save()
        return Response(ProductSerializer(product).data)

class ProductAttachmentViewSet(viewsets.ModelViewSet):
    queryset = ProductAttachment.objects.all()
    serializer_class = ProductAttachmentSerializer
    permission_classes = [IsAuthenticated, IsSupplierStaff]

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer

    def get_queryset(self):
        user = self.request.user

        # Consumer: only see orders for consumers they belong to
        if user.role == 'consumer_contact':
            from scp.models import ConsumerContact
            consumers = ConsumerContact.objects.filter(user=user).values_list('consumer', flat=True)
            return Order.objects.prefetch_related('items').filter(consumer__in=consumers)

        # Supplier staff: only see orders for supplier(s) they belong to
        elif user.role in ['owner', 'manager', 'sales']:
            from scp.models import SupplierStaffMembership
            suppliers = SupplierStaffMembership.objects.filter(user=user, is_active=True).values_list('supplier', flat=True)
            return Order.objects.prefetch_related('items').filter(supplier__in=suppliers)

        # Platform admins: see all orders
        elif user.role == 'platform_admin':
            return Order.objects.prefetch_related('items').all()

        # Default: empty queryset
        return Order.objects.none()

    def create(self, request, *args, **kwargs):
        # ensure consumer is linked to supplier
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save(placed_by=request.user)
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsSupplierStaff])
    def accept(self, request, pk=None):
        order = self.get_object()
        if order.status != Order.Status.PENDING:
            return Response({'detail':'Cannot accept'}, status=status.HTTP_400_BAD_REQUEST)
        order.status = Order.Status.ACCEPTED
        order.accepted_at = timezone.now()
        order.save()
        for item in order.items.all():
            p = item.product
            p.stock = p.stock - item.quantity
            p.save()
        return Response(OrderSerializer(order).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsSupplierStaff])
    def reject(self, request, pk=None):
        order = self.get_object()
        if order.status != Order.Status.PENDING:
            return Response({'detail':'Cannot reject'}, status=status.HTTP_400_BAD_REQUEST)
        order.status = Order.Status.REJECTED
        order.save()
        return Response(OrderSerializer(order).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def cancel(self, request, pk=None):
        order = self.get_object()
        if order.status in [Order.Status.COMPLETED, Order.Status.CANCELLED]:
            return Response({'detail':'Cannot cancel'}, status=status.HTTP_400_BAD_REQUEST)
        order.status = Order.Status.CANCELLED
        order.save()
        return Response(OrderSerializer(order).data)

class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated]

class ComplaintViewSet(viewsets.ModelViewSet):
    queryset = Complaint.objects.select_related('order').all()
    serializer_class = ComplaintSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(filed_by=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsSupplierStaff])
    def escalate(self, request, pk=None):
        complaint = self.get_object()
        target_user_id = request.data.get('to_user_id')
        target = get_object_or_404(User, pk=target_user_id)
        complaint.escalate(to_user=target)
        return Response(self.get_serializer(complaint).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsSupplierStaff])
    def resolve(self, request, pk=None):
        complaint = self.get_object()

        resolution_text = request.data.get('resolution')

        if not resolution_text:
            return Response(
                {"detail": "Resolution text cannot be empty."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not resolution_text.strip():
            return Response(
                {"detail": "Resolution text cannot be empty."},
                status=status.HTTP_400_BAD_REQUEST
            )

        complaint.mark_resolved(
            resolver=request.user,
            resolution_text=resolution_text
        )

        return Response(self.get_serializer(complaint).data)

class IncidentViewSet(viewsets.ModelViewSet):
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer
    permission_classes = [IsAuthenticated]

class ConversationViewSet(viewsets.ModelViewSet):
    queryset = Conversation.objects.prefetch_related('messages').all()
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated, IsConversationParticipant]

    def get_queryset(self):
        user = self.request.user
        if user.role in ['owner', 'manager', 'sales']:
            return Conversation.objects.filter(supplier__staff_members__user=user, supplier__staff_members__is_active=True)
        elif user.role == 'consumer_contact':
            return Conversation.objects.filter(consumer__contacts__user=user)
        return Conversation.objects.none()

    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        conversation = self.get_object()
        serializer = MessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(sender=request.user, conversation=conversation)
        return Response(serializer.data)

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.select_related('conversation').all()
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)

class AttachmentViewSet(viewsets.ModelViewSet):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    permission_classes = [IsAuthenticated]

class RatingViewSet(viewsets.ModelViewSet):
    queryset = Rating.objects.all()
    serializer_class = RatingSerializer
    permission_classes = [IsAuthenticated]

class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]

# end of file
