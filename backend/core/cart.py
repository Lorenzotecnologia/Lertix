from decimal import Decimal

from .models import Book

SESSION_KEY = "cart"
MAX_QUANTITY = 20


class Cart:
    """Carrinho armazenado na sessão: {id_do_livro: quantidade}."""

    def __init__(self, request):
        self.session = request.session
        self.data = self.session.setdefault(SESSION_KEY, {})

    def _save(self):
        self.session.modified = True

    def add(self, book, quantity=1):
        key = str(book.pk)
        self.data[key] = min(self.data.get(key, 0) + quantity, MAX_QUANTITY)
        self._save()

    def set(self, book_id, quantity):
        key = str(book_id)
        if key not in self.data:
            return
        if quantity <= 0:
            del self.data[key]
        else:
            self.data[key] = min(quantity, MAX_QUANTITY)
        self._save()

    def remove(self, book_id):
        self.data.pop(str(book_id), None)
        self._save()

    def clear(self):
        self.session.pop(SESSION_KEY, None)
        self.session.modified = True

    def lines(self):
        books = Book.objects.filter(
            pk__in=self.data.keys(), is_published=True, price__isnull=False
        )
        return [
            {
                "book": book,
                "quantity": self.data[str(book.pk)],
                "subtotal": book.price * self.data[str(book.pk)],
            }
            for book in books
        ]

    def total(self):
        return sum((line["subtotal"] for line in self.lines()), Decimal("0"))

    def count(self):
        return sum(self.data.values())
