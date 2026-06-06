# Manifest Schema 第一版

本文件描述 JSON 文件职责和 owner。字段会随脚本实现细化。

## `deck_manifest.json`

Owner：`prepare_deck_run.py` 创建，`finalize_deck_run.py` 读取。

用途：

- 输入类型。
- page 顺序。
- page manifest 路径。
- notes manifest 路径。
- final output 路径。

关键字段：

```json
{
  "schema_version": 1,
  "run_id": "job-id",
  "input_type": "image|images|pdf|pptx",
  "max_concurrent_pages": 4,
  "pages": [],
  "notes_manifest": "notes_manifest.json",
  "output": "final/origin_edited.pptx"
}
```

## `page_jobs.json`

Owner：状态脚本写入。

用途：

- page 状态 source of truth。
- dispatch 记录。
- result 记录。
- repair 和 blocker 记录。

草案：

```json
{
  "schema_version": 1,
  "run_id": "job-id",
  "max_concurrent_pages": 4,
  "pages": [
    {
      "page_id": "page_001",
      "status": "pending",
      "page_dir": "pages/page_001",
      "page_request": "pages/page_001/page_request.json",
      "source": "pages/page_001/source.png",
      "dispatch": null,
      "result": null,
      "repair": [],
      "blocker": null
    }
  ]
}
```

`dispatch` 由 `record_page_dispatch.py` 写。`result` 由 `record_page_result.py` 写。`repair` 由 `queue_page_repairs.py` 写。`accepted` 由 `finalize_deck_run.py` 写。

## `page_request.json`

Owner：`prepare_deck_run.py`。

用途：给 page worker 的任务边界。

包括：

- page id
- page dir
- source image
- slide size
- max concurrent pages
- allowed write scope
- required outputs
- user constraints

不得包含：

- page type 预判。
- object-level 决策。
- imagegen_required 预判。

## `page_result.json`

Owner：page worker 创建，`record_page_result.py` 校验。

包括：

- manifest path
- page pptx path
- preview path
- contact sheet path
- validation path
- qa note
- known limits
- page-local output hashes，可由 record 脚本补充

## `pages/page_NNN/manifest.json`

Owner：page worker。

用途：page-level PPTX 构建 source of truth。

必须包含：

- `slide`
- `source`
- `visual_layer_plan`
- `text_inventory`
- `visual_inventory`
- `background_strategy`
- `quality_checks`
- `text_boxes`
- `shapes`
- `images`
- `asset_provenance`
- page strategy / known limits

### `visual_layer_plan`

`visual_layer_plan` 是 imagegen-first 分层计划，必须在生成视觉层前确定。

推荐结构：

```json
{
  "strategy": "imagegen-first-layered-reconstruction",
  "primary_text_to_rebuild": [
    {
      "id": "text_title",
      "text": "Quarterly update",
      "reason": "main title should remain editable",
      "native_text_box": "tb_title"
    }
  ],
  "generated_background": {
    "asset_id": "bg_clean",
    "path": "generated/clean_background.png",
    "source_type": "imagegen-clean-background",
    "remove": ["main title", "body copy", "chart value labels"],
    "preserve": ["layout panels", "brand gradient", "decorative microtext texture"],
    "background_decorative_text_policy": "Decorative microtext in the lower texture is kept because it is not user-editable primary content."
  },
  "generated_picture_assets": [
    {
      "asset_id": "pic_dashboard",
      "description": "embedded dashboard screenshot with small labels",
      "source_region_px": [900, 180, 420, 300],
      "path": "assets/pic_dashboard.png",
      "source_type": "imagegen-picture-reconstruction"
    }
  ],
  "art_text_assets": [
    {
      "asset_id": "art_slogan",
      "description": "neon handwritten slogan",
      "path": "assets/art_slogan.png",
      "source_type": "imagegen-art-text"
    }
  ],
  "generated_visual_assets": [],
  "native_text_boxes": [],
  "minimal_native_shapes": [],
  "background_decorative_text_policy": "Decorative microtext in the lower texture is kept because it is not user-editable primary content."
}
```

### `background_strategy`

`background_strategy` 至少说明：

- mode：`imagegen-full-clean-background`、`imagegen-local-clean-background-repair`、`imagegen-generated-layout-background` 等。
- source consistency：保留哪些构图、透视、物体、颜色、光照、容器、图片区域和细节。
- removed foreground：哪些主文字、图片、艺术字、图标会被移除并重建。
- preserved decorative text：哪些装饰小字/水印/纹理文字可以保留。
- comparison note：preview 对照 source 后的背景一致性结论。

### `quality_checks`

`quality_checks` 至少包含：

```json
{
  "font_size_calibrated": true,
  "visual_inventory_matched": true,
  "background_strategy_checked": true,
  "shape_corner_geometry_checked": true,
  "imagegen_visual_layers_recorded": true,
  "generated_background_checked": true,
  "primary_text_removed_from_background": true
}
```

### `images`

`images` 可以包含 full-slide generated clean background，也可以包含独立 generated assets。

Full-slide clean background 示例：

```json
{
  "path": "generated/clean_background.png",
  "box_px": [0, 0, 1920, 1080],
  "z_index": 0,
  "alt": "imagegen clean background without primary text"
}
```

独立嵌入图片 asset 示例：

```json
{
  "path": "assets/dashboard_panel.png",
  "box_px": [980, 180, 520, 360],
  "z_index": 30,
  "alt": "generated dashboard panel"
}
```

不要在 `images` 中引用 `.svg`。复杂视觉资产必须是 imagegen raster output。

### `asset_provenance`

允许的主要 `source_type`：

- `imagegen`
- `imagegen-clean-background`
- `imagegen-picture-reconstruction`
- `imagegen-art-text`
- `imagegen-visual-asset`
- `imagegen-asset-sheet`
- `imagegen-repair`
- `user-provided`
- `user-approved-rasterization`
- `source-derived-rasterization`

source-derived raster 是例外，不是默认策略。它必须记录：

```json
{
  "path": "assets/example.png",
  "source": "source.png",
  "source_type": "source-derived-rasterization",
  "source_region_px": [100, 200, 60, 60],
  "exception_reason": "User explicitly requested exact source crop for this non-text icon.",
  "require_edge_safe_alpha": true
}
```

它只允许用于无主文字的小型独立视觉对象，不能用于整页、整卡片、整图表、嵌入图片或文字区域，除非用户明确要求这种低编辑性结果。

### Shapes

`roundRect` shape 必须记录 `source_corner_radius_px`，可以额外记录 `corner_reason`。原图是直角矩形时必须使用 `rect`。

推荐记录：

```json
{
  "type": "roundRect",
  "box_px": [64, 169, 472, 187],
  "source_corner_radius_px": 12,
  "corner_category": "small-radius",
  "corner_reason": "source card corners are lightly rounded"
}
```

`corner_category` 可选值：`straight`、`small-radius`、`large-radius`、`pill`。`straight` 不应使用 `roundRect`。

## `pages/page_NNN/imagegen-jobs.json`

Owner：page-local imagegen 脚本。

用途：记录 clean background、picture asset、art text asset、asset sheet、repair asset 的生成和处理过程。

状态见 `state-machine.md`。

每个 job 推荐记录：

- intended layer
- prompt file/hash
- input image roles
- selected output
- copied output path
- source type
- sha256
- model/tool when available

## `notes_manifest.json`

Owner：`prepare_deck_run.py` 创建，`finalize_deck_run.py` 读取。

用途：

- PPT/PPTX speaker notes 原文。
- notes hash。
- page 映射。

notes 不交给 page worker，不翻译、不摘要、不改写。
