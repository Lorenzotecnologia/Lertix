from django.urls import path

from . import views

urlpatterns = [
    path("", views.storefront, name="storefront"),
    path("livros/<slug:slug>/", views.book_detail, name="book-detail"),
    path("contato/", views.contact_submit, name="contact"),
    path("carrinho/", views.cart_detail, name="cart"),
    path("carrinho/frete/", views.shipping_calc, name="shipping-calc"),
    path("carrinho/adicionar/<slug:slug>/", views.cart_add, name="cart-add"),
    path("carrinho/atualizar/<int:book_id>/", views.cart_update, name="cart-update"),
    path("carrinho/remover/<int:book_id>/", views.cart_remove, name="cart-remove"),
    path("pedido/", views.checkout, name="checkout"),
    path("pedido/recebido/", views.order_done, name="order-done"),
    path("api/health/", views.health_check, name="health-check"),
    path("api/livros/", views.api_books, name="api-books"),
    path("api/livros/<slug:slug>/", views.api_book_detail, name="api-book-detail"),
]
