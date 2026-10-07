"""
Phase 3: discounted cash flow (DCF) intrinsic value model.

Goal: given a ticker's historical free cash flow and a small set of
user-adjustable assumptions, produce an intrinsic value per share and
show how sensitive that value is to the assumptions -- the sensitivity
table/chart is the actual teaching moment for anyone reviewing this repo,
not just the single-point estimate.

TODO (Phase 3):
- Pull historical free cash flow (FCF = operating cash flow - capex) from
  FMP's cash-flow-statement endpoint.
- Project FCF forward using `growth_rate` for `projection_years`, then a
  terminal value using the Gordon growth formula.
- Discount everything back at `discount_rate` (a WACC estimate -- start
  simple with a fixed assumption, revisit if there's time to estimate
  WACC per-company from beta + capital structure).
- Build a 2D sensitivity grid over (growth_rate, discount_rate).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DCFAssumptions:
    growth_rate: float = 0.08          # projected FCF growth, years 1..N
    terminal_growth_rate: float = 0.025  # perpetuity growth after year N
    discount_rate: float = 0.09        # WACC estimate
    projection_years: int = 5


def intrinsic_value_per_share(
    ticker: str,
    assumptions: DCFAssumptions,
) -> float:
    """Return an estimated intrinsic value per share for `ticker`.

    Stub -- Phase 3 will replace this with the real FCF projection +
    discounting described above. Returning 0.0 for now so callers (and
    the app shell) have a defined value to render.
    """
    raise NotImplementedError("DCF model lands in Phase 3")


def sensitivity_grid(
    ticker: str,
    base_assumptions: DCFAssumptions,
    growth_rates: list[float],
    discount_rates: list[float],
):
    """Return a DataFrame of intrinsic values across a grid of assumptions.

    Stub -- depends on intrinsic_value_per_share() above.
    """
    raise NotImplementedError("DCF sensitivity grid lands in Phase 3")
