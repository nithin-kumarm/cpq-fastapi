from __future__ import annotations

from typing import Any, Dict, Optional


def _money(obj: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not isinstance(obj, dict):
        return None
    return {
        "value": obj.get("value"),
        "currency": obj.get("currency"),
    }


def summarize_parts_response(raw: Dict[str, Any]) -> Dict[str, Any]:
    result = raw.get("result", {})
    items = result.get("items", []) or []

    if not items:
        return {"count": 0, "items": []}

    item = items[0]
    return {
        "count": result.get("count", len(items)),
        "items": [
            {
                "partNumber": item.get("partNumber"),
                "partDisplayNumber": item.get("partDisplayNumber"),
                "description": item.get("description"),
                "status": (item.get("status") or {}).get("displayValue"),
                "eligibleToSell": item.get("eligibleToSell"),
                "directBuy": (item.get("directBuy") or {}).get("displayValue"),
                "listPrice": item.get("listPrice"),
                "leadTime": item.get("leadTime"),
            }
        ],
    }


def summarize_quote_response(raw: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "transactionId": raw.get("transactionID_t") or raw.get("bs_id"),
        "transactionNumber": raw.get("transactionNumber_c"),
        "quoteName": raw.get("transactionName_t"),
        "status": (raw.get("status_t") or {}).get("displayValue"),
        "stage": (raw.get("_stage") or {}).get("displayValue"),
        "quoteType": (raw.get("quoteType_c") or {}).get("displayValue"),
        "currency": (raw.get("currency_t") or {}).get("value"),
        "customer": raw.get("_customer_t_company_name"),
        "shipToCountry": (raw.get("_shipTo_t_country") or {}).get("displayValue"),
        "createdDate": raw.get("createdDate_t"),
        "lastUpdatedDate": raw.get("lastUpdatedDate_t"),
        "lineItemCount": raw.get("sFDCLineItemCount_c"),
        "totals": {
            "net": _money(raw.get("totalNet_t_c")),
            "list": _money(raw.get("totalList_t_c")),
            "discount": _money(raw.get("totalDiscount_t_c")),
            "vat": _money(raw.get("totalVAT_c")),
            "total": _money(raw.get("totalNetWithVAT_c")),
        },
        "owner": raw.get("owner_t"),
        "quoteLink": raw.get("quoteLink_c"),
    }