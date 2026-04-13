import os
from typing import Any, Dict

import httpx
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

CPQ_BASE_URL = os.getenv("CPQ_BASE_URL", "").rstrip("/")
CPQ_USERNAME = os.getenv("CPQ_USERNAME", "")
CPQ_PASSWORD = os.getenv("CPQ_PASSWORD", "")
CPQ_TIMEOUT_SECONDS = float(os.getenv("CPQ_TIMEOUT_SECONDS", "30"))


class CPQClient:
    def __init__(self):
        if not CPQ_BASE_URL:
            raise ValueError("CPQ_BASE_URL is missing")
        if not CPQ_USERNAME or not CPQ_PASSWORD:
            raise ValueError("CPQ_USERNAME or CPQ_PASSWORD is missing")

        self.base_url = CPQ_BASE_URL
        self.auth = httpx.BasicAuth(CPQ_USERNAME, CPQ_PASSWORD)
        self.timeout = httpx.Timeout(CPQ_TIMEOUT_SECONDS)

    async def search_parts(
        self,
        part_number: str,
        limit: int = 1,
        offset: int = 0,
        pricebook: str = "_default_price_book",
    ) -> Dict[str, Any]:
        payload = {
            "criteria": {
                "q": f"{{partNumber:'{part_number}'}}",
                "limit": limit,
                "offset": offset,
                "totalResults": True,
            },
            "context": {
                "pricebookVarName": pricebook,
            },
        }

        async with httpx.AsyncClient(
            timeout=self.timeout,
            auth=self.auth,
            verify=False,
        ) as client:
            response = await client.post(
                f"{self.base_url}/rest/v19/parts/actions/search",
                headers={
                    "accept": "application/json",
                    "Content-Type": "application/json",
                },
                json=payload,
            )

        response.raise_for_status()
        return response.json()
    
    async def get_quote_summary(self, transaction_id: str) -> Dict[str, Any]:
        async with httpx.AsyncClient(
            timeout=self.timeout,
            auth=self.auth,
            verify=False,
        ) as client:
            response = await client.get(
                f"{self.base_url}/rest/v19/commerceDocumentsSalesEngineEMEACommerceProcessTransaction/{transaction_id}",
                params={
                    "excludeFieldTypes": "fileAttachment,readOnlyTextOrHtml"
                },
                headers={
                    "accept": "application/json",
                },
            )

        response.raise_for_status()
        return response.json()