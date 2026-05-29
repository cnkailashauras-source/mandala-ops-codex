# Codex Task 01 — 产品 SEO 清洗流水线

请阅读 README.md 和 AGENTS.md，然后完成以下任务：

## 目标

把当前本地 CSV 清洗工具升级成可用于 Mandala Jewels 批量产品 SEO 的稳定流水线。

## 必须实现

1. 支持 Matrixify 导出的 Products CSV。
2. 输出可回写 Matrixify 的 CSV 模板。
3. 对每个产品生成英文标题、SEO Title、SEO Description、Product Type、Tags、Image Alt Text、Collection Candidates、Listing Recommendation、Compliance Notes。
4. 标记旧品牌词：KAILASH AURAS、冈仁波齐奥拉斯。
5. 标记风险表达：heal / cure / guaranteed / bring wealth / make money / 治病 / 保证 / 必定 / 暴富 / 发财。
6. 保证输出 CSV 可以被人工审核后再导入 Shopify。

## 验收

```bash
PYTHONPATH=src python -m mandala_ops.cli audit data/sample_products.csv --out output/seo_audit.csv
PYTHONPATH=src python -m unittest discover -s tests
```
