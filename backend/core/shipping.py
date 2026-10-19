"""Cálculo de frete por tabela própria: região (UF do CEP) × faixa de peso."""

import re
from decimal import Decimal

from django.conf import settings

from .models import ShippingRate

# Faixas de CEP por UF (cada UF pode ter mais de uma faixa).
CEP_RANGES = [
    (1000, 19999, "SP"), (20000, 28999, "RJ"), (29000, 29999, "ES"),
    (30000, 39999, "MG"), (40000, 48999, "BA"), (49000, 49999, "SE"),
    (50000, 56999, "PE"), (57000, 57999, "AL"), (58000, 58999, "PB"),
    (59000, 59999, "RN"), (60000, 63999, "CE"), (64000, 64999, "PI"),
    (65000, 65999, "MA"), (66000, 68899, "PA"), (68900, 68999, "AP"),
    (69000, 69299, "AM"), (69300, 69399, "RR"), (69400, 69899, "AM"),
    (69900, 69999, "AC"), (70000, 72799, "DF"), (72800, 72999, "GO"),
    (73000, 73699, "DF"), (73700, 76799, "GO"), (76800, 76999, "RO"),
    (77000, 77995, "TO"), (78000, 78899, "MT"), (78900, 78999, "RO"),
    (79000, 79999, "MS"), (80000, 87999, "PR"), (88000, 89999, "SC"),
    (90000, 99999, "RS"),
]


def normalize_cep(cep):
    digits = re.sub(r"\D", "", cep or "")
    return digits if len(digits) == 8 else ""


def cep_to_state(cep):
    digits = normalize_cep(cep)
    if not digits:
        return ""
    prefix = int(digits[:5])
    for start, end, state in CEP_RANGES:
        if start <= prefix <= end:
            return state
    return ""


def cart_weight(lines):
    return sum(
        (line["book"].weight_grams or settings.DEFAULT_BOOK_WEIGHT_GRAMS)
        * line["quantity"]
        for line in lines
    )


def quote(cep, lines, subtotal):
    """Retorna {"price", "days", "region", "free", "state"} ou None (frete a combinar)."""
    state = cep_to_state(cep)
    if not state:
        return None
    weight = cart_weight(lines)
    rate = next(
        (
            r
            for r in ShippingRate.objects.filter(
                is_active=True, max_weight_grams__gte=weight
            ).order_by("max_weight_grams", "price")
            if state in r.state_list
        ),
        None,
    )
    if rate is None:
        return None
    free = (
        settings.FREE_SHIPPING_MIN is not None and subtotal >= settings.FREE_SHIPPING_MIN
    )
    return {
        "price": Decimal("0") if free else rate.price,
        "days": rate.delivery_days,
        "region": rate.region,
        "free": free,
        "state": state,
    }
