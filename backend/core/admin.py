from django.contrib import admin
from django.contrib.admin import AdminSite
from django.db.models import Count, Q

from .models import Book


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
