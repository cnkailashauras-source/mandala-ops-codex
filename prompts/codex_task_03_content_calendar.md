# Codex Task 03 — GEO/SEO 内容日历生成器

## 目标

生成可发布到 Blog / Pinterest / TikTok / Instagram 的内容计划。

## 必须实现

1. 读取 data/keywords.csv 和 data/collections_plan.csv。
2. 生成 30 天内容日历：
   - Blog topic
   - Pinterest pin title
   - Pinterest description
   - TikTok hook
   - Instagram caption
   - Target product/collection
   - Primary keyword
3. 所有文案使用英文，语气适合欧美市场。
4. 不使用 guaranteed healing、bring wealth 等功效承诺。
5. 输出 CSV：

```bash
PYTHONPATH=src python -m mandala_ops.cli content-calendar --days 30 --out output/content_calendar.csv
```
