import re
import shutil
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.test import Client, override_settings

from core.models import Book

CSRF_INPUT = re.compile(r"\s*<input[^>]*name=[\"']csrfmiddlewaretoken[\"'][^>]*>")
CONTACT_FORM_ACTION = re.compile(r'(<form[^>]*class="form-card"[^>]*action=")[^"]*(")')


class Command(BaseCommand):
    help = (
        "Gera a vitrine como site estático (HTML/CSS/JS/imagens) para hospedagem "
        "compartilhada, com carrinho, frete e pedidos desativados."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            default=str(Path(settings.BASE_DIR).parent / "dist" / "locaweb"),
            help="Pasta de saída (será recriada).",
        )

    def handle(self, *args, **options):
        out = Path(options["output"]).resolve()
        if out.exists():
            shutil.rmtree(out)
        out.mkdir(parents=True)

        overrides = {
            "STORE_ENABLED": False,
            "DEBUG": False,
            "ALLOWED_HOSTS": ["*"],
            "CANONICAL_HOST": "",
            "STATIC_ROOT": str(out / "static"),
            "STORAGES": {
                "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
                "staticfiles": {
                    "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
                },
            },
        }
        with override_settings(**overrides):
            call_command(
                "collectstatic",
                interactive=False,
                verbosity=0,
                ignore_patterns=["admin", "admin-brand.css"],
            )
            client = Client(HTTP_HOST="localhost", secure=True)
            pages = {"index.html": "/"}
            for book in Book.objects.filter(is_published=True):
                pages[f"livros/{book.slug}/index.html"] = f"/livros/{book.slug}/"
            for target, url in pages.items():
                response = client.get(url)
                if response.status_code != 200:
                    raise CommandError(f"{url} respondeu {response.status_code}")
                html = response.content.decode()
                html = CSRF_INPUT.sub("", html)
                html = CONTACT_FORM_ACTION.sub(r"\1/contato.php\2", html)
                path = out / target
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(html, encoding="utf-8")

        media = Path(settings.MEDIA_ROOT)
        if (media / "books").is_dir():
            shutil.copytree(media / "books", out / "media" / "books")

        site = Path(settings.BASE_DIR).parent / "infra" / "locaweb-static"
        for item in site.iterdir():
            shutil.copy2(item, out / item.name)
        self.stdout.write(self.style.SUCCESS(f"Site estático gerado em {out}"))
