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
# Serializers (compact but include key fields)
# -------------------------------

class UserReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'display_name', 'phone', 'is_active_user']
        extra_kwargs = {'username': {'required': False}, 'password': {'required': False}}
        read_only_fields = fields

class UserWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'role', 'display_name', 'phone']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
        )
        user.role = validated_data.get('role')
        user.display_name = validated_data.get('display_name', '')
        user.phone = validated_data.get('phone', '')
        user.save()
        return user
    
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
    user = UserReadSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='user')
    class Meta:
        model = ConsumerContact
        fields = ['consumer','user','user_id','title','is_primary']

class SupplierStaffMembershipSerializer(serializers.ModelSerializer):
    user = UserReadSerializer(read_only=True)
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
    
    def create(self, validated_data):
        validated_data['consumer'] = self.context['request'].user.consumer_profile
        validated_data['status'] = 'pending'
        return super().create(validated_data)

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