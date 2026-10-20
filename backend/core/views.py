import logging

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from .cart import Cart
from .context_processors import whatsapp_url
from .pix import build_pix_payload, qr_svg
from . import shipping
from .forms import CheckoutForm, ContactForm
from .models import Book, Order, OrderItem

logger = logging.getLogger(__name__)


def storefront(request, contact_form=None):
    books = Book.objects.filter(is_published=True)
    return render(
        request,
        "index.html",
        {
            "books": books,
            "author": "Antonio Dalama Lorenzo",
            "page_title": "Lertrix Edições — literatura ibero-americana",
            "meta_description": (
                "Editora independente com livros de memória e literatura ibero-americana "
                "em português, espanhol e inglês."
            ),
            "current_page": "storefront",
            "contact_form": contact_form or ContactForm(),
            "contact_error": contact_form is not None,
        },
    )


def book_detail(request, slug):
    book = get_object_or_404(Book, slug=slug, is_published=True)
    return render(
        request,
        "book_detail.html",
        {
            "book": book,
            "page_title": f"{book.title} — Lertrix Edições",
            "meta_description": book.description or book.title,
            "book_whatsapp_url": whatsapp_url(
                f"Olá! Tenho interesse no livro “{book.title}”."
            ),
            "current_page": "book",
        },
    )


def health_check(request):
    return JsonResponse({"status": "ok"})


def _book_data(request, book):
    return {
        "slug": book.slug,
        "title": book.title,
        "author": book.author,
        "description": book.description,
        "price": str(book.price) if book.price is not None else None,
        "cover": request.build_absolute_uri(book.cover.url) if book.cover else None,
        "url": request.build_absolute_uri(f"/livros/{book.slug}/"),
        "isbn_13": book.isbn_13,
        "isbn_10": book.isbn_10,
        "publisher": book.publisher,
        "language": book.language,
        "page_count": book.page_count,
    }


@require_GET
def api_books(request):
    books = Book.objects.filter(is_published=True)
    return JsonResponse({"results": [_book_data(request, b) for b in books]})


@require_GET
def api_book_detail(request, slug):
    book = get_object_or_404(Book, slug=slug, is_published=True)
    return JsonResponse(_book_data(request, book))


def contact_submit(request):
    if request.method != "POST":
        return redirect("/#contato")
    form = ContactForm(request.POST)
    if not form.is_valid():
        return storefront(request, contact_form=form)
    message = form.save()
    try:
        send_mail(
            subject=f"[Site Lertrix] {message.subject or 'Nova mensagem'}",
            message=f"De: {message.name} <{message.email}>\n\n{message.message}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.CONTACT_EMAIL_TO],
        )
    except Exception:
        # A mensagem já está salva no admin; o envio pode ser refeito depois.
        logger.exception("Falha ao enviar e-mail de contato #%s", message.pk)
    messages.success(request, "Mensagem enviada! Responderemos em breve.")
    return redirect("/#contato")


def cart_detail(request):
    cart = Cart(request)
    lines = cart.lines()
    subtotal = cart.total()
    cep = request.session.get("cep", "")
    freight = shipping.quote(cep, lines, subtotal) if cep and lines else None
    return render(
        request,
        "cart.html",
        {
            "lines": lines,
            "total": subtotal,
            "cep": cep,
            "freight": freight,
            "correios_enabled": shipping.correios.is_configured(),
            "freight_total": subtotal + (freight["price"] if freight else 0),
            "cep_invalid": bool(cep) and not shipping.cep_to_state(cep),
            "page_title": "Carrinho — Lertrix Edições",
            "meta_description": "Seu carrinho na Lertrix Edições.",
            "current_page": "cart",
        },
    )


@require_POST
def shipping_calc(request):
    cep = shipping.normalize_cep(request.POST.get("cep", ""))
    if cep:
        request.session["cep"] = cep
    else:
        request.session["cep"] = request.POST.get("cep", "")[:12] or ""
    return redirect("cart")


@require_POST
def cart_add(request, slug):
    book = get_object_or_404(Book, slug=slug, is_published=True, price__isnull=False)
    Cart(request).add(book)
    return redirect("cart")


@require_POST
def cart_update(request, book_id):
    cart = Cart(request)
    try:
        quantity = int(request.POST.get("quantity", 1))
    except ValueError:
        quantity = 1
    cart.set(book_id, quantity)
    return redirect("cart")


@require_POST
def cart_remove(request, book_id):
    Cart(request).remove(book_id)
    return redirect("cart")


def checkout(request):
    cart = Cart(request)
    lines = cart.lines()
    if not lines:
        return redirect("cart")
    cep = request.session.get("cep", "")
    form = CheckoutForm(request.POST or None, initial={"postal_code": cep})
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            order = form.save(commit=False)
            subtotal = sum(line["subtotal"] for line in lines)
            freight = shipping.quote(order.postal_code, lines, subtotal)
            if freight:
                order.shipping_cost = freight["price"]
                order.shipping_days = freight["days"]
                order.shipping_service = freight["service"]
            order.total = subtotal + (freight["price"] if freight else 0)
            order.save()
            OrderItem.objects.bulk_create(
                OrderItem(
                    order=order,
                    book=line["book"],
                    title=line["book"].title,
                    unit_price=line["book"].price,
                    quantity=line["quantity"],
                )
                for line in lines
            )
        cart.clear()
        request.session["last_order_id"] = order.pk
        _notify_order(order)
        return redirect("order-done")
    return render(
        request,
        "checkout.html",
        {
            "form": form,
            "lines": lines,
            "total": cart.total(),
            "freight": shipping.quote(cep, lines, cart.total()) if cep else None,
            "correios_enabled": shipping.correios.is_configured(),
            "page_title": "Finalizar pedido — Lertrix Edições",
            "meta_description": "Finalize seu pedido na Lertrix Edições.",
            "current_page": "cart",
        },
    )


def _notify_order(order):
    items = "\n".join(f"- {i}" for i in order.items.all())
    body = (
        f"Pedido #{order.pk}\nCliente: {order.customer_name} <{order.customer_email}>\n"
        f"Telefone: {order.customer_phone}\n"
        f"Entrega: {order.address}, {order.address_number} {order.address_complement} — "
        f"{order.district}, {order.city}/{order.state}, CEP {order.postal_code}\n\n"
        f"{items}\n\nFrete: {order.shipping_service or 'a combinar'} — "
        f"R$ {order.shipping_cost if order.shipping_cost is not None else 'a combinar'}\n"
        f"Total: R$ {order.total}\nObs.: {order.notes}"
    )
    try:
        send_mail(
            f"[Site Lertrix] Novo pedido #{order.pk}",
            body,
            settings.DEFAULT_FROM_EMAIL,
            [settings.CONTACT_EMAIL_TO],
        )
    except Exception:
        logger.exception("Falha ao notificar pedido #%s", order.pk)


def order_done(request):
    order_id = request.session.get("last_order_id")
    order = Order.objects.filter(pk=order_id).first() if order_id else None
    if order is None:
        return redirect("storefront")
    pix_code = build_pix_payload(
        settings.PIX_KEY,
        settings.PIX_RECEIVER_NAME,
        settings.PIX_RECEIVER_CITY,
        order.total,
        f"LERTRIX{order.pk}",
    )
    return render(
        request,
        "order_done.html",
        {
            "order": order,
            "pix_code": pix_code,
            "pix_qr": qr_svg(pix_code),
            "order_whatsapp_url": whatsapp_url(
                f"Olá! Fiz o pedido #{order.pk} no site da Lertrix Edições "
                f"em nome de {order.customer_name}. Segue o comprovante do Pix "
                "e o CEP para combinarmos o frete."
            ),
            "page_title": "Pedido recebido — Lertrix Edições",
            "meta_description": "Pedido recebido.",
            "current_page": "cart",
        },
    )
