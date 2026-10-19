from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from .models import Book


def storefront(request):
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
            "current_page": "book",
        },
    )


def health_check(request):
    return JsonResponse({"status": "ok"})
