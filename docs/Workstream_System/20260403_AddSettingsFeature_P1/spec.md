# Settings Feature Spec

## API Design

### 1. `GET /api/settings`
获取系统设置摘要。
**Response:**
```json
{
  "version": "1.2.0",
  "plugins": [
    { "id": "font", "name": "字体校验", "enabled": true },
    { "id": "spacing", "name": "间距校验", "enabled": true },
    { "id": "pagination", "name": "高级排版", "enabled": false }
  ],
  "cache_size_kb": 1284,
  "last_check_update": "2026-04-03 09:00"
}
```

### 2. `POST /api/settings/plugin`
更新插件状态。
**Request:**
```json
{ "plugin_id": "font", "enabled": false }
```
**Response:**
```json
{ "status": "ok", "message": "Plugin status updated" }
```

### 3. `POST /api/settings/clear_cache`
执行缓存清理。
**Response:**
```json
{ "status": "ok", "deleted_files": 45, "freed_kb": 2500 }
```

### 4. `GET /api/settings/check_update`
检查更新。
**Response:**
```json
{ "has_update": true, "new_version": "1.2.1", "changelog": "Fix spacing issue..." }
```

## Backend Implementation Changes

1. **`src/version.py`**: New file.
2. **`src/main.py`**: Adpater to add these routes.
3. **`src/use_cases/rule_config.py`**: Add utility to update plugin state in `RuleConfig` and save to `rules.yaml`.

## UI Design

- **Panel**: Side panel sliding in from the right.
- **Background**: Glassmorphism (blur + semi-transparent dark bg).
- **Icons**: Lucide icons for each plugin type.
- **Animation**: CSS transitions for the slider and toggle buttons.
