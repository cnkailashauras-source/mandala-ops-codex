# Mandala Ops Codex Starter

这是给 **Mandala Jewels / mandalajewelshop.com** 准备的 Codex 自动化电商运营工具初版骨架。

目标不是让 Codex 去点 Shopify 后台按钮，而是让 Codex 在一个 GitHub 仓库里持续开发、测试和维护一套运营自动化系统，逐步接入 Shopify Admin API、Matrixify 产品 CSV、Google Search Console、Google Merchant Center、GA4、Pinterest / TikTok / Instagram 内容分发，以及 SEO / GEO 内容生成与复盘。

## 当前 MVP

当前版本先实现不依赖第三方授权的本地流程：

1. 读取产品 CSV
2. 根据 Mandala Jewels 的定位生成英文 SEO 标题、Meta Description、Product Type、Tags、图片 Alt Text 建议、Google Merchant 风险提示、是否建议上架
3. 生成集合规划和内容选题
4. 给 Codex 明确下一步开发任务

## 本地运行

```bash
cd mandala_ops_codex_starter
PYTHONPATH=src python -m mandala_ops.cli audit data/sample_products.csv --out output/seo_audit.csv
PYTHONPATH=src python -m mandala_ops.cli content-plan --out output/content_plan.csv
PYTHONPATH=src python -m unittest discover -s tests
```

## 接入真实 Shopify 之前

不要把 API token 发到聊天里。复制 `.env.example` 为 `.env`，然后在本地或 Codex 环境变量里填入密钥。

```bash
cp .env.example .env
```

## 建议的 Codex 第一条任务

```text
请阅读 AGENTS.md 和 prompts/codex_task_01_product_seo_pipeline.md，
完成产品 SEO 清洗流水线，并保证 python -m unittest discover -s tests 通过。
```

第一阶段不要让 Codex 直接改 Shopify 线上数据，只允许输出 CSV。等 CSV 审核没问题后，再做 Shopify API 回写。
