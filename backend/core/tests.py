from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Book


class HealthCheckTests(TestCase):
    def test_health_check_returns_ok(self):
        response = self.client.get(reverse("health-check"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})


class BookCatalogTests(TestCase):
    def test_catalog_is_seeded_with_confirmed_product_information(self):
        book = Book.objects.get(slug="marcia-de-antonio-memorias-de-uma-historia-de-amor")

        self.assertEqual(book.price, 63)
        self.assertEqual(book.book_format, "Capa comum")
        self.assertEqual(book.page_count, 302)
        self.assertEqual(book.isbn_10, "650062498X")
        self.assertEqual(book.isbn_13, "9786500624984")
        self.assertTrue(book.is_published)

    def test_book_detail_displays_product_information(self):
        book = Book.objects.get(slug="marcia-de-antonio-memorias-de-uma-historia-de-amor")
        response = self.client.get(
            reverse("book-detail", kwargs={"slug": book.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Memórias de uma história de Amor")
        self.assertContains(response, "R$ 63,00")
        self.assertContains(response, "650062498X")
        self.assertContains(response, "Capa comum")
        self.assertContains(response, "images/lertrix-logo.", count=1)
        self.assertContains(response, 'aria-current="page"')

    def test_unpublished_books_are_not_accessible(self):
        book = Book.objects.get(slug="barcelona-e-eu")
        book.is_published = False
        book.save()

        response = self.client.get(
            reverse("book-detail", kwargs={"slug": book.slug})
        )

        self.assertEqual(response.status_code, 404)


class StorefrontTests(TestCase):
    def test_homepage_displays_the_catalog_and_author(self):
        response = self.client.get(reverse("storefront"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "index.html")
        self.assertContains(response, "Marcia de Antonio")
        self.assertContains(response, "Barcelona e EU!")
        self.assertContains(response, "Antonio Dalama Lorenzo")
        self.assertContains(response, "PRÉVIA CONCEITUAL")
        self.assertContains(response, "images/lertrix-logo.", count=1)
        self.assertContains(response, ">Início</a>")
        self.assertContains(response, ">Catálogo</a>")
        self.assertContains(response, ">Sobre a Editora</a>")
        self.assertContains(response, ">Contato</a>")
        self.assertNotContains(response, ">Tecnologia</a>")
        for page in ("inicio", "catalogo", "sobre", "contato"):
            self.assertContains(response, f'data-page-panel="{page}"')
        self.assertContains(response, "js/page-tabs.")
        self.assertContains(response, 'class="page-curtain"')
        self.assertContains(response, "A essência da palavra.")
        self.assertContains(response, "contato@lertrixedicoes.com.br")
        self.assertContains(response, "R$ 63,00")
        self.assertContains(response, "Preço a confirmar")
        self.assertEqual(self.client.get("/tecnologia/").status_code, 404)


class AdminBrandingTests(TestCase):
    def test_admin_login_displays_lertrix_logo(self):
        response = self.client.get(reverse("admin:login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Lertrix Edições")
        self.assertContains(response, "images/lertrix-logo.")


class OwnerDashboardTests(TestCase):
    def test_dashboard_requires_staff_login(self):
        response = self.client.get(reverse("admin:index"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("admin:login"), response.url)

    def test_dashboard_shows_catalog_summary_and_management_links(self):
        Book.objects.create(
            title="Livro publicado de teste",
            slug="livro-publicado-de-teste",
            author="Autor de teste",
            is_published=True,
        )
        Book.objects.create(
            title="Livro em preparação",
            slug="livro-em-preparacao",
            author="Autor de teste",
        )
        owner = get_user_model().objects.create_superuser(
            username="owner",
            email="owner@example.com",
            password="test-password",
        )
        self.client.force_login(owner)

        response = self.client.get(reverse("admin:index"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin/index.html")
        self.assertEqual(response.context["total_books"], Book.objects.count())
        self.assertEqual(
            response.context["published_books"],
            Book.objects.filter(is_published=True).count(),
        )
        self.assertEqual(
            response.context["draft_books"],
            Book.objects.filter(is_published=False).count(),
        )
        self.assertContains(response, "Livros cadastrados")
        self.assertContains(response, reverse("admin:core_book_add"))
        self.assertContains(response, reverse("admin:core_book_changelist"))
        self.assertContains(response, reverse("storefront"))


class ApiTests(TestCase):
    def test_books_api_lists_published_books(self):
        data = self.client.get(reverse("api-books")).json()
        self.assertTrue(data["results"])
        self.assertTrue(all("slug" in b for b in data["results"]))

    def test_book_api_404_for_unknown(self):
        response = self.client.get(reverse("api-book-detail", args=["nao-existe"]))
        self.assertEqual(response.status_code, 404)


class ContactTests(TestCase):
    def test_contact_saves_and_sends_email(self):
        from django.core import mail

        from .models import ContactMessage

        response = self.client.post(
            reverse("contact"),
            {"name": "Ana", "email": "ana@example.com", "subject": "Oi", "message": "Olá"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ContactMessage.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_honeypot_blocks_bots(self):
        from .models import ContactMessage

        response = self.client.post(
            reverse("contact"),
            {"name": "Bot", "email": "b@example.com", "message": "x", "website": "spam"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ContactMessage.objects.count(), 0)


class CartAndOrderTests(TestCase):
    slug = "marcia-de-antonio-memorias-de-uma-historia-de-amor"

    checkout_data = {
        "customer_name": "Ana",
        "customer_email": "ana@example.com",
        "postal_code": "01001-000",
        "address": "Praça da Sé",
        "address_number": "1",
        "district": "Sé",
        "city": "São Paulo",
        "state": "sp",
    }

    def test_full_purchase_flow(self):
        from .models import Order

        self.client.post(reverse("cart-add", args=[self.slug]))
        self.client.post(reverse("cart-add", args=[self.slug]))
        self.assertContains(self.client.get(reverse("cart")), "R$ 126,00")

        response = self.client.post(reverse("checkout"), self.checkout_data)
        self.assertRedirects(response, reverse("order-done"))
        order = Order.objects.get()
        self.assertEqual(order.items.get().quantity, 2)
        self.assertEqual(order.total, 126 + order.shipping_cost)
        self.assertEqual(order.state, "SP")
        self.assertEqual(order.items.get().quantity, 2)
        self.assertContains(self.client.get(reverse("order-done")), f"#{order.pk}")
        self.assertRedirects(self.client.get(reverse("checkout")), reverse("cart"))

    def test_empty_cart_checkout_redirects(self):
        self.assertRedirects(self.client.get(reverse("checkout")), reverse("cart"))


class CanonicalHostTests(TestCase):
    def test_redirects_apex_to_www(self):
        with self.settings(CANONICAL_HOST="www.lertrix.com", ALLOWED_HOSTS=["*"]):
            response = self.client.get("/livros/x/", HTTP_HOST="lertrix.com")
            self.assertEqual(response.status_code, 301)
            self.assertEqual(response["Location"], "http://www.lertrix.com/livros/x/")


class WhatsAppTests(TestCase):
    def test_button_uses_configured_number(self):
        with self.settings(WHATSAPP_NUMBER="5511999998888"):
            response = self.client.get(reverse("storefront"))
        self.assertContains(response, "https://wa.me/5511999998888?text=")

    def test_button_hidden_without_number(self):
        with self.settings(WHATSAPP_NUMBER=""):
            response = self.client.get(reverse("storefront"))
        self.assertNotContains(response, "wa.me")


class PixTests(TestCase):
    def test_payload_matches_known_crc(self):
        from .pix import _crc16, build_pix_payload

        self.assertEqual(_crc16("123456789"), "29B1")
        code = build_pix_payload(
            "51835078000248", "Rotatek Tecnologia de Impressao Ltda", "Barueri", 63, "LERTRIX7"
        )
        self.assertTrue(code.startswith("000201"))
        self.assertIn("br.gov.bcb.pix0114" + "51835078000248", code)
        self.assertIn("540563.00", code)
        self.assertIn("5925ROTATEK TECNOLOGIA DE IMP", code)
        self.assertIn("6007BARUERI", code)
        self.assertEqual(code[-4:], _crc16(code[:-4]))

    def test_order_page_shows_pix(self):
        client = self.client
        slug = "marcia-de-antonio-memorias-de-uma-historia-de-amor"
        client.post(reverse("cart-add", args=[slug]))
        client.post(reverse("checkout"), CartAndOrderTests.checkout_data)
        response = client.get(reverse("order-done"))
        self.assertContains(response, "000201")
        self.assertContains(response, "<svg")
        self.assertContains(response, "Total com frete")


class ShippingTests(TestCase):
    slug = "marcia-de-antonio-memorias-de-uma-historia-de-amor"

    def test_cep_to_state(self):
        from .shipping import cep_to_state

        self.assertEqual(cep_to_state("06455-010"), "SP")
        self.assertEqual(cep_to_state("20040-020"), "RJ")
        self.assertEqual(cep_to_state("69010-000"), "AM")
        self.assertEqual(cep_to_state("123"), "")

    def test_no_free_shipping_by_default(self):
        self.client.post(reverse("cart-add", args=[self.slug]))
        self.client.post(reverse("shipping-calc"), {"cep": "40010-000"})
        response = self.client.get(reverse("cart"))
        self.assertContains(response, "Nordeste")
        self.assertNotContains(response, "grátis")

    def test_free_shipping_when_minimum_configured(self):
        from decimal import Decimal

        self.client.post(reverse("cart-add", args=[self.slug]))
        self.client.post(reverse("shipping-calc"), {"cep": "40010-000"})
        with self.settings(FREE_SHIPPING_MIN=Decimal("62")):
            self.assertContains(self.client.get(reverse("cart")), "grátis")

    def test_paid_shipping_below_minimum(self):
        from decimal import Decimal

        self.client.post(reverse("cart-add", args=[self.slug]))
        self.client.post(reverse("shipping-calc"), {"cep": "40010-000"})
        response = self.client.get(reverse("cart"))
        self.assertContains(response, "Nordeste")
        self.assertNotContains(response, "grátis")

    def test_order_total_includes_shipping(self):
        from decimal import Decimal

        from .models import Order

        self.client.post(reverse("cart-add", args=[self.slug]))
        data = {**CartAndOrderTests.checkout_data, "postal_code": "40010-000", "state": "BA"}
        self.client.post(reverse("checkout"), data)
        order = Order.objects.get()
        self.assertEqual(order.total, order.shipping_cost + 63)
        self.assertGreater(order.shipping_cost, 0)

    def test_invalid_cep_means_arranged_shipping(self):
        from .models import Order

        self.client.post(reverse("cart-add", args=[self.slug]))
        data = {**CartAndOrderTests.checkout_data, "postal_code": "000"}
        self.client.post(reverse("checkout"), data)
        order = Order.objects.get()
        self.assertIsNone(order.shipping_cost)
        self.assertEqual(order.total, 63)
