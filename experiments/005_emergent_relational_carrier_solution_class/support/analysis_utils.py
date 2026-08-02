#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Mapping-free response geometry used by Experiment 005."""

from __future__ import annotations

import numpy as np


OPERATORS = ("delete", "exchange", "sign_flip", "compose", "temporal_reverse")


def response_coordinates(response: np.ndarray) -> np.ndarray:
    """Drop one redundant probability coordinate from each receiver."""
    if response.ndim != 3 or response.shape[1:] != (2, 3):
        raise ValueError(f"unexpected response shape: {response.shape}")
    if float(np.max(np.abs(response.sum(axis=2)))) > 1e-10:
        raise AssertionError("probability response does not sum to zero")
    return np.concatenate((response[:, 0, :2], response[:, 1, :2]), axis=1)


def field_matrix(fields: dict[str, np.ndarray]) -> np.ndarray:
    return np.concatenate(
        [response_coordinates(fields[operator]) for operator in OPERATORS],
        axis=1,
    )


def centered(matrix: np.ndarray) -> np.ndarray:
    return matrix - matrix.mean(axis=0, keepdims=True)


def linear_cka(left: np.ndarray, right: np.ndarray) -> float:
    x = centered(left)
    y = centered(right)
    cross = x.T @ y
    numerator = float(np.sum(cross * cross))
    left_norm = float(np.sqrt(np.sum((x.T @ x) ** 2)))
    right_norm = float(np.sqrt(np.sum((y.T @ y) ** 2)))
    denominator = left_norm * right_norm
    return 0.0 if denominator <= 1e-15 else numerator / denominator


def summarize(values: list[float]) -> dict[str, float]:
    return {
        "minimum": float(min(values)),
        "median": float(np.median(values)),
        "maximum": float(max(values)),
    }
