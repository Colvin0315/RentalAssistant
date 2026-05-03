from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    document_id: str = Field(description="文档唯一标识。")
    filename: str = Field(description="原始文件名。")
    status: str = Field(description="当前文档状态。")


class ParseResponse(BaseModel):
    document_id: str = Field(description="文档唯一标识。")
    status: str = Field(description="解析状态。")
    chunk_count: int = Field(description="切分出的条款数量。")
    fields: dict[str, str] = Field(description="从合同中抽取的关键字段。")


class IndexResponse(BaseModel):
    document_id: str = Field(description="文档唯一标识。")
    status: str = Field(description="索引构建状态。")


class Citation(BaseModel):
    chunk_id: str = Field(description="被引用的条款 ID。")
    text: str = Field(description="条款原文片段。")


class RiskFlag(BaseModel):
    title: str = Field(description="风险标题。")
    severity: Literal["low", "medium", "high"] = Field(description="风险等级。")


class AskRequest(BaseModel):
    document_id: str = Field(description="要提问的文档 ID。")
    question: str = Field(min_length=2, description="用户的自然语言问题。")


class AskResponse(BaseModel):
    answer: str = Field(description="基于合同证据生成的回答。")
    citations: list[Citation] = Field(description="支撑回答的条款引用。")
    risk_flags: list[RiskFlag] = Field(description="识别到的重点风险提示。")
    needs_followup: bool = Field(description="是否需要继续补充信息。")
    session_id: str = Field(description="本次问答会话 ID，可用于查询日志。")


class RiskItem(BaseModel):
    risk_id: str = Field(description="风险规则 ID。")
    title: str = Field(description="风险标题。")
    severity: Literal["low", "medium", "high"] = Field(description="风险等级。")
    clause_id: str = Field(description="命中的条款 ID。")
    explanation: str = Field(description="风险解释。")


class RiskAnalyzeRequest(BaseModel):
    document_id: str = Field(description="要分析风险的文档 ID。")


class RiskAnalyzeResponse(BaseModel):
    document_id: str = Field(description="文档唯一标识。")
    risks: list[RiskItem] = Field(description="识别到的风险列表。")


class DraftRequest(BaseModel):
    document_id: str = Field(description="文档唯一标识。")
    scenario: Literal["deposit_refund", "early_termination", "repair_request"] = Field(
        description="话术场景：押金退还、提前退租协商、维修责任确认。"
    )
    tone: Literal["polite", "firm", "neutral"] = Field(
        default="polite",
        description="话术语气：礼貌、坚定或中性。",
    )


class DraftResponse(BaseModel):
    draft: str = Field(description="生成的沟通草稿。")


class EvalRequest(BaseModel):
    dataset_name: str = Field(description="评测集名称。")
    document_id: str = Field(description="参与评测的文档 ID。")


class EvalResponse(BaseModel):
    dataset_name: str = Field(description="评测集名称。")
    metrics: dict[str, float] = Field(description="输出的评测指标。")


class SessionEvent(BaseModel):
    type: str = Field(description="事件类型。")
    data: dict[str, Any] = Field(description="事件详情。")


class SessionLogResponse(BaseModel):
    session_id: str = Field(description="问答会话 ID。")
    events: list[SessionEvent] = Field(description="按时间顺序记录的事件列表。")
