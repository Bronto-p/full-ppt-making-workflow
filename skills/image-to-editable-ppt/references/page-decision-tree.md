# 页面分层决策树

## 目标

页面重建采用 imagegen-first layered reconstruction：

1. 用 `$imagegen` / GPT Image 2 生成高保真视觉层。
2. 用 native PowerPoint text box 覆盖需要后续编辑的主文字。
3. 只在确定简单且不影响视觉保真的地方使用 native shape。

不要把复杂视觉拆成 SVG 或一堆 PPT primitive。这个 skill 的默认取舍是：视觉保真优先，主文字可编辑，复杂视觉由图片生成承担。

## 1. 建立 Visual Layer Plan

page worker 收到 `source.png` 后，先写 `visual_layer_plan`，至少包含：

- `primary_text_to_rebuild`: 需要成为 native text box 的标题、正文、普通标签、按钮文字、数据数字。
- `generated_background`: full-slide clean background 的生成策略。
- `generated_picture_assets`: 页面中的照片、截图、图表视觉、UI、证书、产品图、医学图、含字图片等独立资产。
- `art_text_assets`: 艺术字、手写字、复杂字体效果、发光字、贴纸字、徽章字。
- `generated_visual_assets`: 图标、pictogram、装饰符号、复杂箭头、手绘标记、纹理对象。
- `native_text_boxes`: native 主文字对应关系。
- `minimal_native_shapes`: 只包含简单 primitive。
- `background_decorative_text_policy`: 哪些小字/水印/纹理文字作为背景装饰保留，为什么不会与 native text 重复。

先计划，后生成。不要边看边画 SVG。

## 2. 主文字

主文字指用户后续大概率要编辑、且在 PPT 里应可选择的文字：

- 标题、副标题、正文段落。
- 普通标签、按钮文字、表头、页内编号。
- 图表中的主要数值和轴标签，如果用户可能需要改。
- 业务语义明确的中文/英文短语。

所有主文字默认成为原生 PPT text box。隐藏、透明、1 pt、off-canvas 或 metadata-only 文本不算可编辑文字。

主文字必须从 generated background 中移除。否则会出现背景一份、native text 一份的重影。

字号不要靠默认值猜测：

- 按 source 中实际字形高度、容器高度、行距和密度估算。
- 同一层级文字用同一组 font size，例如标题、副标题、正文、标签、状态徽章。
- 中文密集版面宁可比估算小 5%-10%，不要偏大。
- 构建 preview 后对照 source。如果标题、正文或标签比 source 更粗大、更拥挤或换行更多，先下调 font size。

manifest 必须通过 `quality_checks.font_size_calibrated=true` 记录字号校准完成。

## 3. Generated Clean Background

默认生成一张 full-slide clean background，作为 PPT 最底层图片。

clean background 应保留：

- 原始画布比例、构图、网格和空间关系。
- 背景色、渐变、纹理、照片/插画氛围、光照、材质。
- 卡片、容器、面板、空图表框、表格网格、分隔线、阴影。
- 不需要单独移动的背景装饰。
- 作为背景氛围的小字、水印、伪屏幕纹理、装饰性微文本；前提是它们不是主文字，且不会被 native text 盖重复。

clean background 应移除：

- 所有将用 native text box 重建的标题、正文、标签、数字。
- 将作为独立 imagegen asset 重建的艺术字、图标、贴纸、徽章、图片和图表视觉。
- 任何会导致重影的前景对象。

prompt 不能只写“remove text”。必须列出 preserve 和 remove 清单。复杂背景要把 source 当作 edit target 和强约束参考，保留同一页面身份，而不是生成同主题新页。

manifest 中 `background_strategy` 至少记录：

- `mode: "imagegen-full-clean-background"` 或局部 imagegen repair 模式。
- `source_consistency_contract`: 要保留的构图、颜色、容器、图片区域、光照和风格。
- `removed_primary_text`: 已移除的主文字类别。
- `preserved_decorative_text`: 保留的装饰小字/水印/纹理说明。
- `comparison_note`: preview 对照 source 后的结论。

## 4. Generated Picture Assets

页面里的照片、截图、图表视觉、UI 截图、证书、医学图、产品图、人物图、带字图片等，默认用 `$imagegen` 高保真重建为独立 raster asset。

要求：

- 保留源图内容、构图、文字、排版、颜色、比例、边框和风格。
- 作为独立 asset 放在页面上，便于移动/替换/缩放。
- 不要默认裁 source；source-derived raster 是例外，不是正常策略。
- 如果 asset 内部有文字，prompt 要明确要求文字、数字、标点和排版与源图一致。
- 如果该图片本身就是整页背景的一部分、且不需要独立移动，可以合入 clean background，但必须在 `visual_layer_plan` 说明。

provenance 推荐：

```json
{
  "path": "assets/chart_panel.png",
  "source_type": "imagegen-picture-reconstruction",
  "source": "source.png",
  "source_region_px": [120, 220, 640, 360],
  "imagegen_job_id": "imagegen_003",
  "provenance_note": "Rebuilt the embedded chart panel with text and layout fidelity."
}
```

## 5. Art Text Assets

艺术字不是普通 editable text。

以下默认生成透明 imagegen asset：

- 手写字、毛笔字、签名字。
- 发光字、金属字、3D 字、立体字。
- 渐变描边字、阴影字、贴纸字、徽章字。
- 字体身份很强、转成普通字体会明显失真的文字。

要求：

- 用 source 作为视觉参考。
- 保持字形、颜色、描边、阴影、纹理、角度和位置。
- 输出透明背景资产或可去底 asset sheet。
- 不再叠同样 native text，除非用户明确要求艺术字也要可编辑并接受视觉下降。

## 6. Generated Visual Assets

以下对象默认用 `$imagegen` 生成/编辑：

- 图标、pictogram、symbol、logo-like mark。
- 徽章、贴纸、胶带、印章、角标。
- 手绘标记、手绘箭头、装饰下划线、圈注、对勾、叉号。
- 复杂箭头、图标化节点、带纹理或阴影的元素。
- dashboard 或图表里的语义小图标、趋势图标、警告符号、状态符号。

可以用稀疏 asset sheet，但必须对账：

- 切分出的资产数量覆盖 inventory。
- 每个资产语义、颜色、形状和风格接近 source。
- 不缺图标，不替换成同类但不同符号。
- 对象之间不粘连、不互相投影。

## 7. Minimal Native Shapes

native shape 只用于简单 primitive：

- 直线、虚线、折线。
- 矩形、圆角矩形、圆形、椭圆。
- 纯色卡片、面板、分隔线、边框。
- 表格线、坐标轴、网格线。
- 简单柱状块、进度条、状态色块。

复杂图标、插画、艺术字、纹理、照片、复杂图表视觉、复杂箭头不要用 native shape 或 SVG 硬拼。

角形选择仍然要保守：

- `straight` 用 `rect`。
- `small-radius`、`large-radius`、`pill` 用 `roundRect`，并估算 `source_corner_radius_px`。
- 不确定时偏向 generated background 或 imagegen asset，不要用默认圆角 shape 猜。

## 8. 禁止 SVG Fallback

不要在 manifest 中引用 `.svg` 作为复杂视觉资产。SVG 不能作为 “imagegen 不方便” 时的替代方案。

如果一个对象无法用简单 native shape 表示，就用 `$imagegen`。如果 `$imagegen` 不可用，报告 blocker。

## 9. 层级

推荐 z-index：

- generated clean background：0
- minimal native structural shapes：10-20
- generated picture assets：30
- generated visual assets：35
- generated art text assets：38
- native editable text：40+

## 10. Manifest 坐标

页面 manifest 使用 source-image pixel coordinates：

- `source.width_px`
- `source.height_px`
- `box_px: [x, y, width, height]`
- `points_px: [x1, y1, x2, y2]`

文本框要比源图字形边界更宽松，避免 PowerPoint/WPS/preview font metrics 导致裁切或错误换行。
