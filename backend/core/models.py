from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify


class Book(models.Model):
    title = models.CharField("título", max_length=200)
    slug = models.SlugField("identificador na URL", max_length=220, unique=True)
    author = models.CharField("autor", max_length=160)
    description = models.TextField("descrição", blank=True)
    author_bio = models.TextField("sobre o autor", blank=True)
    cover = models.ImageField(
        "capa",
        upload_to="books/covers/",
        blank=True,
        help_text="Envie a capa oficial do livro. O campo é opcional.",
    )
    price = models.DecimalField(
        "preço (R$)",
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
    )
    publisher = models.CharField("editora", max_length=160, blank=True)
    publication_date = models.DateField("data de publicação", blank=True, null=True)
    edition = models.CharField("edição", max_length=40, blank=True)
    language = models.CharField("idioma", max_length=60, blank=True)
    book_format = models.CharField("formato", max_length=80, blank=True)
    page_count = models.PositiveSmallIntegerField(
        "número de páginas", blank=True, null=True
    )
    isbn_10 = models.CharField("ISBN-10", max_length=10, blank=True)
    isbn_13 = models.CharField("ISBN-13", max_length=13, blank=True)
    weight_grams = models.PositiveIntegerField("peso (g)", blank=True, null=True)
    dimensions = models.CharField("dimensões", max_length=80, blank=True)
    minimum_reading_age = models.PositiveSmallIntegerField(
        "idade mínima de leitura", blank=True, null=True
    )
    is_published = models.BooleanField("visível na loja", default=False)
    display_order = models.PositiveSmallIntegerField("ordem na vitrine", default=0)
    created_at = models.DateTimeField("cadastrado em", auto_now_add=True)
    updated_at = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        ordering = ("display_order", "title")
        verbose_name = "livro"
        verbose_name_plural = "livros"

    def __str__(self):
        return self.title

    @property
    def cover_style(self):
        if self.slug.startswith("marcia-de-antonio"):
            return "marcia"
        if self.slug.startswith("barcelona-e-eu"):
            return "barcelona"
        return "default"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
