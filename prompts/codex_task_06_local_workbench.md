# Codex Task 06: Local Operations Workbench

Mandala Jewels 的自动化工作流需要一个非技术操作入口，方便店主在浏览器里运行本地 CSV 流程。

## 目标

创建一个本地工作台，集中运行以下流程：

1. 第一批 commercial_jewelry SEO 审核
2. Matrixify 可审核更新模板
3. TikTok / Instagram / Pinterest / YouTube Shorts 主动曝光计划
4. 达人触达与 UGC 寄样管理表
5. AI 生图、AI 生视频、自动剪辑和素材审核任务表

## 安全边界

- 不连接 Shopify API
- 不修改线上商品
- 不自动发布内容
- 不自动联系达人
- 不调用外部 AI 生图或生视频 API
- 只读取和写入本地 CSV / Markdown 文件

## 使用方式

```powershell
cd C:\Users\Administrator\Documents\Codex\2026-05-29\files-mentioned-by-the-user-mandala\mandala-ops-codex-repo
$env:PYTHONPATH="src"
python -m mandala_ops.cli workbench
```

打开后访问：

```text
http://127.0.0.1:8787/
```

## 交付物

- `src/mandala_ops/workbench.py`
- CLI 命令：`python -m mandala_ops.cli workbench`
- 本地网页工作台
- 输出文件状态查看
- CSV 下载入口
- 安全的本地 workflow allowlist
