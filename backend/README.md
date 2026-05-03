# RentGuard Backend Demo

这是一个按 `docs/api-spec.md` 搭建的可运行后端 demo，当前已经接入真实解析链路、FAISS 检索和 OpenAI 兼容的 DeepSeek 问答。

## 已实现

- `POST /api/v1/documents/upload`
- `POST /api/v1/documents/{document_id}/parse`
- `POST /api/v1/documents/{document_id}/index`
- `POST /api/v1/qa/ask`
- `POST /api/v1/risk/analyze`
- `POST /api/v1/drafts/generate`
- `POST /api/v1/eval/run`
- `GET /api/v1/sessions/{session_id}/logs`

## Demo 特点

- 使用 `FastAPI + SQLite + 本地 JSON/FAISS 文件`
- 解析层支持 `txt/md/docx/pdf/图片 OCR`
- 检索层使用本地向量化 + `FAISS`
- 回答层支持 OpenAI 兼容的 `DeepSeek API`
- 风险识别使用规则引擎，并会作为回答上下文的一部分

## 启动

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

如需启用 DeepSeek 回答，请先配置环境变量：

```bash
set DEEPSEEK_API_KEY=你的key
set DEEPSEEK_BASE_URL=https://api.deepseek.com
set DEEPSEEK_MODEL=deepseek-chat
```

如需图片/PDF OCR，可按本机实际情况配置：

```bash
set TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```

服务默认启动后访问：

- [Swagger UI](http://127.0.0.1:8000/docs)
- [Health Check](http://127.0.0.1:8000/)

## 快速体验

可以先上传 [sample_contract.txt](/C:/Coding/WorkPlace/Project/LLM_Agent/backend/sample_contract.txt)，再依次调用：

1. `/api/v1/documents/upload`
2. `/api/v1/documents/{document_id}/parse`
3. `/api/v1/documents/{document_id}/index`
4. `/api/v1/qa/ask`

示例问题：

- `如果我提前退租，会不会被扣押金？`
- `空调坏了谁负责维修？`
- `合同里有哪些风险？`

## 当前说明

- 如果未配置 `DEEPSEEK_API_KEY`，问答接口会自动退回到本地规则回答
- 如果本机未安装 `Tesseract`，图片 OCR 和扫描版 PDF OCR 会记录提示，但不会中断接口
- 当前向量化使用本地哈希 embedding，后续可以平滑替换为外部 embedding 模型
