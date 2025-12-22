"""
Thresholds Module - Automatic threshold calculation utilities
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Iterable, List

import numpy as np
import pandas as pd


@dataclass
class ThresholdConfig:
    """Configuration for threshold calculation."""
    method: str = "zscore"          # "zscore" | "iqr" | "percentile"
    zscore_limit: float = 3.0       # for z-score
    iqr_factor: float = 1.5         # for IQR fences
    lower_percentile: float = 1.0   # for percentile method
    upper_percentile: float = 99.0


class ThresholdCalculator:
    """
    Compute numeric thresholds for outliers / alerts on numeric columns.

    Methods:
        - zscore: mean ± zscore_limit * std
        - iqr:    Q1 - factor*IQR, Q3 + factor*IQR
        - percentile: fixed lower/upper percentiles
    """

    def __init__(self, config: Optional[ThresholdConfig] = None):
        self.config = config or ThresholdConfig()

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def calculate_for_series(
        self,
        s: pd.Series,
        method: Optional[str] = None,
    ) -> Dict[str, float]:
        """
        Calculate lower/upper threshold for a numeric series.

        Returns:
            {"lower": float, "upper": float}
        """
        s = pd.to_numeric(s.dropna(), errors="coerce").dropna()
        if s.empty:
            return {"lower": np.nan, "upper": np.nan}

        method = (method or self.config.method).lower()

        if method == "zscore":
            return self._zscore_threshold(s)
        if method == "iqr":
            return self._iqr_threshold(s)
        if method == "percentile":
            return self._percentile_threshold(s)

        raise ValueError(f"Unsupported threshold method: {method}")

    def calculate_for_dataframe(
        self,
        df: pd.DataFrame,
        columns: Optional[Iterable[str]] = None,
        method: Optional[str] = None,
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate thresholds for multiple numeric columns.

        Returns:
            {
                "col1": {"lower": ..., "upper": ...},
                "col2": {"lower": ..., "upper": ...},
                ...
            }
        """
        cols: List[str] = (
            list(columns)
            if columns is not None
            else df.select_dtypes("number").columns.tolist()
        )
        result: Dict[str, Dict[str, float]] = {}

        for col in cols:
            if col not in df.columns:
                continue
            result[col] = self.calculate_for_series(df[col], method=method)

        return result

    # ------------------------------------------------------------------ #
    # Internal methods
    # ------------------------------------------------------------------ #

    def _zscore_threshold(self, s: pd.Series) -> Dict[str, float]:
        mean = s.mean()
        std = s.std(ddof=0)
        limit = self.config.zscore_limit
        return {"lower": mean - limit * std, "upper": mean + limit * std}

    def _iqr_threshold(self, s: pd.Series) -> Dict[str, float]:
        q1 = s.quantile(0.25)
        q3 = s.quantile(0.75)
        iqr = q3 - q1
        k = self.config.iqr_factor
        return {"lower": q1 - k * iqr, "upper": q3 + k * iqr}

    def _percentile_threshold(self, s: pd.Series) -> Dict[str, float]:
        lp = self.config.lower_percentile / 100.0
        up = self.config.upper_percentile / 100.0
        return {"lower": s.quantile(lp), "upper": s.quantile(up)}
