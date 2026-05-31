# 架构与职责边界

## 目标

这个 skill 的架构目标是让图片/PDF/图片版 PPTX 到可编辑 PPTX 的流程稳定、可复现、可审计、可局部返工。

核心原则：

- 主 agent 只做 orchestration。
- page subagent 只做一个页面的重建。
- `$imagegen` / GPT Image 2 是默认视觉生成层，负责 clean background、嵌入图片、艺术字和复杂视觉资产。
- native PPT text 只负责需要后续编辑的主文字；native shape 只负责简单 primitive。
- 确定性脚本负责目录、状态、记录、构建、验证和组装。
- 共享状态只能由明确 owner 和脚本推进。

## 角色分工

### 主 agent

主 agent 负责：

- 运行 `prepare_deck_run.py`。
- 读取 `page_job_status.py` 输出。
- 为每个 page spawn 一个 page subagent。
- 用 `record_page_dispatch.py` 记录 dispatch。
- 用 `record_page_result.py` 记录 page worker 返回结果。
- 运行 repair queue。
- 运行 `finalize_deck_run.py`。
- 向用户报告进度、最终路径、QA 结果和 blocker。

主 agent 不负责：

- 页面对象识别。
- 页面 manifest 编写。
- 页面 PPTX 构建。
- 页面 preview/contact sheet 生成。
- 页面内 `$imagegen` 决策。

### Page subagent

page subagent 负责一个 `pages/page_NNN/` 目录：

- 读取 `page_request.json` 和 `source.png`。
- 分析页面主文字、generated background、嵌入图片、艺术字、复杂视觉对象和简单结构。
- 写 `visual_layer_plan`。
- 使用 `$imagegen` 生成/编辑 clean background、picture assets、art text assets、visual assets 和 repair bitmap。
- 用脚本记录 imagegen 结果。
- 写 `manifest.json`。
- 构建 `page.pptx`。
- 生成 `preview.png` 和 `split_assets_contact.png`。
- 运行 page validation。
- 写 `page_result.json`。

page subagent 不能编辑 deck-level 文件或其他 page 目录。

### `$imagegen`

`$imagegen` 负责所有视觉生成和编辑：

- full-slide clean background。
- 嵌入图片、截图、图表视觉、UI、含字图片重建。
- 艺术字、手写字、复杂字体效果和贴纸字。
- 图标、pictogram、徽章、复杂箭头、装饰对象。
- foreground removal + background restoration。
- 稀疏 chroma-key asset sheet。
- targeted repair asset。
- transparent asset 的 chroma-key 源图。

本 skill 不直接调用 Image API，不绕过 `$imagegen`。

### 确定性脚本

脚本负责：

- 创建 run/page 结构。
- 推进关键状态。
- 复制和记录生成资产。
- 切分 asset sheet。
- 构建 PPTX。
- 验证 PPTX 和 manifest。
- 生成 QA artifacts。

脚本不负责：

- 手绘复杂视觉资产。
- 用本地代码替代 `$imagegen`。
- 用 SVG/native shape 伪造复杂视觉。
- 伪造完成状态。

## Run 目录

```text
output/image-to-editable-ppt/<job-id>/
├── input/
├── deck_manifest.json
├── page_jobs.json
├── notes_manifest.json
├── repair_queue.json
├── run_summary.json
├── final/
├── qa/
└── pages/
```

## Page 目录

```text
pages/page_001/
├── source.png
├── page_request.json
├── page_result.json
├── manifest.json
├── imagegen-jobs.json
├── prompts/
├── generated/
├── assets/
├── page.pptx
├── preview.png
├── split_assets_contact.png
└── validation.json
```

## Owner 原则

- `deck_manifest.json`：主 agent 和 deck-level 脚本。
- `page_jobs.json`：`prepare_deck_run.py`、`record_page_dispatch.py`、`record_page_result.py`、`queue_page_repairs.py`、`finalize_deck_run.py`。
- `notes_manifest.json`：`prepare_deck_run.py` 创建，`finalize_deck_run.py` 读取。
- `page_request.json`：`prepare_deck_run.py` 创建。
- `page_result.json`：page worker 创建，`record_page_result.py` 校验。
- `manifest.json`：page worker 创建。
- `imagegen-jobs.json`：page-local 脚本维护。

任何 agent 都不能手写关键状态来跳过脚本。
