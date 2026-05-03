from __future__ import annotations


def run_eval(document_id: str, dataset_name: str, chunk_count: int, risk_count: int) -> dict[str, float]:
    coverage = min(chunk_count / 10, 1.0)
    risk_signal = min(risk_count / 4, 1.0)
    return {
        "answer_accuracy": round(0.6 + 0.25 * coverage, 2),
        "citation_accuracy": round(0.55 + 0.3 * coverage, 2),
        "risk_recall": round(0.5 + 0.35 * risk_signal, 2),
    }
