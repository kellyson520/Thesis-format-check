# 技术规格方案 (Technical Specification)

## 需求背景
目前用户在一次校验完成后，如果想针对同一文件再次运行校验（例如，调整规则后或因为网络偶发导致的完成但无内容场景），必须重新执行拖拽或文件选择。增加"重新检测"按钮可提升用户体验的连贯性。

## API 实现建议
无需修改后端 API。可以直接在前端通过 Vue 状态重用已保存在 `uploadedFile` 引用中的 `File` 对象，并再次发起 `POST /api/check/stream` 请求。

## 前端组件修改建议 (`App.vue`)

### Logic Update
1. **`reCheck` function**:
   ```javascript
   const reCheck = async () => {
     if (!uploadedFile.value) return
     await uploadFile(uploadedFile.value)
   }
   ```
2. **`uploadFile` function refine (optional)**:
   Ensure `uploadFile` properly resets states before starting. (Checked earlier, it already resets `loading`, `progress`, `issues`, and `validationDone`).

### UI Layout Update
在 `App.vue` 的 `<div class="action-row">` (约 442 行) 前后添加：
```html
<button class="btn btn-ghost" @click="reCheck" :disabled="loading">
  🔄 重新检测
</button>
```

### UI Detail Specs
*   **Icon**: 🔄 (Rotating icon font or SVG)
*   **Color**: Use `btn-ghost` style to keep it subtle compared to "Export" and "Fix" primary actions.
*   **States**: 
    - `Disabled` during loading to prevent re-entrant calls.
    - `Visible` once detection is done OR once a file has been at least once uploaded.

## Implementation Steps
1.  Locate Script section in `App.vue`.
2.  Append `reCheck` function.
3.  Modify template to include the button.
4.  Apply styles if necessary (reusing `.btn-ghost` and `.btn`).
