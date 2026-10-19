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


class ContactMessage(models.Model):
    name = models.CharField("nome", max_length=120)
    email = models.EmailField("e-mail")
    subject = models.CharField("assunto", max_length=160, blank=True)
    message = models.TextField("mensagem", max_length=4000)
    is_answered = models.BooleanField("respondida", default=False)
    created_at = models.DateTimeField("recebida em", auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "mensagem de contato"
        verbose_name_plural = "mensagens de contato"

    def __str__(self):
        return f"{self.name} — {self.subject or 'sem assunto'}"


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Aguardando contato"
        CONFIRMED = "confirmed", "Confirmado"
        SHIPPED = "shipped", "Enviado"
        DELIVERED = "delivered", "Entregue"
        CANCELLED = "cancelled", "Cancelado"

    customer_name = models.CharField("nome", max_length=160)
    customer_email = models.EmailField("e-mail")
    customer_phone = models.CharField("telefone", max_length=30, blank=True)
    postal_code = models.CharField("CEP", max_length=9)
    address = models.CharField("endereço", max_length=200)
    address_number = models.CharField("número", max_length=20)
    address_complement = models.CharField("complemento", max_length=80, blank=True)
    district = models.CharField("bairro", max_length=80)
    city = models.CharField("cidade", max_length=80)
    state = models.CharField("UF", max_length=2)
    notes = models.TextField("observações", blank=True, max_length=1000)
    status = models.CharField(
        "situação", max_length=12, choices=Status.choices, default=Status.PENDING
    )
    shipping_cost = models.DecimalField(
        "frete (R$)", max_digits=8, decimal_places=2, blank=True, null=True,
        help_text="Vazio = frete a combinar.",
    )
    shipping_days = models.PositiveSmallIntegerField("prazo (dias úteis)", blank=True, null=True)
    total = models.DecimalField(
        "total (R$)", max_digits=10, decimal_places=2, default=0,
        help_text="Produtos + frete (quando calculado).",
    )
    created_at = models.DateTimeField("criado em", auto_now_add=True)
    updated_at = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "pedido"
        verbose_name_plural = "pedidos"

    def __str__(self):
        return f"Pedido #{self.pk} — {self.customer_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    book = models.ForeignKey(
        Book, null=True, on_delete=models.SET_NULL, verbose_name="livro"
    )
    title = models.CharField("título", max_length=200)
    unit_price = models.DecimalField("preço unitário (R$)", max_digits=8, decimal_places=2)
    quantity = models.PositiveSmallIntegerField("quantidade", default=1)

    class Meta:
        verbose_name = "item do pedido"
        verbose_name_plural = "itens do pedido"

    @property
    def subtotal(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f"{self.quantity}× {self.title}"


class ShippingRate(models.Model):
    region = models.CharField("região", max_length=60)
    states = models.CharField(
        "UFs atendidas",
        max_length=120,
        help_text="Siglas separadas por vírgula, ex.: SP,RJ,MG",
    )
    max_weight_grams = models.PositiveIntegerField(
        "peso máximo (g)", help_text="A faixa vale para pedidos até este peso."
    )
    price = models.DecimalField("frete (R$)", max_digits=8, decimal_places=2)
    delivery_days = models.PositiveSmallIntegerField("prazo (dias úteis)", default=7)
    is_active = models.BooleanField("ativa", default=True)

    class Meta:
        ordering = ("region", "max_weight_grams")
        verbose_name = "tarifa de frete"
        verbose_name_plural = "tarifas de frete"

    @property
    def state_list(self):
        return [s.strip().upper() for s in self.states.split(",") if s.strip()]

    def __str__(self):
        return f"{self.region} até {self.max_weight_grams} g — R$ {self.price}"
