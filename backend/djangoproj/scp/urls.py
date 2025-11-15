# scp/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

router.register(r'users', views.UserViewSet, basename='user')
router.register(r'suppliers', views.SupplierViewSet, basename='supplier')
router.register(r'supplier-kyb', views.SupplierKYBDocumentViewSet, basename='supplier-kyb')
router.register(r'consumers', views.ConsumerViewSet, basename='consumer')
router.register(r'consumer-contacts', views.ConsumerContactViewSet, basename='consumer-contact')
router.register(r'staff', views.SupplierStaffMembershipViewSet, basename='staff')
router.register(r'links', views.LinkViewSet, basename='link')
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'product-attachments', views.ProductAttachmentViewSet, basename='product-attachment')
router.register(r'orders', views.OrderViewSet, basename='order')
router.register(r'order-items', views.OrderItemViewSet, basename='order-item')
router.register(r'complaints', views.ComplaintViewSet, basename='complaint')
router.register(r'incidents', views.IncidentViewSet, basename='incident')
router.register(r'conversations', views.ConversationViewSet, basename='conversation')
router.register(r'messages', views.MessageViewSet, basename='message')
router.register(r'attachments', views.AttachmentViewSet, basename='attachment')
router.register(r'ratings', views.RatingViewSet, basename='rating')
router.register(r'notifications', views.NotificationViewSet, basename='notification')
router.register(r'auditlogs', views.AuditLogViewSet, basename='auditlog')

urlpatterns = [
    path('api/', include(router.urls)),
    # optionally include DRF auth views (login/logout for browsable API)
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]
