from django.conf import settings
from django.http import HttpResponsePermanentRedirect


class CanonicalHostMiddleware:
    """Redireciona lertrix.com (e outros hosts) para o host canônico, ex.: www.lertrix.com."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        canonical = settings.CANONICAL_HOST
        if (
            canonical
            and request.path != "/api/health/"
            and request.get_host().split(":")[0] != canonical
        ):
            scheme = "https" if request.is_secure() else "http"
            return HttpResponsePermanentRedirect(
                f"{scheme}://{canonical}{request.get_full_path()}"
            )
        return self.get_response(request)
