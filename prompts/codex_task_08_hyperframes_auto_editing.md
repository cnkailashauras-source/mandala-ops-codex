# Codex Task 08: Codex + HyperFrames Auto Editing

Mandala Jewels 的自动剪辑主流程应该使用 Codex + HyperFrames。

## 推荐分工

1. GPT Image 2：生成商品图、佩戴图、封面图
2. Kling 可灵：把图片生成 3-5 秒视频片段
3. Codex + HyperFrames：根据素材和剪辑提示词生成视频工程
4. 剪映 / CapCut：导出 MP4 后人工微调

## 当前工作台

启动：

```powershell
$env:PYTHONPATH="src"
python -m mandala_ops.cli hyperframes-studio
```

打开：

```text
http://127.0.0.1:8792/
```

## 输出

每次生成一个工程目录：

```text
output/hyperframes_projects/<project_id>/
```

目录内包含：

- `assets/`
- `comp.html`
- `index.html`
- `package.json`
- `hyperframes_job.json`
- `README.md`

## 预览与导出

```powershell
npx hyperframes preview comp.html
npx hyperframes render comp.html --output output.mp4
```

## 注意

- 当前不自动调用 GPT Image 2 或 Kling API
- 当前不自动控制剪映
- HyperFrames 是主自动剪辑引擎
- 剪映只作为最后人工精修工具
