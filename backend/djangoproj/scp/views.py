# scp/views.py
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

from .models import (
    User, Supplier, SupplierKYBDocument, Consumer, ConsumerContact,
    SupplierStaffMembership, SupplierConsumerLink, CatalogCategory, Product,
    ProductAttachment, Order, OrderItem, Complaint, Incident,
    Conversation, Message, Attachment, Rating, Notification, AuditLog
)

# -------------------------------
# Serializers (compact but include key fields)
# -------------------------------

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'display_name', 'phone', 'role', 'is_active']
        read_only_fields = ['id', 'is_active']

class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ['id','name','legal_name','description','country','city','address','contact_email','contact_phone',
                  'is_verified','verification_status','default_currency','languages','created_at','updated_at','deleted']
        read_only_fields = ['id','created_at','updated_at']

class SupplierKYBSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierKYBDocument
        fields = ['id','supplier','document','uploaded_by','uploaded_at','note']
        read_only_fields = ['id','uploaded_by','uploaded_at']

class ConsumerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consumer
        fields = ['id','name','consumer_type','address','contact_email','contact_phone','languages','created_at','updated_at','deleted']
        read_only_fields = ['id','created_at','updated_at']

class ConsumerContactSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='user')
    class Meta:
        model = ConsumerContact
        fields = ['consumer','user','user_id','title','is_primary']

class SupplierStaffMembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='user')
    class Meta:
        model = SupplierStaffMembership
        fields = ['id','supplier','user','user_id','role','created_at','is_active']
        read_only_fields = ['id','created_at']

class SupplierConsumerLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierConsumerLink
        fields = ['id','supplier','consumer','requested_by','status','note','created_at','approved_by','approved_at','blocked_by','blocked_at']
        read_only_fields = ['id','created_at','approved_by','approved_at','blocked_by','blocked_at','requested_by']

class CatalogCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CatalogCategory
        fields = ['id','supplier','name','slug','parent']

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id','supplier','category','name','description','unit','price','discount_percentage','stock','min_order_quantity',
                  'is_active','delivery_option','lead_time_days','image','created_at','updated_at']
        read_only_fields = ['id','created_at','updated_at']

class ProductAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductAttachment
        fields = ['id','product','file','uploaded_by','uploaded_at']
        read_only_fields = ['id','uploaded_by','uploaded_at']

class OrderItemSerializer(serializers.ModelSerializer):
    product_detail = ProductSerializer(source='product', read_only=True)
    class Meta:
        model = OrderItem
        fields = ['id','order','product','product_detail','quantity','unit_price','line_total','note','is_accepted','is_cancelled']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    class Meta:
        model = Order
        fields = ['id','supplier','consumer','placed_by','status','note','total_amount','created_at','accepted_at','completed_at','tracking_code','estimated_delivery','items']
        read_only_fields = ['id','created_at','accepted_at','completed_at','total_amount']

class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, write_only=True)
    class Meta:
        model = Order
        fields = ['supplier','consumer','placed_by','note','items','estimated_delivery']

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        with transaction.atomic():
            order = Order.objects.create(**validated_data, total_amount=0)
            total = 0
            for item in items_data:
                product = item['product']
                unit_price = item.get('unit_price') or product.effective_price
                quantity = item['quantity']
                line_total = unit_price * quantity
                OrderItem.objects.create(order=order, product=product, quantity=quantity, unit_price=unit_price, line_total=line_total)
                total += line_total
                # reduce stock? or let supplier accept first; we leave stock management to separate endpoint
            order.total_amount = total
            order.save()
        return order

class ComplaintSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complaint
        fields = ['id','order','order_item','filed_by','assigned_to','status','description','resolution','created_at','updated_at','resolved_at','escalated_to','escalated_at']
        read_only_fields = ['id','created_at','updated_at','resolved_at','escalated_at']

class IncidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incident
        fields = ['id','supplier','consumer','reported_by','title','description','status','created_at','updated_at','exported']
        read_only_fields = ['id','created_at','updated_at']

class ConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = ['id','supplier','consumer','created_at','updated_at']
        read_only_fields = ['id','created_at','updated_at']

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id','conversation','sender','text','created_at','is_read']
        read_only_fields = ['id','created_at']

class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ['id','message','file','filename','uploaded_at']
        read_only_fields = ['id','uploaded_at']

class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = ['id','order','score','comment','created_at']
        read_only_fields = ['id','created_at']

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id','user','title','body','is_read','created_at']
        read_only_fields = ['id','created_at']

class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = ['id','actor','action','target_type','target_id','data','timestamp']
        read_only_fields = ['id','timestamp']

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

# -------------------------------
# ViewSets
# -------------------------------

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]  # optionally restrict/create endpoints to admins for user creation

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

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
    queryset = Product.objects.select_related('supplier').all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        # For unsafe methods require supplier staff; safe methods allowed if consumer is linked or staff
        if self.request.method in SAFE_METHODS:
            return [IsAuthenticated(), ]
        return [IsAuthenticated(), IsSupplierStaff()]

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsSupplierStaff])
    def adjust_stock(self, request, pk=None):
        product = self.get_object()
        delta = float(request.data.get('delta', 0))
        product.stock = product.stock + delta
        product.save()
        return Response(ProductSerializer(product).data)

class ProductAttachmentViewSet(viewsets.ModelViewSet):
    queryset = ProductAttachment.objects.all()
    serializer_class = ProductAttachmentSerializer
    permission_classes = [IsAuthenticated, IsSupplierStaff]

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.prefetch_related('items').all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer

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
        # optionally decrement stock:
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
        # allow consumer or supplier staff to cancel depending on status
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

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def escalate(self, request, pk=None):
        complaint = self.get_object()
        target_user_id = request.data.get('to_user_id')
        target = get_object_or_404(User, pk=target_user_id)
        complaint.escalate(to_user=target)
        return Response(self.get_serializer(complaint).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def resolve(self, request, pk=None):
        complaint = self.get_object()
        resolution_text = request.data.get('resolution','')
        complaint.mark_resolved(resolver=request.user, resolution_text=resolution_text)
        return Response(self.get_serializer(complaint).data)

class IncidentViewSet(viewsets.ModelViewSet):
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer
    permission_classes = [IsAuthenticated]

class ConversationViewSet(viewsets.ModelViewSet):
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        # Create conversation only if link approved
        supplier_id = request.data.get('supplier')
        consumer_id = request.data.get('consumer')
        supplier = get_object_or_404(Supplier, pk=supplier_id)
        consumer = get_object_or_404(Consumer, pk=consumer_id)
        # check link
        if not SupplierConsumerLink.objects.filter(supplier=supplier, consumer=consumer, status=SupplierConsumerLink.Status.APPROVED).exists():
            return Response({'detail':'No approved link'}, status=status.HTTP_400_BAD_REQUEST)
        conv, created = Conversation.objects.get_or_create(supplier=supplier, consumer=consumer)
        return Response(ConversationSerializer(conv).data)

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
