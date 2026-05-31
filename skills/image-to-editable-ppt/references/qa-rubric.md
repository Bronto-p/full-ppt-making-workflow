# QA Rubric

确定性验证必要但不充分。最终接受前必须检查 preview 和 contact sheet。

## 结构 QA

- PPTX 是有效 zip/package。
- slide count 与输入页数一致。
- PDF/PPTX 页码映射正确。
- media relationship 完整。
- manifest 引用的 asset 文件都存在。
- media hash 与 manifest provenance 匹配。
- speaker notes hash 匹配。
- 不存在原始 full-slide source raster + editable text overlay 的违规模式。
- full-slide background 如果存在，必须是 imagegen clean background，而不是 source crop 或 user-provided full-slide screenshot。

## Visual Layer QA

- `visual_layer_plan` 存在并且与 manifest 实际对象一致。
- generated clean background 覆盖整页底层，视觉接近 source。
- clean background 已移除会被 native text 重建的主文字、主要数字和标签。
- clean background 没有 ghost text、伪文字、模糊块、硬涂抹、布局漂移或新发明的容器。
- 允许保留背景氛围小字、水印、微纹理文字，但必须在 `background_decorative_text_policy` 说明，且不能与 native text 重复。
- 页面中的照片、截图、图表视觉、UI、证书、产品图、医学图和含字图片应作为 generated picture asset 或明确归入 generated background。
- 艺术字应作为 generated art text asset；不能硬转成普通字体，也不能 SVG 拼。
- 图标、pictogram、徽章、贴纸、手绘标记和复杂箭头应作为 imagegen visual asset；不能用粗糙 native shape 或 SVG 替代。

## 文本 QA

- `text_inventory` 覆盖所有需要编辑的主文字。
- 每个可编辑主文字都是真实可见的 native PPT text box。
- 没有隐藏文本、透明文本、1 pt 文本、off-canvas 文本。
- 预览中没有明显裁切、错误换行、容器文字溢出。
- 中文预览不应显示方框或乱码；必要时使用稳定 CJK 字体。
- 字号和位置必须按 source 校准，不允许默认放大标题、正文或标签。
- 如果 preview 中同层级文字比 source 明显更大、更粗、更拥挤或换行更多，必须 repair。
- 主文字不能在 generated background 和 native text 中重复出现。

## 资产 QA

- `visual_inventory` 覆盖所有必需非主文字视觉对象。
- 每个必需视觉对象有 imagegen-generated 表示，除非明确记录为 generated background 的一部分。
- 不允许 `.svg` asset 作为复杂视觉复刻。
- asset sheet 切分结果没有粘连、缺边、错名、碎片、跨对象阴影。
- alpha 边缘没有明显 chroma-key 残留。
- 每个最终 raster asset 有 provenance。
- 图标、pictogram、徽章、艺术字不能漏项，不能被替换成同类但不同的符号。
- 嵌入图片/截图/图表视觉里的文字、数字、标点和布局应尽量与源图一致；明显错误必须 repair。
- source-derived raster asset 是例外路径，必须有 exception reason 和 source 区域。

## 背景 QA

- generated background 无主文字残留。
- generated background 无会被后续重建的前景对象。
- 背景修复区域无明显 ghost、模糊块、涂抹块、伪文字。
- 复杂背景 clean background 必须和 source 是同一页面身份：构图、透视、主要物体位置、容器布局、色彩、光照和关键细节不能明显漂移。
- 如果 `$imagegen` 生成了同主题但不同页面，即使 deterministic validation 通过，也必须 repair。

## 形状 QA

- native shape 只用于简单 primitive。
- source 是直角矩形、表格外框或方形面板时，manifest 必须用 `rect`。
- `roundRect` 只在 source 明确为圆角时使用，并记录 `source_corner_radius_px`。
- 重建圆角半径必须接近 source，轻微圆角不能被放大成胶囊。
- 不要因为设计偏好把普通矩形改成圆角矩形。
- 不要把图标、艺术字、复杂箭头、插画、纹理、复杂图表视觉拆成 native shape。

## 视觉 QA

- `preview.png` 必须存在。
- `split_assets_contact.png` 必须存在，并展示 origin 与 preview 对比。
- 视觉漂移、缺图片、缺艺术字、缺图标、低质量占位图、粗糙 native-shape 图标都应进入 repair。
- 大容器角形、表格边界、卡片边框要和 source 对齐；圆角误判是 repair blocker，不是低风险 warning。

## 阻塞与 Warning

blocker：

- 子 agent 不可用。
- 必需 `$imagegen` 不可用。
- 输入无法归一化。
- final PPTX 无法打开。
- page 缺少 buildable manifest/page.pptx。
- 必需 generated background 缺失。
- 必需视觉对象缺失。
- SVG/native shape 被用于复杂视觉 fallback。
- 复杂背景 clean background 明显失真或变成不同页面。
- generated background 残留主文字并与 native text 重影。
- source 直角矩形被重建成圆角矩形，且未能证明 source 有圆角。
- 文字字号/位置明显偏离 source，导致布局拥挤、溢出或遮挡。

warning：

- 轻微视觉漂移。
- 部分非关键装饰未完全一致。
- 已记录的低风险字体差异。
- imagegen 生成的内部小字存在轻微差异，但该区域不是主文字、不是客户要求 100% 准确的图片资产。

warning 可以如实报告；blocker 不能称为完成。
