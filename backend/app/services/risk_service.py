from __future__ import annotations

from typing import Iterable


RISK_RULES = [
    {
        "risk_id": "risk_01",
        "title": "押金退还条件不明确",
        "severity": "high",
        "patterns": ["押金不退", "扣除押金", "押金作为违约金", "押金不予退还"],
        "explanation": "合同提到押金可能被扣或不退，但没有写清适用条件、计算标准或争议认定方式。",
    },
    {
        "risk_id": "risk_02",
        "title": "提前解约处罚较重",
        "severity": "high",
        "patterns": ["提前解除合同", "提前退租", "违约金", "双倍租金"],
        "explanation": "合同对提前退租设置了较重处罚，签约前需要重点确认是否可协商。",
    },
    {
        "risk_id": "risk_03",
        "title": "房东单方权利过大",
        "severity": "medium",
        "patterns": ["甲方有权单方", "房东有权单方", "无需乙方同意"],
        "explanation": "存在房东单方决定的重要条款，可能导致租客权利失衡。",
    },
    {
        "risk_id": "risk_04",
        "title": "隐性费用风险",
        "severity": "medium",
        "patterns": ["服务费", "管理费", "卫生费", "额外费用"],
        "explanation": "合同出现了除租金和押金外的额外收费字段，需要确认收费标准和支付条件。",
    },
    {
        "risk_id": "risk_05",
        "title": "自动续租陷阱",
        "severity": "medium",
        "patterns": ["自动续租", "视为续租", "默认续签"],
        "explanation": "合同存在自动续租约定，若未及时通知可能被视为继续履约。",
    },
    {
        "risk_id": "risk_06",
        "title": "维修责任过度转嫁给租客",
        "severity": "high",
        "patterns": ["所有维修由乙方承担", "一切维修费用由租客承担", "维修责任均由乙方承担"],
        "explanation": "合同将维修义务大范围转给租客，可能超出正常居住损耗责任范围。",
    },
]


def analyze_risks(chunks: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    risks: list[dict[str, str]] = []
    for chunk in chunks:
        text = chunk["text"]
        for rule in RISK_RULES:
            if any(pattern in text for pattern in rule["patterns"]):
                risks.append(
                    {
                        "risk_id": rule["risk_id"],
                        "title": rule["title"],
                        "severity": rule["severity"],
                        "clause_id": chunk["chunk_id"],
                        "explanation": rule["explanation"],
                    }
                )
    return _dedupe(risks)


def _dedupe(items: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    result: list[dict[str, str]] = []
    for item in items:
        key = (item["risk_id"], item["clause_id"])
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result
