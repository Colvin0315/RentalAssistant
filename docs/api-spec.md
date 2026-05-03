# RentGuard API 设计

## 一、说明

本文档定义 RentGuard 第一版后端 API，供前后端联调与后端开发参考。

统一前缀：

```text
/api/v1
```

## 二、文档上传

### `POST /documents/upload`

上传租房合同或相关材料。

请求格式：

- `multipart/form-data`
- 字段：
  - `file`：合同 PDF、DOCX 或图片
  - `document_type`：可选，如 `contract`、`chatlog`、`listing`

响应示例：

```json
{
  "document_id": "doc_123",
  "filename": "rental_contract.pdf",
  "status": "uploaded"
}
```

## 三、文档解析

### `POST /documents/{document_id}/parse`

对上传文件执行文本提取、OCR 与条款切分。

响应示例：

```json
{
  "document_id": "doc_123",
  "status": "parsed",
  "chunk_count": 42,
  "fields": {
    "rent": "4500元/月",
    "deposit": "4500元",
    "lease_term": "2026-06-01 至 2027-05-31"
  }
}
```

## 四、向量索引构建

### `POST /documents/{document_id}/index`

对解析结果构建 embedding 并写入向量索引。

响应示例：

```json
{
  "document_id": "doc_123",
  "status": "indexed"
}
```

## 五、智能问答

### `POST /qa/ask`

请求示例：

```json
{
  "document_id": "doc_123",
  "question": "如果我提前退租，会不会被扣押金？"
}
```

响应示例：

```json
{
  "answer": "合同约定提前退租时，若未经房东同意，押金可能被部分或全部扣除。",
  "citations": [
    {
      "chunk_id": "clause_08",
      "text": "若乙方未经甲方同意提前解除合同，甲方有权不退还押金。"
    }
  ],
  "risk_flags": [
    {
      "title": "提前解约处罚较重",
      "severity": "high"
    }
  ],
  "needs_followup": false
}
```

## 六、风险分析

### `POST /risk/analyze`

请求示例：

```json
{
  "document_id": "doc_123"
}
```

响应示例：

```json
{
  "document_id": "doc_123",
  "risks": [
    {
      "risk_id": "risk_01",
      "title": "押金退还条件不明确",
      "severity": "high",
      "clause_id": "clause_05",
      "explanation": "合同允许扣除押金，但未明确扣除标准和认定方式。"
    }
  ]
}
```

## 七、沟通话术生成

### `POST /drafts/generate`

请求示例：

```json
{
  "document_id": "doc_123",
  "scenario": "deposit_refund",
  "tone": "polite"
}
```

响应示例：

```json
{
  "draft": "您好，根据合同第 5 条关于押金退还的约定，在房屋及家具设备无损坏的情况下，押金应于退租后退还。现我已完成搬离并配合交接，烦请您尽快办理押金退还。"
}
```

## 八、评测执行

### `POST /eval/run`

请求示例：

```json
{
  "dataset_name": "golden_cases_v1",
  "document_id": "doc_123"
}
```

响应示例：

```json
{
  "dataset_name": "golden_cases_v1",
  "metrics": {
    "answer_accuracy": 0.82,
    "citation_accuracy": 0.78,
    "risk_recall": 0.75
  }
}
```

## 九、问答日志

### `GET /sessions/{session_id}/logs`

返回一次问答流程中的检索结果、回答内容和调试日志。

响应示例：

```json
{
  "session_id": "sess_123",
  "events": [
    {
      "type": "retrieval",
      "chunks": ["clause_05", "clause_08"]
    },
    {
      "type": "answer",
      "text": "合同约定提前退租可能导致押金被扣除。"
    }
  ]
}
```

## 十、建议后端模块划分

- `routes_upload.py`
- `routes_qa.py`
- `routes_risk.py`
- `routes_eval.py`
- `parser_service.py`
- `retrieval_service.py`
- `agent_service.py`
- `eval_service.py`
