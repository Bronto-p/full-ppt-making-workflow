# Repair Policy

## 原则

修最小失败范围，不推倒重来。

repair item 必须包含：

- page id
- failure type
- evidence path
- suggested scope
- required output
- previous attempt summary

## 失败类型

- `missing_text`
- `clipped_text`
- `wrong_text_wrapping`
- `missing_asset`
- `bad_asset_split`
- `bad_generated_background`
- `primary_text_left_in_background`
- `bad_generated_picture_asset`
- `bad_art_text_asset`
- `bad_asset_provenance`
- `layout_drift`
- `broken_pptx`
- `notes_mismatch`
- `imagegen_blocked`
- `svg_fallback_used`
- `native_shape_complex_visual`

## 返工范围

优先顺序：

1. 修改一个 text box。
2. 重新编辑 generated clean background 的局部问题。
3. 重新生成一个 picture/art-text/visual asset。
4. 修改一个 coordinate 或简单 shape。
5. 重新切分一个 asset sheet。
6. 重新生成一个 asset sheet。
7. 重新生成整张 generated clean background。
8. 重派整页 page worker。

不要为了一个文本框重建整页。
不要为了 imagegen 失败降级到 SVG、Pillow、HTML/canvas 或粗糙 native shape。

## Repair worker

repair worker 必须收到：

- repair item id
- 原 page dir
- 失败证据
- 允许修改范围
- 相关 preview/contact sheet
- 上一次 validation

repair worker 只能写当前 page dir。

## Blocker

以下情况停止并报告 blocker：

- 子 agent 不可用。
- 必需 `$imagegen` 不可用。
- 多次 repair 后仍没有可执行下一步。
- 输入格式无法归一化。
- 脚本无法构建有效 PPTX。
- 必需 generated background 或 generated visual asset 无法生成。
- 只能通过 SVG/native shape 伪造复杂视觉才能继续。

不设计低保真降级模式。blocker 不是低保真完成。
