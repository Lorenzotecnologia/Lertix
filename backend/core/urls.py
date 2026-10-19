from django.urls import path

from .views import book_detail, health_check, storefront

urlpatterns = [
    path("", storefront, name="storefront"),
    path("livros/<slug:slug>/", book_detail, name="book-detail"),
    path("api/health/", health_check, name="health-check"),
]
