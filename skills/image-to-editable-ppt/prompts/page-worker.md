# Page Worker Prompt 模板

```text
重建 image-to-editable-ppt 的一个页面。

Run dir: <absolute run dir>
Page id: <page_001>
Page dir: <absolute page dir>
Source image: <absolute page dir>/source.png

你只拥有这个 Page dir。不要编辑 deck_manifest.json、page_jobs.json、notes_manifest.json、final 输出、input 原件或任何其他 page 目录。

在任何生图或改图前，读取并遵守：
${CODEX_HOME:-$HOME/.codex}/skills/.system/imagegen/SKILL.md

同时遵守这些本地 reference：
- <skill root>/references/page-decision-tree.md
- <skill root>/references/imagegen-integration.md
- <skill root>/references/manifest-schema.md
- <skill root>/references/qa-rubric.md
- <skill root>/references/script-contracts.md

目标：
把 source page 重建成高保真分层可编辑 PowerPoint。默认采用 imagegen-first 策略：用 $imagegen / GPT Image 2 生成 clean background、嵌入图片、含字图片、艺术字、图标、复杂装饰和其他视觉资产；只把需要后续编辑的主文字放成原生 PPT text box。不要用 SVG 或 native shape 伪造复杂视觉。

开始写 manifest 前必须完成 `visual_layer_plan`：
1. 主文字清单：列出需要 native editable text 的标题、正文、普通标签、按钮文字、数据数字。它们必须从 generated background 中移除，避免背景文字和 native text 重复。
2. 背景计划：定义 full-slide generated clean background。说明哪些主文字/前景会移除，哪些装饰小字、水印、纹理、符号可以保留为背景氛围。背景要保持源页构图、颜色、容器、图片区域、空间关系和视觉身份。
3. 图片/视觉资产计划：列出页面中的照片、截图、图表视觉、UI、证书、产品图、医学图、含字图片、logo-like mark、图标、pictogram、复杂箭头、手绘标记、贴纸、纹理对象。默认都用 $imagegen 高保真重建为独立 raster asset，不能默认裁 source。
4. 艺术字计划：识别手写字、复杂字体效果、发光字、徽章字、贴纸字、3D/渐变/描边文字。它们默认生成透明 raster asset，不转普通 PPT text box。
5. native shape 计划：只保留确实简单的 primitive，例如直线、矩形、圆、表格线、坐标轴、基础容器。不要用 SVG/native shape 拼图标、插画、艺术字或复杂图表。

必须在 Page dir 内产出：
- manifest.json
- imagegen-jobs.json
- page.pptx
- preview.png
- split_assets_contact.png
- validation.json
- page_result.json

`page_result.json` 必须是 JSON，至少包含：

```json
{
  "page_manifest": "manifest.json",
  "imagegen_jobs": "imagegen-jobs.json",
  "page_pptx": "page.pptx",
  "preview": "preview.png",
  "contact_sheet": "split_assets_contact.png",
  "validation": "validation.json",
  "page_result": "page_result.json",
  "qa_note": "one sentence",
  "known_limits": []
}
```

使用 $imagegen 的 built-in image_gen 路径生成 clean background、嵌入图片/截图/含字图片、艺术字、图标、asset sheet 和 repair asset。如果可指定模型，使用 gpt-image-2 或最高保真 GPT Image 模型。不要直接调用 Image API。不要使用本地脚本、SVG、canvas、HTML/CSS 或 Python 绘图来伪造复杂视觉资产。确定性脚本只可用于归一化、记录、去底、切分、裁剪、构建、验证和 QA。

manifest.json 还必须包含：
- `visual_layer_plan`: 页面分层计划，至少包含 `primary_text_to_rebuild`、`generated_background`、`generated_picture_assets`、`art_text_assets`、`native_text_boxes`、`minimal_native_shapes`、`background_decorative_text_policy`。
- `visual_inventory`: 非主文字视觉对象清单，至少记录 id、描述、分层类型、imagegen job 或 background 归属。
- `background_strategy`: 背景处理方式、source-consistency 约束、移除的主文字/前景、保留的装饰小字/纹理、是否使用整张 imagegen clean background 以及原因。
- `quality_checks`: `font_size_calibrated`、`visual_inventory_matched`、`background_strategy_checked`、`shape_corner_geometry_checked`、`imagegen_visual_layers_recorded`、`generated_background_checked`、`primary_text_removed_from_background` 都必须为 true。

生成规则：
- Clean background 可以是一张 full-slide imagegen raster，放在 `images` 最底层，`z_index` 通常为 0。provenance 使用 `source_type: "imagegen-clean-background"` 或等价 imagegen 类型。
- 嵌入图片/截图/图表视觉/含字图片必须作为独立 imagegen raster asset，不能被永久烘焙进背景，除非它本来就是背景的一部分且不需要单独移动。
- 艺术字必须作为独立透明 imagegen raster asset，放在文字/视觉层对应位置。
- 普通可编辑文字必须是 native PPT text box，不能隐藏、透明、1 pt 或 off-canvas。
- 生成图通常先落在 $CODEX_HOME/generated_images；必须用 `record_imagegen_result.py` 复制进 page dir 并记录 hash、prompt、输入图角色和输出路径。
- 如果使用 asset sheet，必须稀疏、完整、无粘连；生成后用 `process_asset_sheet.py` 去底和切分。
- 不要在 manifest 的 `images` 中引用 `.svg`。SVG 不是复杂视觉 fallback。

source-derived raster asset 是例外，不是默认策略。只有用户明确要求、或 imagegen 无法合规重建且对象不包含主文字时才可使用；必须记录 `source_type: "source-derived-rasterization"`、source 区域和例外原因。

不要重复拆源图中的文字笔画。普通主文字由 native text 承担；艺术字由 imagegen asset 承担；背景中的装饰小字如果保留，必须明确不再叠同样文字。

返回前必须：
- 从 manifest.json 构建 page.pptx
- 渲染 preview.png
- 创建 split_assets_contact.png
- 运行 page validation
- 检查 required outputs 都存在
- 视觉检查 preview/contact sheet：生成背景像源页且无主文字残留，嵌入图片/艺术字/图标准确，native 主文字不重复、不缺失、字号不过大
- 可行时修复最小 page-local 失败范围

只返回：
page_manifest=<absolute path>
page_pptx=<absolute path>
preview=<absolute path>
contact_sheet=<absolute path>
validation=<absolute path>
page_result=<absolute path>
qa_note=<one sentence>
known_limits=<none or short list>
```
