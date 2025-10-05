### 05. ICS 导入/导出

本节指导以 Python 处理 iCalendar（.ics）文件，实现导入固定事件与导出当前日程。

### 目标

- `POST /v1/ics/import`：multipart/form-data 上传 .ics，解析为 Event 列表
- `GET /v1/ics/export`：根据当前事件生成 .ics 内容

### 依赖建议

```
ics
python-dateutil
```

### 提示词（实现）

```
实现两个端点与工具函数：
- parse_ics(file_bytes)->list[Event]
- build_ics(events)->bytes
并提供文件级单测：使用 BytesIO 构造内存文件，不依赖磁盘。
```

### 测试方法

- 用示例 .ics 导入 → 返回 Event 列表，字段正确
- 导出 → 下载的内容可被日历客户端导入

### 验收标准

- 基本字段兼容主流日历；错误文件返回 4xx 并包含错误信息。


