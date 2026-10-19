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
