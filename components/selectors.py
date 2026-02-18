"""Shared selector helpers — client/product maps, safe_index, DataFrame column mapping.

Eliminates duplicated dict comprehensions and .map() lambdas across pages.
"""

from constants import STATUS_CODES
from services import annual_plan as ap_svc
from services import crm as crm_svc


def get_client_map() -> dict[int, str]:
    """Return {client_id: company_name} from cached CRM data."""
    return {c["client_id"]: c["company_name"] for c in crm_svc.get_all()}


def get_product_map() -> dict[int, str]:
    """Return {product_id: product_name} from cached annual plan data."""
    return {p["product_id"]: p["product_name"] for p in ap_svc.get_all()}


def safe_index(options: list, value, default: int = 0) -> int:
    """Return list.index(value) or *default* if not found."""
    try:
        return options.index(value)
    except ValueError:
        return default


def map_id_columns(df, *, client_map: dict | None = None, product_map: dict | None = None):
    """Mutate *df* in-place: map status_code, client_id, product_id to display strings."""
    if "status_code" in df.columns:
        df["status_code"] = df["status_code"].map(lambda x: f"{x} {STATUS_CODES.get(x, '')}")
    if client_map is not None and "client_id" in df.columns:
        df["client_id"] = df["client_id"].map(lambda x: client_map.get(x, x or "—"))
    if product_map is not None and "product_id" in df.columns:
        df["product_id"] = df["product_id"].map(lambda x: product_map.get(x, x or "—"))
