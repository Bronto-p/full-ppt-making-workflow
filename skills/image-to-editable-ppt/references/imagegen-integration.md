# `$imagegen` / GPT Image 2 集成

## 入口

所有图片生成、图片编辑、背景修复、嵌入图片重建、艺术字、透明 bitmap 和 asset sheet 都必须使用 `$imagegen`。

使用前读取：

```text
${CODEX_HOME:-$HOME/.codex}/skills/.system/imagegen/SKILL.md
```

不要在本 skill 里直接调用 Image API，不写临时 SDK 脚本。若 `$imagegen` 支持模型选择，优先使用 `gpt-image-2` 或当前可用的最高保真 GPT Image 模型；若只能使用 built-in `image_gen`，记录实际工具和模型/模式。

## Imagegen-First 原则

本 skill 不再把 imagegen 当少量修补工具。默认视觉层都走 imagegen：

- full-slide clean background
- embedded picture / screenshot / chart visual / UI panel
- text-bearing picture asset
- art text / decorative typography
- icons / pictograms / decorative symbols
- complex arrows / hand-drawn marks / badges / stickers
- localized repair

native PPT text 只承载需要后续编辑的主文字。native shape 只承载简单 primitive。

## 本地图片角色

page worker 必须明确每张输入图片角色：

- `source.png` 作为 edit target：用于 clean background、去主文字、背景修复。
- `source.png` 作为 strict visual reference：用于嵌入图片、艺术字、图标和视觉资产重建。
- 已生成的 clean background 或 asset sheet 作为 repair target。
- 已生成的 picture/art-text asset 作为 targeted repair target。

如果 built-in edit 需要本地图片进入上下文，先让图片可见，再调用 built-in edit。

## Clean Background

clean background 是页面最底层 full-slide generated raster。它不是原始 source screenshot。

适用：

- 所有正常页面，除非页面本身几乎全是需要可编辑的 native text 和极简单纯色背景。
- 照片、纹理、插画、纸张质感、复杂渐变、复杂光影。
- dashboard、报告页、海报页、医学/产品/品牌页、信息图。
- 前景文字、图片、图标、标签、贴纸、艺术字遮住了底层视觉。

保真要求：

- 必须把 `source.png` 作为 edit target 和强约束参考。
- 输出应保持原始构图、透视、主要物体位置、屏幕/面板布局、色彩、光照、材质、景深和背景身份。
- 移除后续会重建的主文字、艺术字、图片资产、图标、标签、贴纸、手绘标记和装饰对象。
- 可以保留背景氛围里的小字、水印、微纹理文字、不可编辑的屏幕噪声文字；必须在 plan/manifest 说明它们不是主文字。
- 如果整张 clean background 与 source 的空间、物体、光照、容器布局或品牌风格明显不同，不能通过 QA。

prompt 必须具体列出：

- `preserve`: 构图、容器、颜色、光照、材质、图片区域、装饰氛围。
- `remove`: 标题、正文、主要标签、数据数字、艺术字、独立图片、图标等会单独叠加的对象。
- `allowed decorative text`: 可以作为背景保留的小字/水印/纹理文字。
- `forbid`: pseudo text、ghost text、blur patches、new layout、new objects、watermark。

## Embedded Picture Reconstruction

页面中的图片、截图、UI、图表视觉、证书、医学图、人物图、产品图、含字图片等，默认用 imagegen 重建为独立 asset。

要求：

- 使用 `source.png` 和源区域说明作为 strict visual reference。
- prompt 需要要求文字、数字、标点、图例、UI 文案、图表标签和空间位置保持一致。
- 输出 asset 可以是透明或矩形图片，取决于源图形态。
- 最终 asset 必须复制进 page dir，并记录 `source_type: "imagegen-picture-reconstruction"`。

不要默认裁 source。source crop 是例外路径，只能在用户明确要求或 imagegen 无法合规重建时使用。

## Art Text

艺术字默认由 imagegen 生成透明 asset。

prompt 要求：

- 保持源字形、笔画风格、颜色、渐变、描边、阴影、发光、纹理、透视和旋转。
- 不要把艺术字改成普通字体。
- 不要生成额外文字。
- 输出背景透明或适合 chroma-key 去底。

记录 `source_type: "imagegen-art-text"`。

## Visual Asset Sheet

可以用稀疏 chroma-key asset sheet 降低调用次数。

要求：

- 背景是纯色 chroma-key。
- 元素之间留足距离。
- 每个元素内部完整。
- 可以包含图标、pictogram、徽章、贴纸、手绘标记、复杂箭头、艺术字等。
- 对含字图片或复杂 UI/图表，优先单独生成，不要塞进拥挤 asset sheet。
- 不要对象粘连、跨对象阴影、裁切边缘。
- 不要漏掉 `visual_inventory` 中的必需对象。

生成后：

1. 用 `$imagegen` helper 去 chroma-key。
2. 用 `process_asset_sheet.py` 做去底、组件切分或定点裁剪；`split_alpha_components.py` 只是它的内部组件拆分 helper。
3. 检查 alpha 和切分结果。
4. 与 `visual_inventory` 对账：数量、命名、语义和外观都必须匹配。
5. 写入 manifest provenance。

## 结果记录

生成图通常先落到 `$CODEX_HOME/generated_images/...`。

page worker 必须用 `record_imagegen_result.py` 把选中结果复制到 page 目录，并记录：

- source path
- output path
- prompt path/hash
- input image roles
- intended layer: `clean-background`、`picture-asset`、`art-text-asset`、`visual-asset`、`repair`
- model/tool when available
- sha256
- metadata
- completed_at

不要让 `manifest.json` 引用只存在于 `$CODEX_HOME/generated_images/...` 的图片。

## 失败处理

以下情况不要降级到 SVG/native/Pillow：

- imagegen 工具不可用。
- generated background 还残留主文字。
- generated picture asset 文字不准。
- art text 变成普通字体。
- 图标/徽章变成同类但不同符号。

先 targeted repair；仍无法修复时报告 blocker 或 known limitation，不要伪装成完成。
