from __future__ import annotations

from pathlib import Path as FilePath

from fastapi import FastAPI, File, Form, HTTPException, Path as ApiPath, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .config import API_PREFIX
from .db import init_db
from .repository import (
    get_document,
    get_session_events,
    insert_document,
    insert_session,
    insert_session_event,
    update_document_status,
)
from .schemas import (
    AskRequest,
    AskResponse,
    Citation,
    DraftRequest,
    DraftResponse,
    EvalRequest,
    EvalResponse,
    IndexResponse,
    ParseResponse,
    RiskAnalyzeRequest,
    RiskAnalyzeResponse,
    RiskFlag,
    RiskItem,
    SessionEvent,
    SessionLogResponse,
    UploadResponse,
)
from .services.agent_service import choose_flow
from .services.draft_service import generate_draft
from .services.eval_service import run_eval
from .services.llm_service import generate_answer
from .services.parser_service import parse_document
from .services.retrieval_service import build_index, load_index_bundle, retrieve, write_faiss_bundle
from .services.risk_service import analyze_risks
from .storage import index_path, new_id, parsed_path, read_json, save_upload, write_json

app = FastAPI(
    title="RentGuard 后端演示服务",
    version="0.1.0",
    summary="面向租房合同场景的后端 Demo",
    description=(
        "这是一个用于本地联调和功能演示的 RentGuard 后端服务。"
        "当前版本覆盖文档上传、合同解析、索引构建、合同问答、风险识别、沟通话术生成、评测和会话日志查询。"
    ),
)

# Allow a separately hosted local frontend to call the demo API during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


def require_document(document_id: str) -> dict[str, str]:
    doc = get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@app.get(
    "/",
    tags=["系统"],
    summary="健康检查",
    description="用于确认后端服务已经成功启动。",
)
def health() -> dict[str, str]:
    return {"message": "RentGuard 后端演示服务运行中"}


@app.post(
    f"{API_PREFIX}/documents/upload",
    response_model=UploadResponse,
    tags=["文档"],
    summary="上传文档",
    description="上传租房合同或相关材料，支持作为后续解析和问答的输入。",
)
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form("contract", description="文档类型，如 contract、chatlog、listing。"),
) -> UploadResponse:
    document_id = new_id("doc")
    stored = save_upload(document_id, file)
    insert_document(
        document_id=document_id,
        filename=file.filename or stored.name,
        document_type=document_type,
        stored_path=str(stored),
        status="uploaded",
    )
    return UploadResponse(document_id=document_id, filename=file.filename or stored.name, status="uploaded")


@app.post(
    f"{API_PREFIX}/documents/{{document_id}}/parse",
    response_model=ParseResponse,
    tags=["文档"],
    summary="解析文档",
    description="从已上传文档中提取正文，切分条款，并抽取关键信息字段。",
)
def parse_uploaded_document(
    document_id: str = ApiPath(..., description="上传接口返回的文档 ID。"),
) -> ParseResponse:
    doc = require_document(document_id)
    payload = parse_document(FilePath(doc["stored_path"]))
    write_json(parsed_path(document_id), payload)
    update_document_status(document_id, "parsed")
    return ParseResponse(
        document_id=document_id,
        status="parsed",
        chunk_count=len(payload["chunks"]),
        fields=payload["fields"],
    )


@app.post(
    f"{API_PREFIX}/documents/{{document_id}}/index",
    response_model=IndexResponse,
    tags=["文档"],
    summary="构建索引",
    description="根据解析结果生成检索索引，供问答和风险分析使用。",
)
def build_document_index(
    document_id: str = ApiPath(..., description="已完成解析的文档 ID。"),
) -> IndexResponse:
    require_document(document_id)
    parsed_file = parsed_path(document_id)
    if not parsed_file.exists():
        raise HTTPException(status_code=400, detail="Document must be parsed before indexing")
    parsed = read_json(parsed_file)
    index_data = build_index(parsed["chunks"])
    write_faiss_bundle(document_id, index_data)
    update_document_status(document_id, "indexed")
    return IndexResponse(document_id=document_id, status="indexed")


@app.post(
    f"{API_PREFIX}/qa/ask",
    response_model=AskResponse,
    tags=["问答"],
    summary="合同问答",
    description="围绕指定合同提问，返回回答、引用条款、风险提示和会话 ID。",
)
def ask_question(request: AskRequest) -> AskResponse:
    require_document(request.document_id)
    parsed_file = parsed_path(request.document_id)
    indexed_file = index_path(request.document_id)
    if not parsed_file.exists() or not indexed_file.exists():
        raise HTTPException(status_code=400, detail="Document must be parsed and indexed before QA")

    parsed = read_json(parsed_file)
    indexed = load_index_bundle(request.document_id)
    top_chunks = retrieve(indexed, request.question, top_k=3)
    flow = choose_flow(request.question)
    risks = analyze_risks(parsed["chunks"])

    citations = [
        Citation(chunk_id=chunk["chunk_id"], text=chunk["text"][:180])
        for chunk in top_chunks
    ]

    needs_followup = not bool(top_chunks)
    if flow == "followup" or needs_followup:
        answer = "当前证据不足，我还不能直接下结论。建议补充完整合同页、押金约定和解约条款后再判断。"
    else:
        try:
            answer = generate_answer(request.question, top_chunks, risks)
        except Exception:
            answer = compose_answer(request.question, top_chunks, risks)

    session_id = new_id("sess")
    insert_session(session_id, request.document_id, request.question, answer)
    insert_session_event(
        session_id,
        "retrieval",
        {"chunks": [chunk["chunk_id"] for chunk in top_chunks], "flow": flow},
    )
    insert_session_event(
        session_id,
        "answer",
        {"text": answer},
    )

    return AskResponse(
        answer=answer,
        citations=citations,
        risk_flags=[RiskFlag(title=item["title"], severity=item["severity"]) for item in risks[:3]],
        needs_followup=needs_followup,
        session_id=session_id,
    )


@app.post(
    f"{API_PREFIX}/risk/analyze",
    response_model=RiskAnalyzeResponse,
    tags=["风险"],
    summary="分析合同风险",
    description="扫描合同条款并返回命中的常见租房风险项。",
)
def analyze_document_risk(request: RiskAnalyzeRequest) -> RiskAnalyzeResponse:
    require_document(request.document_id)
    parsed_file = parsed_path(request.document_id)
    if not parsed_file.exists():
        raise HTTPException(status_code=400, detail="Document must be parsed before risk analysis")

    parsed = read_json(parsed_file)
    risks = analyze_risks(parsed["chunks"])
    return RiskAnalyzeResponse(
        document_id=request.document_id,
        risks=[RiskItem(**risk) for risk in risks],
    )


@app.post(
    f"{API_PREFIX}/drafts/generate",
    response_model=DraftResponse,
    tags=["话术"],
    summary="生成沟通话术",
    description="基于合同内容生成面向房东或中介的沟通草稿。",
)
def create_draft(request: DraftRequest) -> DraftResponse:
    require_document(request.document_id)
    parsed_file = parsed_path(request.document_id)
    if not parsed_file.exists():
        raise HTTPException(status_code=400, detail="Document must be parsed before draft generation")

    parsed = read_json(parsed_file)
    citations = parsed["chunks"][:1]
    draft = generate_draft(request.scenario, request.tone, parsed["fields"], citations)
    return DraftResponse(draft=draft)


@app.post(
    f"{API_PREFIX}/eval/run",
    response_model=EvalResponse,
    tags=["评测"],
    summary="运行评测",
    description="基于解析结果输出一组演示用评测指标。",
)
def run_document_eval(request: EvalRequest) -> EvalResponse:
    require_document(request.document_id)
    parsed_file = parsed_path(request.document_id)
    if not parsed_file.exists():
        raise HTTPException(status_code=400, detail="Document must be parsed before eval")

    parsed = read_json(parsed_file)
    risks = analyze_risks(parsed["chunks"])
    metrics = run_eval(
        document_id=request.document_id,
        dataset_name=request.dataset_name,
        chunk_count=len(parsed["chunks"]),
        risk_count=len(risks),
    )
    return EvalResponse(dataset_name=request.dataset_name, metrics=metrics)


@app.get(
    f"{API_PREFIX}/sessions/{{session_id}}/logs",
    response_model=SessionLogResponse,
    tags=["日志"],
    summary="查看会话日志",
    description="查询一次问答流程中的检索和回答事件。",
)
def get_session_logs(
    session_id: str = ApiPath(..., description="问答接口返回的会话 ID。"),
) -> SessionLogResponse:
    events = [SessionEvent(**event) for event in get_session_events(session_id)]
    if not events:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionLogResponse(session_id=session_id, events=events)


def compose_answer(question: str, chunks: list[dict[str, object]], risks: list[dict[str, str]]) -> str:
    if not chunks:
        return "我暂时没有检索到足够相关的合同条款，无法可靠回答这个问题。"

    evidence = "；".join(str(chunk["text"])[:80] for chunk in chunks[:2])
    risk_hint = f"。另外，这份合同存在“{risks[0]['title']}”风险" if risks else ""

    if "押金" in question:
        return f"从合同原文看，和押金最相关的条款是：{evidence}。是否能扣押金，取决于这些条款是否明确写了扣除条件、违约场景和交接标准{risk_hint}。"
    if "提前退租" in question or "解约" in question:
        return f"合同中关于提前退租/解约的证据是：{evidence}。这意味着你需要重点确认是否约定了通知期限、违约金和押金处理方式{risk_hint}。"
    if "维修" in question or "修" in question:
        return f"合同中与维修责任最相关的内容是：{evidence}。建议区分房屋主体故障、设备自然损耗和租客使用不当三类责任{risk_hint}。"
    return f"根据检索到的合同条款，相关证据包括：{evidence}。目前的结论应优先以合同原文约定为准{risk_hint}。"
