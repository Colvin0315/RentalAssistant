from __future__ import annotations

import hashlib
import re
from typing import Any

from ..config import VECTOR_DIMENSION
from ..storage import faiss_index_path, index_path, read_json, write_json

STOPWORDS = {"如果", "是否", "什么", "怎么", "一下", "一下子", "一下吗", "这个", "那个", "请问", "合同", "里面"}
DOMAIN_TERMS = [
    "押金",
    "退押金",
    "提前退租",
    "退租",
    "解约",
    "违约",
    "违约金",
    "维修",
    "修缮",
    "空调",
    "热水器",
    "房东",
    "租金",
    "物业费",
    "管理费",
    "续租",
]


def build_index(chunks: list[dict[str, str]]) -> dict[str, object]:
    indexed_chunks: list[dict[str, object]] = []
    vectors: list[list[float]] = []
    for chunk in chunks:
        vector = embed_text(chunk["text"])
        tokens = tokenize(chunk["text"])
        indexed_chunks.append(
            {
                "chunk_id": chunk["chunk_id"],
                "title": chunk["title"],
                "text": chunk["text"],
                "keywords": sorted(set(tokens)),
            }
        )
        vectors.append(vector)
    return {
        "chunks": indexed_chunks,
        "dimension": VECTOR_DIMENSION,
        "count": len(indexed_chunks),
        "vectors": vectors,
    }


def retrieve(index_data: dict[str, object], question: str, top_k: int = 3) -> list[dict[str, object]]:
    chunks = index_data.get("chunks", [])
    if not chunks:
        return []

    query_vector = embed_text(question)
    try:
        import faiss  # type: ignore
        import numpy as np  # type: ignore

        vectors = np.asarray(index_data.get("vectors", []), dtype="float32")
        if len(vectors) == 0:
            return []
        query_array = np.asarray([query_vector], dtype="float32")
        faiss.normalize_L2(vectors)
        faiss.normalize_L2(query_array)
        index = faiss.IndexFlatIP(vectors.shape[1])
        index.add(vectors)
        _, indices = index.search(query_array, min(top_k, len(chunks)))
        return [chunks[idx] for idx in indices[0] if idx >= 0]
    except Exception:
        scored: list[tuple[float, dict[str, object]]] = []
        question_tokens = set(tokenize(question))
        matched_terms = [term for term in DOMAIN_TERMS if term in question]
        for idx, chunk in enumerate(chunks):
            chunk_vector = index_data.get("vectors", [])[idx] if idx < len(index_data.get("vectors", [])) else []
            similarity = cosine_similarity(query_vector, chunk_vector)
            keyword_bonus = len(question_tokens.intersection(chunk.get("keywords", []))) * 0.08
            term_bonus = sum((len(term) / 2.0) for term in matched_terms if term in chunk.get("text", ""))
            score = similarity + keyword_bonus + term_bonus
            scored.append((score, chunk))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [chunk for _, chunk in scored[:top_k]]


def write_faiss_bundle(document_id: str, index_data: dict[str, Any]) -> None:
    metadata = {
        "chunks": index_data["chunks"],
        "dimension": index_data["dimension"],
        "count": index_data["count"],
    }
    write_json(index_path(document_id), metadata)

    try:
        import faiss  # type: ignore
        import numpy as np  # type: ignore

        vectors = np.asarray(index_data.get("vectors", []), dtype="float32")
        if len(vectors) == 0:
            return
        faiss.normalize_L2(vectors)
        index = faiss.IndexFlatIP(vectors.shape[1])
        index.add(vectors)
        faiss.write_index(index, str(faiss_index_path(document_id)))
    except Exception:
        metadata["vectors"] = index_data.get("vectors", [])
        write_json(index_path(document_id), metadata)


def load_index_bundle(document_id: str) -> dict[str, Any]:
    metadata = read_json(index_path(document_id))
    if "vectors" in metadata:
        return metadata

    try:
        import faiss  # type: ignore
        import numpy as np  # type: ignore

        index = faiss.read_index(str(faiss_index_path(document_id)))
        vectors = np.zeros((index.ntotal, index.d), dtype="float32")
        for i in range(index.ntotal):
            vectors[i] = index.reconstruct(i)
        metadata["vectors"] = vectors.tolist()
        return metadata
    except Exception:
        metadata["vectors"] = []
        return metadata


def tokenize(text: str) -> list[str]:
    ascii_words = re.findall(r"[A-Za-z0-9_]+", text.lower())
    chinese = re.sub(r"[^\u4e00-\u9fff]", "", text)
    bigrams = [chinese[i : i + 2] for i in range(max(len(chinese) - 1, 0))]
    unigrams = [char for char in chinese if char.strip()]
    tokens = ascii_words + bigrams + unigrams
    return [token for token in tokens if token and token not in STOPWORDS]


def embed_text(text: str) -> list[float]:
    vector = [0.0] * VECTOR_DIMENSION
    for token in tokenize(text):
        slot = _stable_hash(token) % VECTOR_DIMENSION
        sign = 1.0 if (_stable_hash(f"{token}:sign") % 2 == 0) else -1.0
        weight = 1.0 + min(len(token), 6) / 10.0
        vector[slot] += sign * weight
    norm = sum(value * value for value in vector) ** 0.5
    if norm > 0:
        vector = [value / norm for value in vector]
    return vector


def _stable_hash(value: str) -> int:
    return int(hashlib.md5(value.encode("utf-8")).hexdigest(), 16)


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    return sum(lv * rv for lv, rv in zip(left, right))
