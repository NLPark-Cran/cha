# Flet 0.85 API 兼容性 Skill

> **适用范围**: Flet 0.85.x (测试于 0.85.3)
> **背景**: Flet 0.85 是彻底重写的 API，与 0.7x/0.8x 早期版本完全不兼容。本 Skill 记录所有已验证的 API 差异和正确写法。

---

## 1. Button 家族（最高频踩坑区）

### 1.1 不要使用 `ElevatedButton` / `OutlinedButton` / `TextButton` / `FilledButton`

这些类在 0.85 中已被标记为 `@deprecated_class`，**统一改用 `ft.Button`**。

```python
# ❌ 废弃
ft.ElevatedButton(text="保存", on_click=...)
ft.OutlinedButton(text="取消", on_click=...)

# ✅ 正确
ft.Button(content=ft.Text("保存"), on_click=...)
```

### 1.2 `icon_size` 不在 Button 构造函数中

**只有 `Icon`、`IconButton`、`PopupMenuButton` 直接接受 `icon_size`（或 `size`）。**

Button 家族的图标大小必须通过 `ButtonStyle(icon_size=...)` 设置：

```python
# ❌ 错误 - 直接传 icon_size
ft.Button(icon=ft.Icons.SAVE, icon_size=20)

# ✅ 正确 - 通过 ButtonStyle
ft.Button(
    icon=ft.Icons.SAVE,
    style=ft.ButtonStyle(icon_size=20),
)
```

### 1.3 `text` 参数已被移除

所有 Button 不再接受 `text` 参数，改用 `content`：

```python
# ❌ 错误
ft.Button(text="保存")

# ✅ 正确
ft.Button(content=ft.Text("保存"))
```

### 1.4 `icon` 参数类型

`icon` 接受 `IconData`（`ft.Icons.XXX` 枚举）或 `Control`（`ft.Icon(...)`）：

```python
# 两种写法都可以
ft.Button(icon=ft.Icons.SAVE)                              # 传枚举
ft.Button(icon=ft.Icon(ft.Icons.SAVE, size=20, color="red"))  # 传 Icon 控件
```

### 1.5 ButtonStyle 完整可用字段

```python
ft.ButtonStyle(
    color=...,              # 文字颜色
    bgcolor=...,            # 背景颜色
    overlay_color=...,      # 点击涟漪色
    shadow_color=...,
    elevation=...,
    animation_duration=...,
    padding=...,            # ft.Padding 或数字
    side=...,               # ft.BorderSide
    shape=...,              # 圆角形状
    alignment=...,          # ft.Alignment
    enable_feedback=...,
    text_style=...,         # ft.TextStyle
    icon_size=...,          # ← 图标大小放这里！
    icon_color=...,         # ← 图标颜色放这里！
    visual_density=...,
    mouse_cursor=...,
)
```

---

## 2. Icon 与图标大小控制总表

| 控件 | icon 参数 | icon_size 参数 | 图标大小控制方式 |
|------|-----------|----------------|------------------|
| `ft.Icon` | ✅ `icon` (必填) | ✅ `size` | `size=20` |
| `ft.IconButton` | ✅ `icon` | ✅ `icon_size` | `icon_size=20` |
| `ft.Button` | ✅ `icon` | ❌ | `style=ft.ButtonStyle(icon_size=20)` |
| `ft.PopupMenuButton` | ✅ `icon` | ✅ `icon_size` | `icon_size=20` |
| `ft.PopupMenuItem` | ✅ `icon` | ❌ | 传 `ft.Icon(..., size=...)` |
| `ft.Chip` | ❌ (用 `leading`) | ❌ | 传 `ft.Icon(..., size=...)` |
| `ft.ListTile` | ❌ (用 `leading`) | ❌ | 传 `ft.Icon(..., size=...)` |
| `ft.AppBar` | ❌ (用 `leading`) | ❌ | 传 `ft.Icon(..., size=...)` |
| `ft.NavigationBarDestination` | ✅ `icon` | ❌ | 传 `ft.Icon(..., size=...)` |

**统一规则**: 只有 `Icon`、`IconButton`、`PopupMenuButton` 三个控件直接提供 size 参数；其余要么通过 style，要么传 `ft.Icon(...)` 对象。

---

## 3. SnackBar 显示方式

### 3.1 `page.open()` 已移除

```python
# ❌ 0.7x 写法，0.85 报错
page.open(ft.SnackBar(content=ft.Text("保存成功")))

# ✅ 0.85 正确写法
page.show_dialog(ft.SnackBar(content=ft.Text("保存成功")))
```

`page.show_dialog()` 接受任何 `DialogControl`（包括 `SnackBar`、`AlertDialog`、`BottomSheet`）。

---

## 4. 布局参数数据类化

0.85 将所有布局参数从模块级工具函数改为数据类：

| 旧写法 (0.7x) | 0.85 正确写法 |
|---------------|---------------|
| `ft.padding.all(16)` | `ft.Padding.all(16)` 或 `ft.Padding(16,16,16,16)` |
| `ft.padding.symmetric(vertical=8, horizontal=16)` | `ft.Padding.symmetric(vertical=8, horizontal=16)` |
| `ft.padding.only(left=10)` | `ft.Padding.only(left=10)` |
| `ft.margin.all(10)` | `ft.Margin.all(10)` |
| `ft.alignment.center` | `ft.Alignment(0, 0)` |
| `ft.alignment.top_left` | `ft.Alignment(-1, -1)` |
| `ft.border.all(width=1, color="red")` | `ft.Border.all(width=1, color="red")` |
| `ft.border_radius.all(8)` | `ft.BorderRadius.all(8)` |

### 4.1 Padding / Margin

```python
# 四边相同
ft.Padding.all(16)           # 或 ft.Padding(16, 16, 16, 16)
ft.Margin.all(10)

# 对称
ft.Padding.symmetric(vertical=8, horizontal=16)

# 单边
ft.Padding.only(left=10, top=5)

# 数字简写（部分控件支持）
padding=16   # 等同于四边 16
```

### 4.2 Border

```python
ft.Border.all(width=1, color=ft.Colors.GREY_200)

# 或逐边指定
ft.Border(
    top=ft.BorderSide(1, ft.Colors.GREY_200),
    right=ft.BorderSide(0, ft.Colors.TRANSPARENT),
    bottom=ft.BorderSide(1, ft.Colors.GREY_200),
    left=ft.BorderSide(0, ft.Colors.TRANSPARENT),
)
```

### 4.3 BorderRadius

```python
ft.BorderRadius.all(10)
ft.BorderRadius.only(top_left=8, bottom_right=8)
ft.BorderRadius.horizontal(left=4, right=12)

# 或简写
border_radius=8   # 部分控件支持直接传数字
```

---

## 5. 命名空间变化（大小写敏感）

| 旧写法 (0.7x) | 0.85 正确写法 |
|---------------|---------------|
| `ft.icons.XXX` | `ft.Icons.XXX` |
| `ft.colors.XXX` | `ft.Colors.XXX` |
| `ft.alignment.XXX` | `ft.Alignment(...)` |
| `ft.border.XXX` | `ft.Border(...)` |
| `ft.border_radius.XXX` | `ft.BorderRadius(...)` |
| `ft.padding.XXX` | `ft.Padding(...)` |
| `ft.margin.XXX` | `ft.Margin(...)` |
| `ft.TextAlign.XXX` | `ft.TextAlign.XXX` ✅ (没变) |
| `ft.FontWeight.XXX` | `ft.FontWeight.XXX` ✅ (没变) |
| `ft.MainAxisAlignment.XXX` | `ft.MainAxisAlignment.XXX` ✅ (没变) |
| `ft.CrossAxisAlignment.XXX` | `ft.CrossAxisAlignment.XXX` ✅ (没变) |

---

## 6. Page 相关 API

### 6.1 `page.query` (获取 URL 参数)

```python
# 获取参数字典
params = page.query.to_dict   # 注意：是 property，不是方法！
code = params.get("code")

# 获取单个参数
name = page.query.get("name")  # 不存在会抛 KeyError

# 获取路径
path = page.query.path
```

### 6.2 `page.client_storage` 已移除

```python
# ❌ 0.7x 写法，0.85 不存在
page.client_storage.set("token", "abc")

# ✅ 0.85 替代方案：SharedPreferences（异步）
async def save_token():
    prefs = ft.SharedPreferences()
    await prefs.set("token", "abc")
    value = await prefs.get("token")
```

### 6.3 `page.launch_url()` 参数更名

```python
# ❌ 旧参数名
page.launch_url(url, web_window_name="_blank")

# ✅ 新参数名
page.launch_url(url, web_popup_window_name="_self")

# 或用 UrlTarget 枚举
page.launch_url(url, web_popup_window_name=ft.UrlTarget.BLANK)
```

注意：`launch_url` 是**同步方法**，不需要 `await`。

---

## 7. 控件特定变更

### 7.1 Chip

```python
ft.Chip(
    label=ft.Text("标签"),           # label 必须传
    leading=ft.Icon(ft.Icons.CHECK),  # 用 leading 代替 icon
    label_text_style=ft.TextStyle(...),  # 用 label_text_style 代替 label_style
    bgcolor=...,
    on_click=...,
)
```

### 7.2 PopupMenuItem

```python
ft.PopupMenuItem(
    content=ft.Text("设置"),   # 用 content 代替 text
    icon=ft.Icons.SETTINGS,    # 支持 icon
    on_click=...,
)
```

### 7.3 AppBar

```python
ft.AppBar(
    leading=ft.Icon(ft.Icons.MENU),  # 必须是 Control，不能直接传枚举
    title=ft.Text("标题"),
    actions=[ft.IconButton(icon=ft.Icons.SEARCH)],
    bgcolor=ft.Colors.WHITE,         # 用 bgcolor 代替 color
)
```

### 7.4 NavigationBar

```python
ft.NavigationBar(
    destinations=[
        ft.NavigationBarDestination(
            icon=ft.Icons.HOME,           # 可以是枚举或 ft.Icon()
            selected_icon=ft.Icons.HOME_FILLED,
            label="首页",
        ),
    ],
    label_behavior=ft.NavigationBarLabelBehavior.ONLY_SHOW_SELECTED,
)
```

---

## 8. Image / 图片

### 8.1 base64 图片

```python
# ❌ 旧写法
ft.Image(src_base64=b64_string)

# ✅ 0.85 正确写法 - 使用 data URI
ft.Image(src=f"data:image/png;base64,{b64_string}")
```

---

## 9. 已完全移除的控件

| 旧控件 | 状态 | 替代方案 |
|--------|------|----------|
| `ft.PlotlyChart` | ❌ 已移除 | 用 matplotlib → base64 → `ft.Image` |
| `ft.Markdown` | ⚠️ 可能变更 | 检查最新版本 |
| `page.client_storage` | ❌ 已移除 | `ft.SharedPreferences()` |

---

## 10. 快速检查清单（写代码前必读）

- [ ] Button 用 `ft.Button` 而非 `ft.ElevatedButton`
- [ ] Button 没有 `text` 参数，用 `content=ft.Text(...)`
- [ ] Button 没有 `icon_size` 参数，用 `style=ft.ButtonStyle(icon_size=...)`
- [ ] SnackBar 用 `page.show_dialog(...)` 而非 `page.open(...)`
- [ ] 布局参数用 `ft.Padding`/`ft.Margin`/`ft.Border`/`ft.BorderRadius` 数据类
- [ ] 枚举用大写：`ft.Icons.XXX`、`ft.Colors.XXX`
- [ ] `page.query.to_dict` 是 property（不加括号）
- [ ] `page.launch_url` 参数是 `web_popup_window_name`
- [ ] base64 图片用 `src="data:image/png;base64,..."` 而非 `src_base64`

---

## 参考源码位置

```
venv/lib/python3.13/site-packages/flet/controls/material/button.py
venv/lib/python3.13/site-packages/flet/controls/material/icon_button.py
venv/lib/python3.13/site-packages/flet/controls/material/buttons.py    # ButtonStyle
venv/lib/python3.13/site-packages/flet/controls/material/snack_bar.py
venv/lib/python3.13/site-packages/flet/controls/page.py
```
