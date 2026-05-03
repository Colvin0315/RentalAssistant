from __future__ import annotations


def choose_flow(question: str) -> str:
    normalized = question.lower()
    if any(keyword in normalized for keyword in ("话术", "帮我写", "沟通", "申请", "短信", "微信")):
        return "draft"
    if any(keyword in normalized for keyword in ("风险", "有没有坑", "不利", "注意")):
        return "risk"
    if any(keyword in normalized for keyword in ("缺什么", "还需要", "信息不足")):
        return "followup"
    return "qa"
