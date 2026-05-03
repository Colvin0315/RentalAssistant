from __future__ import annotations


SCENARIO_LABELS = {
    "deposit_refund": "押金退还",
    "early_termination": "提前退租协商",
    "repair_request": "维修责任确认",
}


TONE_PREFIX = {
    "polite": "您好，",
    "neutral": "关于本次租赁事宜，",
    "firm": "我想就合同履行情况正式说明，",
}


def generate_draft(scenario: str, tone: str, fields: dict[str, str], citations: list[dict[str, str]]) -> str:
    intro = TONE_PREFIX[tone]
    evidence = citations[0]["text"] if citations else "根据双方签署的租房合同约定"
    rent = fields.get("rent", "合同约定租金")
    deposit = fields.get("deposit", "合同约定押金")

    if scenario == "deposit_refund":
        return (
            f"{intro}根据合同内容，关于押金退还的相关约定为：{evidence}。"
            f"目前我已按约履行交接义务，请您按合同尽快办理 {deposit} 的退还。谢谢配合。"
        )

    if scenario == "early_termination":
        return (
            f"{intro}我想就提前退租事宜与您协商。合同中与解约相关的表述是：{evidence}。"
            f"我希望在不影响房屋再次出租的前提下，协商一个合理的退租方案，并妥善结清包括 {rent} 在内的应付款项。"
        )

    return (
        f"{intro}关于房屋维修责任，合同相关表述为：{evidence}。"
        "当前问题已经影响正常居住，烦请确认维修安排、责任归属和预计处理时间。"
    )
