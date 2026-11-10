"""Perceptual difference hashing (dHash) and near-duplicate shot detection."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import cv2
import numpy as np

from backend.api.schemas import MediaAsset


def compute_dhash_from_bgr(bgr: np.ndarray) -> str:
    """Compute a 64-bit perceptual difference hash (`dHash`) encoded as 16-char hex."""
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(gray, (9, 8), interpolation=cv2.INTER_AREA)
    diff = resized[:, 1:] > resized[:, :-1]
    bits = diff.flatten()
    value = 0
    for bit in bits:
        value = (value << 1) | int(bool(bit))
    return f"{value:016x}"


def compute_media_dhash(file_path: Path, is_image: bool = False) -> str:
    """Extract a representative frame (image or video midpoint) and compute its 64-bit dHash."""
    if is_image:
        bgr = cv2.imread(str(file_path))
        if bgr is None:
            return ""
        return compute_dhash_from_bgr(bgr)

    cap = cv2.VideoCapture(str(file_path))
    if not cap.isOpened():
        return ""
    try:
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        mid_idx = max(0, total // 2)
        cap.set(cv2.CAP_PROP_POS_FRAMES, mid_idx)
        ok, frame = cap.read()
        if not ok or frame is None:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok, frame = cap.read()
        return compute_dhash_from_bgr(frame) if (ok and frame is not None) else ""
    finally:
        cap.release()


def hamming_distance(hash_a: str, hash_b: str) -> int:
    """Compute bitwise Hamming distance between two 16-char hex hashes (0..64)."""
    if len(hash_a) != 16 or len(hash_b) != 16:
        return 64
    xor_val = int(hash_a, 16) ^ int(hash_b, 16)
    return xor_val.bit_count()


def find_best_duplicate_match(
    candidate_id: str,
    candidate_hash: str,
    existing_assets: list[MediaAsset],
    max_hamming_distance: int = 6,
) -> tuple[Optional[str], Optional[float]]:
    """Compare `candidate_hash` against analyzed assets and return `(duplicate_of_id, similarity_percent)`."""
    if not candidate_hash:
        return None, None

    best_id: Optional[str] = None
    best_dist = max_hamming_distance + 1

    for asset in existing_assets:
        if asset.id == candidate_id:
            continue
        if not asset.analysis or not asset.analysis.perceptual_hash:
            continue
        # Only point duplicates toward primary/non-duplicate originals when possible
        if asset.analysis.duplicate_of_id is not None:
            continue
        dist = hamming_distance(candidate_hash, asset.analysis.perceptual_hash)
        if dist < best_dist:
            best_dist = dist
            best_id = asset.id

    if best_id is None:
        return None, None

    similarity = round(((64 - best_dist) / 64.0) * 100.0, 1)
    return best_id, similarity
