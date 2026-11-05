import numpy as np
import pandas as pd
import pytest

from cleaning.missing_values import MissingValueHandler


@pytest.fixture
def df():
    # 'a' has a leading NaN that ffill cannot reach; 'b' is fully fillable by ffill.
    return pd.DataFrame({"a": [np.nan, 2.0, np.nan, 4.0], "b": [1.0, np.nan, 3.0, np.nan]})


def test_all_selected_strategies_are_applied(df):
    # Regression: previously only strategies[0] ran. ffill leaves a[0] NaN; mean must fill it.
    out = MissingValueHandler().handle_many(df, ["forward_fill", "mean"])
    assert out.isna().sum().sum() == 0
    assert out.loc[0, "a"] == pytest.approx(8.0 / 3)  # mean of [2, 2, 4] after ffill


def test_order_is_fixed_not_selection_order(df):
    h = MissingValueHandler()
    assert h.handle_many(df, ["drop", "forward_fill"]).equals(h.handle_many(df, ["forward_fill", "drop"]))
    # drop runs last, so ffill rescues rows: only row 0 (a=NaN before any value) is dropped.
    assert len(h.handle_many(df, ["drop", "forward_fill"])) == 3


def test_ffill_bfill_work_on_installed_pandas(df):
    h = MissingValueHandler()
    assert h.handle(df, "forward_fill").loc[1, "b"] == 1.0
    assert h.handle(df, "backward_fill").loc[0, "a"] == 2.0


def test_unknown_strategy_rejected(df):
    with pytest.raises(ValueError):
        MissingValueHandler().handle_many(df, ["mean", "bogus"])


def test_input_not_mutated(df):
    before = df.copy()
    MissingValueHandler().handle_many(df, ["mean", "drop"])
    assert df.equals(before)
