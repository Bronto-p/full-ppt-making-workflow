# Page Repair Worker Prompt 模板

```text
修复 image-to-editable-ppt 的一个页面问题。

Run dir: <absolute run dir>
Page id: <page_001>
Page dir: <absolute page dir>
Repair item id: <repair item id>
Failure type: <failure type>
Evidence:
- validation: <absolute path>
- preview: <absolute path>
- contact_sheet: <absolute path>
- repair_note: <absolute path or inline note>

允许修改范围：
<one native text box | generated clean background | one imagegen asset | one art text asset | one manifest section | etc>

你只拥有这个 Page dir。不要编辑 deck_manifest.json、page_jobs.json、notes_manifest.json、final 输出、input 原件或任何其他 page 目录。

在任何生图或改图前，读取并遵守：
${CODEX_HOME:-$HOME/.codex}/skills/.system/imagegen/SKILL.md

目标：
只修复 repair item 指定的最小失败范围。默认仍然使用 imagegen-first 策略：背景、嵌入图片、艺术字、图标、复杂装饰和复杂图表视觉都用 $imagegen / GPT Image 2 修复，不用 SVG/native shape 伪造。不要重建整页，除非 repair item 明确说明整页 generated background 或 manifest 不可用。

常见 repair：
- `bad_generated_background`: 重新编辑/生成 clean background，移除残留主文字，保留源页构图、颜色、容器和装饰氛围。
- `primary_text_left_in_background`: 只修复背景中残留的标题/正文/标签/数字，避免与 native text 重复。
- `bad_generated_picture_asset`: 重新生成页面中的照片、截图、图表视觉、UI 或含字图片资产。
- `bad_art_text_asset`: 重新生成艺术字透明资产，保持源页字形效果、颜色、描边、阴影和位置。
- `missing_asset`: 生成缺失的视觉对象并更新 manifest/provenance。
- `clipped_text` / `wrong_text_wrapping`: 修改 native text box、字号或行距，不重做视觉层。

完成后必须重新生成或更新：
- manifest.json
- page.pptx
- preview.png
- split_assets_contact.png
- validation.json
- page_result.json

`page_result.json` 必须是 JSON，字段与 page worker 相同，路径必须指向当前 Page dir 内的文件。

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
