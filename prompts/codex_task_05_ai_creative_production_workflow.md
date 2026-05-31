# Codex Task 05 — AI Creative Production Workflow

## Goal

Turn the active exposure calendar into a local, review-first AI creative production workflow.

This workflow prepares generation jobs for:
- AI image prompts
- AI video prompts
- automatic editing plans
- asset review tracking

It must not call paid image/video APIs automatically. It must not publish content automatically. All generated assets must be reviewed by a human before use.

## Inputs

Use:

```bash
output/active_exposure_calendar.csv
```

## Outputs

Generate:

```bash
output/ai_image_generation_jobs.csv
output/ai_video_generation_jobs.csv
output/auto_edit_plan.csv
output/creative_asset_review_tracker.csv
```

## Creative Safety Rules

Do not use:
- healing
- cure
- guaranteed protection
- bring wealth
- make money
- Jade or jadeite wording for African Green Quartzite

Do use:
- everyday jewelry
- stackable bracelet
- gift for her
- purple bracelet
- green stone jewelry
- minimalist styling
- outfit detail
- natural stone accessory

## Production Notes

Use real product reference images when possible. AI-generated images and videos must preserve product color, shape, material impression, and scale. Any asset with inaccurate product appearance should be rejected before posting.

Recommended sequence:

1. Generate image jobs.
2. Review image prompts and product references.
3. Generate still images.
4. Generate image-to-video clips.
5. Auto-edit clips with captions and CTA.
6. Review final assets.
7. Move approved assets into the publish calendar.

## Command

```bash
PYTHONPATH=src python -m mandala_ops.cli creative-plan --input output/active_exposure_calendar.csv --image-out output/ai_image_generation_jobs.csv --video-out output/ai_video_generation_jobs.csv --edit-out output/auto_edit_plan.csv --review-out output/creative_asset_review_tracker.csv
```
