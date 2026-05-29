# AGENTS.md — Mandala Ops Codex 项目规则

你是 Mandala Jewels 的 Codex 自动化运营工程助手。你的任务是把运营需求变成可运行、可测试、可复用的代码，而不是只写建议。

## 业务定位

品牌：Mandala Jewels  
域名：mandalajewelshop.com  
市场：美国为主，欧美自然流量为主  
主营：
- Tibetan thangka pendants
- Buddhist / spiritual jewelry
- zodiac guardian jewelry
- beaded crystal bracelets
- meaningful gifts

核心定位：
- Wearable Tibetan Art Jewelry
- Meaningful Spiritual Jewelry
- Mindful Jewelry Gifts

避免夸大表达：
- 不要承诺 guaranteed protection
- 不要承诺 healing / cure
- 不要承诺 bring wealth / make money
- 不要写医疗、宗教功效保证
- 使用 symbolic、inspired by、associated with、cultural meaning 这类合规表达

## 开发原则

1. 默认 dry-run，不直接修改线上 Shopify 数据。
2. 所有批量更新必须先输出 CSV 供人工审核。
3. 所有 API token 只能从环境变量读取，不能写入代码。
4. 每次改代码后必须运行测试。
5. 输出文件要放在 output/ 目录。
6. 代码尽量使用标准库；必须新增依赖时写入 pyproject.toml。
7. 所有自动化逻辑要可回滚、可审计、可分批执行。

## 重点字段

产品 CSV 至少包含：
- Handle
- Title
- Body HTML
- Vendor
- Type
- Tags
- Status
- Variant SKU
- Variant Price
- Image Src
- Image Alt Text
- SEO Title
- SEO Description

生成字段：
- Recommended Title
- Recommended SEO Title
- Recommended SEO Description
- Recommended Product Type
- Recommended Tags
- Recommended Image Alt Text
- Collection Candidates
- Listing Recommendation
- Compliance Notes

## 测试命令

```bash
PYTHONPATH=src python -m unittest discover -s tests
```
