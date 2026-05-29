# Codex Task 02 — Shopify API 只读导出

## 目标

接入 Shopify Admin GraphQL API，但第一阶段只允许读取，不允许写入线上数据。

## 必须实现

1. 从 `.env` 读取 SHOPIFY_SHOP_DOMAIN、SHOPIFY_ADMIN_API_VERSION、SHOPIFY_ADMIN_ACCESS_TOKEN。
2. 增加命令：

```bash
PYTHONPATH=src python -m mandala_ops.cli shopify-export --limit 100 --out output/shopify_products.csv
```

3. 导出字段必须兼容现有 audit 命令。
4. 默认 dry-run。
5. 如果 token 缺失，给出清晰错误提示。
6. 增加测试或 mock，避免测试依赖真实 Shopify。

## 禁止

- 禁止直接更新线上产品。
- 禁止把 token 写进代码或日志。
