from django.contrib import admin
from .models import Supplier, SupplierKYBDocument


# ------------------------------
# SUPPLIER KYB DOCUMENT ADMIN
# ------------------------------
@admin.register(SupplierKYBDocument)
class SupplierKYBDocumentAdmin(admin.ModelAdmin):
    list_display = ("supplier", "uploaded_by", "uploaded_at", "note")
    list_filter = ("uploaded_at", "uploaded_by")
    search_fields = ("supplier__name", "uploaded_by__email")
    readonly_fields = ("uploaded_at",)


# ------------------------------
# SUPPLIER ADMIN WITH KYB FILTERS
# ------------------------------
class KYBStatusFilter(admin.SimpleListFilter):
    title = "KYB Status"
    parameter_name = "kyb_status"

    def lookups(self, request, model_admin):
        return [
            ("incoming", "Incoming / Submitted"),
            ("pending", "Pending Review"),
            ("unsubmitted", "Unsubmitted"),
            ("verified", "Verified"),
            ("rejected", "Rejected"),
        ]

    def queryset(self, request, queryset):
        value = self.value()

        if value == "incoming":
            # Supplier submitted docs but not yet verified
            return queryset.filter(verification_status__in=["pending"])
        if value == "pending":
            return queryset.filter(verification_status="pending")
        if value == "unsubmitted":
            return queryset.filter(verification_status="unsubmitted")
        if value == "verified":
            return queryset.filter(verification_status="verified")
        if value == "rejected":
            return queryset.filter(verification_status="rejected")

        return queryset


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "owner",
        "verification_status",
        "is_verified",
        "created_at",
    )
    list_filter = (
        KYBStatusFilter,
        "is_verified",
        "created_at",
    )
    search_fields = ("name", "legal_name", "owner__email")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Basic Info", {
            "fields": (
                "name",
                "legal_name",
                "owner",
                "description",
                "country",
                "city",
                "address",
                "contact_email",
                "contact_phone",
            )
        }),
        ("KYB Verification", {
            "fields": (
                "verification_status",
                "is_verified",
            )
        }),
        ("Metadata", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
    )
