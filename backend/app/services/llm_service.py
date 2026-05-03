from __future__ import annotations

from typing import Any

from ..config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL, DEEPSEEK_TIMEOUT


SYSTEM_PROMPT = """
你是 RentGuard 的合同问答助手。
你的目标是基于给定合同条款回答用户问题，严格区分“合同原文事实”和“建议”。
如果证据不足，明确说“不确定”或“无法判断”。
输出要求：
1. 先给出简洁结论。
2. 再说明依据的合同条款。
3. 如有风险，补一句风险提醒。
""".strip()


def generate_answer(question: str, chunks: list[dict[str, Any]], risks: list[dict[str, str]]) -> str:
    if not DEEPSEEK_API_KEY:
        raise RuntimeError("DEEPSEEK_API_KEY is not configured")

    from openai import OpenAI

    client = OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL,
        timeout=DEEPSEEK_TIMEOUT,
    )

    evidence = "\n\n".join(
        f"[{chunk['chunk_id']}] {chunk['text']}" for chunk in chunks
    )
    risk_lines = "\n".join(
        f"- {risk['title']}（{risk['severity']}）" for risk in risks[:5]
    ) or "无明显风险提示。"

    user_prompt = f"""
用户问题：
{question}

合同证据：
{evidence}

风险提示：
{risk_lines}
""".strip()

    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        temperature=0.2,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )
    return (response.choices[0].message.content or "").strip()
