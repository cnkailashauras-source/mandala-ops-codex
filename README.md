# Mandala Ops Codex Starter

这是给 **Mandala Jewels / mandalajewelshop.com** 准备的 Codex 自动化电商运营工具初版骨架。

目标不是让 Codex 直接修改 Shopify 线上商品，而是在 GitHub 仓库里持续开发、测试和维护一套本地可审核的运营自动化系统。当前阶段只生成 CSV / Markdown 文件，人工审核后再决定是否通过 Matrixify 或其他工具回写 Shopify。

## 当前能力

1. 读取 Matrixify / Shopify Products CSV
2. 生成 commercial_jewelry 商品 SEO/GEO 审核表
3. 生成 Matrixify 可审核更新模板
4. 生成 TikTok、Instagram、Pinterest、YouTube Shorts 主动曝光内容表
5. 生成达人触达和 UGC 寄样管理表
6. 生成 AI 生图、AI 生视频、自动剪辑和素材审核任务表
7. 提供本地浏览器工作台，方便非技术操作

## 本地操作工作台

如果不想记命令，可以启动本地浏览器面板：

```powershell
cd C:\Users\Administrator\Documents\Codex\2026-05-29\files-mentioned-by-the-user-mandala\mandala-ops-codex-repo
$env:PYTHONPATH="src"
python -m mandala_ops.cli workbench
```

然后打开：

```text
http://127.0.0.1:8787/
```

这个工作台只运行本地 CSV 流程，不连接 Shopify API，不修改线上商品，不自动发布内容，不自动联系达人，也不调用外部 AI 生成接口。

## Mandala Creative Studio

如果当前重点是社媒内容生产，而不是 Shopify 商品内容优化，启动这个工作台：

```powershell
cd C:\Users\Administrator\Documents\Codex\2026-05-29\files-mentioned-by-the-user-mandala\mandala-ops-codex-repo
$env:PYTHONPATH="src"
python -m mandala_ops.cli creative-studio
```

然后打开：

```text
http://127.0.0.1:8790/
```

Creative Studio 会围绕商品生成 GPT Image 生图任务、Kling 生视频任务、剪映 / HyperFrames 剪辑任务和素材审核表。它当前只生成任务表和 prompt，不会自动调用外部平台。

## 常用命令

```powershell
$env:PYTHONPATH="src"
python -m mandala_ops.cli audit data/first_batch_commercial_products.csv --focus commercial_jewelry --out output/first_batch_commercial_seo_audit.csv
python -m mandala_ops.cli matrixify-template data/first_batch_commercial_products.csv --focus commercial_jewelry --out output/matrixify_commercial_update_template.csv
python -m mandala_ops.cli exposure-plan --input output/first_batch_commercial_seo_audit.csv --days 30 --out output/active_exposure_calendar.csv
python -m mandala_ops.cli creator-outreach --out output/creator_outreach_tracker.csv
python -m mandala_ops.cli creative-plan --input output/active_exposure_calendar.csv --image-out output/ai_image_generation_jobs.csv --video-out output/ai_video_generation_jobs.csv --edit-out output/auto_edit_plan.csv --review-out output/creative_asset_review_tracker.csv
python -m unittest discover -s tests
```

## 安全边界

- 不连接 Shopify 线上 API
- 不修改线上产品
- 不自动发布社媒内容
- 不自动给达人发私信
- 不写 healing、cure、guaranteed protection、bring wealth、make money 等高风险功效或收益承诺
- 非洲翠统一使用 African Green Quartzite / Green Quartzite Jewelry，不默认写 Jade

## 接入真实 Shopify 之前

不要把 API token 发到聊天里。等 CSV 审核确认后，再通过 Matrixify 手动导入，或在后续阶段设计带 dry-run 和人工确认的 Shopify API 流程。
