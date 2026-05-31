---
name: image-to-editable-ppt
description: 当用户提供一张或多张幻灯片图片、图片版 PPT/PPTX 或 PDF，并要求转成高保真可编辑 PowerPoint/PPTX、用图片生成重建视觉层、保留页面备注、重建主文字或做可编辑化复刻时使用。
---
# Image to Editable PPT

## Overview

这个 skill 用于把视觉型幻灯片输入重建成高保真、可继续编辑的 PowerPoint `.pptx`。

输入可以是一张图片、多张图片、PDF、图片版 PPT/PPTX。输出始终是 `.pptx`。默认策略是 **imagegen-first layered reconstruction**：先用 `$imagegen` / GPT Image 2 高保真生成页面视觉层，再把需要后续编辑的正文、标题、普通标签等主文字作为原生 PowerPoint text box 覆盖上去。

核心目标不是追求所有视觉对象都变成 PPT primitive，而是让最终页面视觉像原稿，同时让用户最常修改的主文字保持可编辑。复杂背景、嵌入图片、含字图片、图标、艺术字、图表视觉、装饰、纹理、插画和风格化对象默认都走图片生成或图片编辑。

## Hard Constraints

- 每一个来源页面都必须由 page subagent 重建，包括单张图片输入。
- 主 agent 不做页面重建，只做 orchestration。
- 不设计父 agent 单独执行、顺序降级执行或低保真降级模式。没有可用 page subagent 就停止，不进入页面重建。
- 所有视觉层生成、图片编辑、背景修复、嵌入图片重建、艺术字、透明 bitmap 资产和 asset sheet 都必须使用 `$imagegen`。如果能选择模型，使用 `gpt-image-2` 或当前可用的最高保真 GPT Image 模型。
- `$imagegen` 的默认路径是 built-in `image_gen`。不要在本 skill 里绕过 `$imagegen` 直接调用 Image API，除非 `$imagegen` 的规则明确要求 fallback。
- 如果页面需要 `$imagegen`，但 `$imagegen` 或 built-in `image_gen` 不可用，停止该页并报告 blocker，不用 SVG、Pillow、HTML/canvas 或 native shape 伪造复杂视觉。
- 原始整页 `source.png` 加可编辑文本覆盖是失败模式，不是 fallback。
- 允许一张 full-slide generated clean background 作为底层，但它必须是 imagegen 生成/编辑后的无主文字背景，并在 provenance 中记录为 imagegen clean background。
- 背景必须移除正文、标题、主要标签、数据数字等需要可编辑或会与覆盖文本重复的主文字；背景中作为纹理、装饰、品牌水印或不可编辑氛围的小字可以保留，但必须在 `visual_layer_plan.background_decorative_text_policy` 里说明。
- 页面中的图片、截图、图表视觉、含字图片和 UI 截图默认也用 imagegen/edit 高保真重建为独立 raster asset；不要用 source crop 作为默认策略。
- source-derived raster asset 只允许作为用户明确要求的例外，或者用于 imagegen 无法合规重建且不包含主文字的小型对象；例外必须记录原因。
- 艺术字、复杂字体效果、手写字、徽章字、发光字、贴纸字等默认是 imagegen 透明资产，不硬转普通 PPT text box。
- 禁止用 SVG 承担复杂视觉复刻。SVG 不能作为图标、插画、艺术字、纹理、复杂图表或装饰对象的 fallback。
- page worker 必须先写视觉分层计划，再生成视觉层，再写 manifest；不能先用审美猜测 SVG/shape 拼页面。
- 关键状态只能由脚本推进。agent 不能手写 JSON 把 page、imagegen job 或 run 标成完成。

## Visible Progress Plan

正常运行时，主 agent 必须保持一个用户可见 checklist，同一时间只有一个 active step：

1. 准备输入和任务目录。
2. 分派页面重建。
3. 生成页面视觉层和可编辑文字。
4. 检查并修复页面。
5. 组装和验证 PPTX。

完成条件：

- `准备输入和任务目录`：`deck_manifest.json`、`page_jobs.json`、`pages/page_NNN/source.png`、`notes_manifest.json` 已存在。
- `分派页面重建`：主 agent 按 `max_concurrent_pages` 分批 spawn page subagent；每个已 spawn page 都由 `record_page_dispatch.py` 记录为 dispatched。如果不能继续 spawn subagent，停在这里并报告 blocker。
- `生成页面视觉层和可编辑文字`：每个 page 都由 page worker 产出 `visual_layer_plan`、`manifest.json`、`page.pptx`、`preview.png`、`split_assets_contact.png`、`validation.json`、`page_result.json`。
- `检查并修复页面`：所有 page 通过 `record_page_result.py` 记录，repair queue 清空；无法修复时报告 blocker。
- `组装和验证 PPTX`：`final/<origin>_edited.pptx` 和 `final/validation.json` 已存在。

不要只因为聊天里说完成就标记步骤完成；必须有真实文件或脚本推进的状态。

## Default Workflow

1. 运行 `prepare_deck_run.py` 创建 run 目录、归一化输入、生成 deck/page manifest 和 page request。
2. 运行 `page_job_status.py` 查看待分派页面、active dispatches 和可用 dispatch slot。
3. 主 agent 按 `max_concurrent_pages` 分批 spawn 普通 Codex worker subagent；不要一次性 spawn 超过运行时并发上限。
4. spawn 后立即运行 `record_page_dispatch.py` 记录 dispatch。
5. 每个 page worker 只在自己的 page 目录内工作，完成分层计划、imagegen 视觉层、可编辑文字、page-level build、preview、contact sheet、validation。
6. page worker 返回后，主 agent 运行 `record_page_result.py` 检查文件、路径和 hash，并推进 page 状态。
7. 再次运行 `page_job_status.py`；如果还有 pending/repair_needed page，就继续下一批分派。
8. 如有页面问题，运行 `queue_page_repairs.py` 生成 repair item，再分批分派 repair worker。
9. 所有 page accepted 后，运行 `finalize_deck_run.py` 组装最终 PPTX、复制 notes、运行 deck validation 和 QA summary。

正常主入口是 `prepare_deck_run.py`。不再保留旧输入归一化脚本作为公开入口或兼容 wrapper。

## Generation Delegation

使用 `$imagegen` 前必须读取并遵守：

```text
${CODEX_HOME:-$HOME/.codex}/skills/.system/imagegen/SKILL.md
```

本 skill 只组合 `$imagegen`，不重新定义图片生成 API 规则。若 `$imagegen` 支持模型选择，页面 worker 应选择 `gpt-image-2` 或最高保真 GPT Image 模型；如果只能使用 built-in `image_gen`，就用 built-in 路径并在 `imagegen-jobs.json` 记录实际工具。

页面内需要 `$imagegen` 的常见场景：

- 生成 full-slide clean background：保留页面构图、颜色、空间、容器、图片区域和装饰氛围，移除主文字和会被覆盖的前景。
- 重建嵌入图片、截图、图表视觉、UI 截图、证书、医学/产品/人物图片等独立视觉资产。
- 生成艺术字、手写字、复杂字体效果、发光字、徽章字和贴纸字透明资产。
- 生成图标、pictogram、装饰符号、复杂箭头、手绘标记和风格化图形。
- targeted repair 某个 clean background、嵌入图片资产或艺术字资产。

项目实际使用的生成图片必须复制到 page 目录，并通过 page-local `imagegen-jobs.json` 记录。不要让 manifest 引用只存在于 `$CODEX_HOME/generated_images/...` 的图片。

## Subagent Dispatch

page subagent 是唯一的页面重建执行者。主 agent 不重建页面。

每个 page worker 必须收到自包含 prompt，至少包含：

- run dir、page id、page dir、source image 绝对路径。
- 允许写入范围：只能写当前 page dir。
- 禁止写入范围：deck manifest、notes manifest、final deck、其他 page。
- 必读 reference：`page-decision-tree.md`、`imagegen-integration.md`、`manifest-schema.md`、`qa-rubric.md`。
- 必读 `$imagegen/SKILL.md`。
- required outputs 和返回格式。

page worker prompt 模板在 `prompts/page-worker.md`。

如果无法 spawn page subagent，停止并报告 blocker。不要顺序执行页面重建。

## Rules

- 分层：每页先写 `visual_layer_plan`，再生成视觉层。计划必须区分 generated clean background、generated picture assets、generated art text assets、editable native text、minimal native shapes。
- 背景：默认用 `$imagegen` 生成或编辑一张 full-slide clean background。背景可以包含图片区域、装饰小字、纹理和视觉氛围，但不得包含会被 native text 覆盖的主文字。
- 图片：页面中的照片、截图、图表视觉、UI、证件、产品图和含字图片默认用 `$imagegen` 高保真重建为独立 asset，保证内容和源图一致。不要默认裁 source。
- 艺术字：复杂字体效果默认用 `$imagegen` 生成透明 asset。普通正文/标题才作为 native text box。
- 文字：所有需要后续编辑的主文字应成为可见原生 PPT text box。隐藏、透明、1 pt、off-canvas 或 metadata-only 文本不算可编辑文字。
- 字号：先根据 source 字形高度、容器高度和同行密度估算，再用 preview 对照缩放；不确定时偏小而不是偏大。manifest 必须记录 `quality_checks.font_size_calibrated=true`。
- 结构：native shape 只用于确实简单且不会影响视觉保真的 primitive，例如直线、矩形、圆形、表格线、坐标轴和基础容器。复杂视觉不要用 SVG 或 native shape 硬拼。
- provenance：每个最终 raster asset 都必须有来源记录，优先记录 imagegen prompt、输入图角色、输出路径和 hash。
- QA：确定性 validation 必要但不充分。必须检查 `preview.png` 和 `split_assets_contact.png`，重点看视觉层是否像源页、主文字是否重复/缺失、艺术字和嵌入图片是否准确。
- repair：修最小失败范围。不要为了一个文本框或一个图标重建整页；但如果 clean background 与源页漂移明显，应重做该背景。
- 状态：`page_jobs.json`、`imagegen-jobs.json` 的关键状态必须由脚本推进。

## Acceptance Criteria

- 输出是有效 `.pptx`。
- 单图输出 1 页；多图每图 1 页；PDF 第 N 页对应输出第 N 页；PPT/PPTX 第 N 页对应输出第 N 页。
- PPT/PPTX speaker notes 按页原样复制，不翻译、不摘要、不交给 page worker 改写。
- 每页有 `visual_layer_plan`、`manifest.json`、`page.pptx`、`preview.png`、`split_assets_contact.png`、`validation.json`、`page_result.json`。
- 每页 source image size、主文字清单、视觉分层计划、generated background、generated assets、asset provenance、known limits 都有记录。
- 每个 page 都由 `record_page_dispatch.py` 记录 dispatch，并由 `record_page_result.py` 记录结果。
- 最终 deck 有 `final/<origin>_edited.pptx` 和 `final/validation.json`。
- 若出现 blocker，最终回复必须说明 blocker 阶段、证据路径和未完成原因；不能称为正常完成。

## Reference Map

- `references/architecture.md`：职责边界、run/page 目录结构、owner 原则。
- `references/state-machine.md`：run/page/imagegen 状态机和脚本推进规则。
- `references/subagent-contract.md`：page worker、repair worker 的提示词契约和返回格式。
- `references/imagegen-integration.md`：如何组合 `$imagegen` / GPT Image 2，包括 clean background、嵌入图片、艺术字、asset sheet、透明化和记录。
- `references/page-decision-tree.md`：页面分析、视觉分层、背景/图片/艺术字/主文字边界。
- `references/manifest-schema.md`：deck/page/imagegen JSON schema 第一版。
- `references/qa-rubric.md`：高保真视觉层、主文字、资产、背景、PPTX 结构 QA 标准。
- `references/repair-policy.md`：repair queue、最小返工范围和 blocker 判定。
- `references/script-contracts.md`：脚本职责、输入输出和允许调用者。
- `prompts/page-worker.md`：普通页面重建 worker prompt。
- `prompts/page-repair-worker.md`：页面修复 worker prompt。
- `prompts/imagegen-clean-base.md`：clean background 生成/编辑 prompt。
- `prompts/imagegen-asset-sheet.md`：图片、艺术字和视觉资产生成 prompt。
- `prompts/imagegen-repair.md`：targeted imagegen repair prompt。
