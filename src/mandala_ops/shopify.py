from __future__ import annotations

import json
from typing import Any

import requests

from .config import Settings


class ShopifyClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        if not settings.shopify_graphql_url or not settings.shopify_admin_access_token:
            raise ValueError("Missing Shopify settings. Check .env variables.")

    def graphql(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        response = requests.post(
            self.settings.shopify_graphql_url,
            headers={
                "Content-Type": "application/json",
                "X-Shopify-Access-Token": self.settings.shopify_admin_access_token,
            },
            data=json.dumps({"query": query, "variables": variables or {}}),
            timeout=45,
        )
        response.raise_for_status()
        payload = response.json()
        if "errors" in payload:
            raise RuntimeError(payload["errors"])
        return payload["data"]


PRODUCTS_QUERY = """
query ProductsForSeo($first: Int!, $after: String) {
  products(first: $first, after: $after, sortKey: UPDATED_AT, reverse: true) {
    edges {
      cursor
      node {
        id
        handle
        title
        descriptionHtml
        vendor
        productType
        tags
        status
        seo { title description }
        featuredMedia {
          ... on MediaImage {
            image { url altText }
          }
        }
        variants(first: 10) {
          edges {
            node { id sku price }
          }
        }
      }
    }
    pageInfo { hasNextPage endCursor }
  }
}
"""


def fetch_products_for_seo(client: ShopifyClient, limit: int = 50) -> list[dict[str, Any]]:
    products: list[dict[str, Any]] = []
    after = None
    while len(products) < limit:
        data = client.graphql(PRODUCTS_QUERY, {"first": min(50, limit - len(products)), "after": after})
        connection = data["products"]
        for edge in connection["edges"]:
            products.append(edge["node"])
        if not connection["pageInfo"]["hasNextPage"]:
            break
        after = connection["pageInfo"]["endCursor"]
    return products
