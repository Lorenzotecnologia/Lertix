from django.contrib import admin
from django.contrib.admin import AdminSite
from django.db.models import Count, Q

from .models import Book, ContactMessage, Order, OrderItem, ShippingRate


class BookAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "author",
        "price",
        "is_published",
        "display_order",
        "updated_at",
    )
    list_filter = ("is_published", "book_format", "language")
    search_fields = ("title", "author", "isbn_10", "isbn_13")
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("display_order", "title")
    fieldsets = (
        (
            "Vitrine",
            {
                "fields": (
                    "title",
                    "slug",
                    "author",
                    "description",
                    "author_bio",
                    "cover",
                    "price",
                    "is_published",
                    "display_order",
                )
            },
        ),
        (
            "Detalhes do produto",
            {
                "fields": (
                    "publisher",
                    "publication_date",
                    "edition",
                    "language",
                    "book_format",
                    "page_count",
                    ("isbn_10", "isbn_13"),
                    "weight_grams",
                    "dimensions",
                    "minimum_reading_age",
                )
            },
        ),
        ("Histórico", {"fields": ("created_at", "updated_at")}),
    )
    readonly_fields = ("created_at", "updated_at")


class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "subject", "is_answered", "created_at")
    list_filter = ("is_answered",)
    search_fields = ("name", "email", "subject", "message")
    readonly_fields = ("name", "email", "subject", "message", "created_at")


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("book", "title", "unit_price", "quantity")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer_name", "customer_email", "total", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("customer_name", "customer_email")
    list_editable = ("status",)
    readonly_fields = ("created_at", "updated_at")
    inlines = [OrderItemInline]


class ShippingRateAdmin(admin.ModelAdmin):
    list_display = ("region", "states", "max_weight_grams", "price", "delivery_days", "is_active")
    list_filter = ("region", "is_active")
    list_editable = ("price", "delivery_days", "is_active")


class LertrixAdminSite(AdminSite):
    site_header = "Lertrix Edições"
    site_title = "Administração Lertrix"
    index_title = "Gestão da loja"

    def index(self, request, extra_context=None):
        book_counts = Book.objects.aggregate(
            total_books=Count("pk"),
            published_books=Count("pk", filter=Q(is_published=True)),
            draft_books=Count("pk", filter=Q(is_published=False)),
        )
        context = {**(extra_context or {}), **book_counts}
        return super().index(request, extra_context=context)


admin_site = LertrixAdminSite(name="admin")
admin_site.register(Book, BookAdmin)
admin_site.register(ContactMessage, ContactMessageAdmin)
admin_site.register(Order, OrderAdmin)
admin_site.register(ShippingRate, ShippingRateAdmin)
