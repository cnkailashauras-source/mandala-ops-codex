from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    shopify_shop_domain: str = os.getenv("SHOPIFY_SHOP_DOMAIN", "")
    shopify_admin_api_version: str = os.getenv("SHOPIFY_ADMIN_API_VERSION", "2026-01")
    shopify_admin_access_token: str = os.getenv("SHOPIFY_ADMIN_ACCESS_TOKEN", "")
    dry_run: bool = os.getenv("DRY_RUN", "true").lower() != "false"

    @property
    def shopify_graphql_url(self) -> str:
        if not self.shopify_shop_domain:
            return ""
        return (
            f"https://{self.shopify_shop_domain}/admin/api/"
            f"{self.shopify_admin_api_version}/graphql.json"
        )


def get_settings() -> Settings:
    return Settings()
