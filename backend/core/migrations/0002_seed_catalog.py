from datetime import date

from django.db import migrations


def seed_catalog(apps, schema_editor):
    Book = apps.get_model("core", "Book")
    database = schema_editor.connection.alias

    Book.objects.using(database).update_or_create(
        slug="marcia-de-antonio-memorias-de-uma-historia-de-amor",
        defaults={
            "title": "Marcia de Antonio: Memórias de uma história de Amor",
            "author": "Antonio Dalama Lorenzo",
            "description": (
                "Escrito por um marido apaixonado, este livro de memórias é uma "
                "homenagem a Marcia e à vida construída a dois. A narrativa "
                "acompanha a história de uma família de imigrantes da Galícia "
                "até o Brasil e revisita lembranças, documentos, fotografias e "
                "caminhos recuperados pelo autor ao longo de décadas.\n\n"
                "Da aldeia raiana onde a história começa às ruas do Brás, em "
                "São Paulo, o livro percorre a imigração, a travessia de navio "
                "em 1957, os costumes e curiosidades da região entre Espanha e "
                "Portugal, e o encontro de Antonio com Marcia. Uma história "
                "individual e familiar situada nas transformações sociais do "
                "século XX."
            ),
            "author_bio": (
                "Antonio Dalama Lorenzo nasceu em uma pequena aldeia da Galícia, "
                "na Espanha. Sua família migrou para o Brasil quando ele tinha "
                "cinco anos, no final da década de 1950, e foi aqui que conheceu "
                "o pai, que havia migrado antes. Estudou Economia e Letras e "
                "atua desde os dezesseis anos no setor gráfico. Empresário do "
                "setor de máquinas impressoras rotativas, também realizou o "
                "sonho de registrar em livro a história de amor com Marcia."
            ),
            "price": "63.00",
            "publisher": "Letrix Edições",
            "publication_date": date(2023, 11, 15),
            "edition": "2ª",
            "language": "Português",
            "book_format": "Capa comum",
            "page_count": 302,
            "isbn_10": "650062498X",
            "isbn_13": "9786500624984",
            "weight_grams": 445,
            "dimensions": "16 x 1,7 x 23 cm",
            "minimum_reading_age": 8,
            "is_published": True,
            "display_order": 1,
        },
    )

    Book.objects.using(database).update_or_create(
        slug="barcelona-e-eu",
        defaults={
            "title": "Barcelona e EU!",
            "author": "Antonio Dalama Lorenzo",
            "is_published": True,
            "display_order": 2,
        },
    )


def remove_seeded_catalog(apps, schema_editor):
    Book = apps.get_model("core", "Book")
    database = schema_editor.connection.alias
    Book.objects.using(database).filter(
        slug__in=(
            "marcia-de-antonio-memorias-de-uma-historia-de-amor",
            "barcelona-e-eu",
        )
    ).delete()


class Migration(migrations.Migration):
    dependencies = [("core", "0001_initial")]

    operations = [migrations.RunPython(seed_catalog, remove_seeded_catalog)]
