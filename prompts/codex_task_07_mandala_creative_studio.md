# Codex Task 07: Mandala Creative Studio

Mandala Creative Studio 是 Mandala Jewels 的本地社媒 AI 内容生产工作台。

## 当前定位

这不是 Shopify 商品优化面板。Shopify 商品管理可以由人工或 GPT 连接后台完成。

这个工作台只做社媒内容生产准备：

1. 从第一批商业商品中读取可用于内容生产的商品
2. 生成 TikTok / Reels / Pinterest / YouTube Shorts / Instagram 内容日历
3. 生成 GPT Image 生图任务表
4. 生成 Kling 生视频任务表
5. 生成剪映 / HyperFrames 自动剪辑任务表
6. 生成素材审核表
7. 支持按单个商品导出独立素材包

## 安全边界

- 不连接 Shopify API
- 不修改线上商品
- 不自动发布社媒内容
- 不自动联系达人
- 不自动调用 GPT Image、Kling、剪映或 HyperFrames
- 不写 healing、cure、guaranteed protection、bring wealth、make money
- 非洲翠统一使用 African Green Quartzite / Green Quartzite Jewelry，不写 Jade 或 jadeite jade

## 使用方式

```powershell
cd C:\Users\Administrator\Documents\Codex\2026-05-29\files-mentioned-by-the-user-mandala\mandala-ops-codex-repo
$env:PYTHONPATH="src"
python -m mandala_ops.cli creative-studio
```

打开：

```text
http://127.0.0.1:8790/
```

## 主要输出

- `output/active_exposure_calendar.csv`
- `output/pinterest_pin_plan.csv`
- `output/short_video_script_plan.csv`
- `output/ai_image_generation_jobs.csv`
- `output/ai_video_generation_jobs.csv`
- `output/auto_edit_plan.csv`
- `output/creative_asset_review_tracker.csv`
- `output/creative_studio/*_gpt_image_jobs.csv`
- `output/creative_studio/*_kling_video_jobs.csv`
- `output/creative_studio/*_capcut_hyperframes_edit_plan.csv`
- `output/creative_studio/*_asset_review_tracker.csv`
- `output/creative_studio/*_creative_brief.md`
