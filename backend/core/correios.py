import base64
import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class CorreiosQuoteError(Exception):
    pass


def is_configured():
    return all(
        (
            settings.CORREIOS_USERNAME,
            settings.CORREIOS_ACCESS_CODE,
            settings.CORREIOS_POSTING_CARD,
            settings.CORREIOS_PACKAGE_LENGTH_CM,
            settings.CORREIOS_PACKAGE_WIDTH_CM,
            settings.CORREIOS_PACKAGE_HEIGHT_CM,
            settings.CORREIOS_PAC_CODE or settings.CORREIOS_SEDEX_CODE,
        )
    )


def _request_json(path, payload, authorization):
    url = urljoin(settings.CORREIOS_API_BASE_URL.rstrip("/") + "/", path.lstrip("/"))
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Accept": "application/json",
            "Authorization": authorization,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=settings.CORREIOS_API_TIMEOUT) as response:
            return json.load(response)
    except HTTPError as exc:
        raise CorreiosQuoteError(
            f"Correios API retornou HTTP {exc.code} para {path}."
        ) from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise CorreiosQuoteError(
            f"Não foi possível acessar a API dos Correios ({path})."
        ) from exc
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise CorreiosQuoteError(
            f"A API dos Correios retornou uma resposta inválida ({path})."
        ) from exc


def _as_api_items(payload):
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("produtos", "resultados", "itens", "resultado", "data"):
            value = payload.get(key)
            if isinstance(value, list):
                return value
        if all(key in payload for key in ("coProduto", "prazoEntrega")):
            return [payload]
        if "items" in payload and isinstance(payload["items"], list):
            return payload["items"]
    return []


def _token():
    cached = cache.get("correios_api_token")
    if cached:
        return cached

    credentials = f"{settings.CORREIOS_USERNAME}:{settings.CORREIOS_ACCESS_CODE}"
    basic_auth = base64.b64encode(credentials.encode("utf-8")).decode("ascii")
    response = _request_json(
        "token/v1/autentica/cartaopostagem",
        {"numero": settings.CORREIOS_POSTING_CARD},
        f"Basic {basic_auth}",
    )
    if not isinstance(response, dict):
        raise CorreiosQuoteError("A API dos Correios retornou um token inválido.")
    token = response.get("token")
    if not token:
        raise CorreiosQuoteError("A API dos Correios não retornou um token.")

    ttl = 23 * 60 * 60
    expires_at = response.get("expiraEm")
    if expires_at:
        try:
            expires = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            ttl = max(1, min(ttl, int((expires - datetime.now(timezone.utc)).total_seconds()) - 60))
        except (TypeError, ValueError):
            logger.warning("Validade do token Correios inválida; usando cache por 23 horas.")
    cache.set("correios_api_token", token, ttl)
    return token


def _decimal_price(value):
    try:
        return Decimal(str(value).replace(",", "."))
    except (InvalidOperation, ValueError):
        return None


def _package_weight(lines):
    return sum(
        (line["book"].weight_grams or settings.DEFAULT_BOOK_WEIGHT_GRAMS)
        * line["quantity"]
        for line in lines
    )


def _cache_key(cep, weight):
    payload = "|".join(
        str(value)
        for value in (
            settings.SHIPPING_ORIGIN_CEP,
            cep,
            weight,
            settings.CORREIOS_PAC_CODE,
            settings.CORREIOS_SEDEX_CODE,
            settings.CORREIOS_PACKAGE_LENGTH_CM,
            settings.CORREIOS_PACKAGE_WIDTH_CM,
            settings.CORREIOS_PACKAGE_HEIGHT_CM,
        )
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"correios_quote_{digest}"


def quotes(cep, lines):
    if not is_configured():
        return None

    weight = _package_weight(lines)
    cache_key = _cache_key(cep, weight)
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    products = [
        (code, name)
        for code, name in (
            (settings.CORREIOS_PAC_CODE, "PAC"),
            (settings.CORREIOS_SEDEX_CODE, "SEDEX"),
        )
        if code
    ]
    lot_id = uuid.uuid4().hex[:12]
    product_params = [
        {
            "coProduto": code,
            "nuRequisicao": code,
            "cepOrigem": "".join(filter(str.isdigit, settings.SHIPPING_ORIGIN_CEP)),
            "cepDestino": cep,
            "psObjeto": str(weight),
            "tpObjeto": "2",
            "comprimento": str(settings.CORREIOS_PACKAGE_LENGTH_CM),
            "largura": str(settings.CORREIOS_PACKAGE_WIDTH_CM),
            "altura": str(settings.CORREIOS_PACKAGE_HEIGHT_CM),
        }
        for code, _ in products
    ]
    token = _token()
    authorization = f"Bearer {token}"
    price_response = _request_json(
        "preco/v1/nacional",
        {"idLote": lot_id, "parametrosProduto": product_params},
        authorization,
    )
    deadline_response = _request_json(
        "prazo/v1/nacional",
        {
            "idLote": lot_id,
            "parametrosPrazo": [
                {
                    "coProduto": code,
                    "nuRequisicao": code,
                    "cepOrigem": "".join(filter(str.isdigit, settings.SHIPPING_ORIGIN_CEP)),
                    "cepDestino": cep,
                }
                for code, _ in products
            ],
        },
        authorization,
    )
    price_items = _as_api_items(price_response)
    deadline_items = _as_api_items(deadline_response)
    if not price_items or not deadline_items:
        raise CorreiosQuoteError("A API dos Correios retornou uma cotação inválida.")

    prices = {}
    for item in price_items:
        code = item.get("coProduto") or item.get("codigo")
        if not code or item.get("txErro"):
            continue
        value = item.get("pcFinal")
        if value is None:
            value = item.get("valor")
        price = _decimal_price(value)
        if price is not None:
            prices[code] = price

    deadlines = {}
    for item in deadline_items:
        code = item.get("coProduto") or item.get("codigo")
        if not code or item.get("txErro"):
            continue
        deadline = item.get("prazoMaximo")
        if deadline is None:
            deadline = item.get("prazoEntrega")
        if isinstance(deadline, (int, float)) and deadline > 0:
            deadlines[code] = int(deadline)
    results = [
        {
            "price": prices[code],
            "days": deadlines[code],
            "service": name,
            "service_code": code,
        }
        for code, name in products
        if prices.get(code) is not None
        and prices[code] >= 0
        and isinstance(deadlines.get(code), int)
        and deadlines[code] > 0
    ]
    if not results:
        raise CorreiosQuoteError(
            "Os Correios não retornaram preço e prazo para os serviços configurados."
        )

    cache.set(cache_key, results, 5 * 60)
    return results
