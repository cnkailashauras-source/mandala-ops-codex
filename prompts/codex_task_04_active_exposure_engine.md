# Codex Task 04 — Active Exposure Engine

## Goal

Build a local, review-first active exposure system for Mandala Jewels commercial jewelry products.

This workflow starts after the first `commercial_jewelry` SEO/GEO batch. It should not keep optimizing only for passive search discovery. It should generate organic distribution plans and creator outreach templates for manual review.

## Scope

Use `output/first_batch_commercial_seo_audit.csv` or `output/matrixify_commercial_update_template.csv` as input.

Only include products where:
- `Priority` is `High` or `Medium`
- `Focus Category` is not `Excluded Religious Item`

Skip products where:
- `Priority` is `Skip`
- the product is religious/cultural-first

## Organic Content Distribution Engine

Generate:
- `output/active_exposure_calendar.csv`
- `output/pinterest_pin_plan.csv`
- `output/short_video_script_plan.csv`

For each eligible product, create:
- 3 TikTok/Reels short video ideas
- 3 YouTube Shorts scripts
- 5 Pinterest Pin titles/descriptions
- 2 Instagram captions
- hashtags
- UTM URL
- product landing page handle
- content angle

Safe content angles:
- everyday jewelry
- stackable bracelet
- gift for her
- purple bracelet
- green stone jewelry
- minimalist styling
- outfit detail
- natural stone accessory

Never use:
- healing
- cure
- guaranteed protection
- bring wealth
- make money
- Jade or jadeite claims for African Green Quartzite

## Creator Outreach / UGC Seeding Engine

Generate:
- `data/creator_seed_list_template.csv`
- `output/creator_outreach_tracker.csv`
- `output/creator_dm_templates.csv`
- `output/creator_dm_templates.md`

Do not scrape creators. Do not auto-send messages. Produce reviewable templates only.

Every DM template must include:
- gifted by Mandala Jewels
- affiliate link or commission if applicable
- #ad when required

Never promise fixed earnings. Never ask for false positive reviews.

## Commands

```bash
PYTHONPATH=src python -m mandala_ops.cli exposure-plan --input output/first_batch_commercial_seo_audit.csv --days 30 --out output/active_exposure_calendar.csv
PYTHONPATH=src python -m mandala_ops.cli creator-outreach --out output/creator_outreach_tracker.csv
PYTHONPATH=src python -m unittest discover -s tests
```
