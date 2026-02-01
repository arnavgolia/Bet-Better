"""
Copula-based correlation modeling for SGP simulation.

This package contains the core mathematical engine:
- simulation.py: JAX Student-t Copula implementation
- regime.py: Game script detection and parameter adjustment
"""

from app.services.copula.simulation import (
    simulate_parlay_t_copula,
    SimulationResult,
    benchmark_simulation,
)
from app.services.copula.regime import (
    detect_game_regime,
    GameRegime,
    RegimeParameters,
    apply_regime_to_correlation_matrix,
)

__all__ = [
    "simulate_parlay_t_copula",
    "SimulationResult",
    "benchmark_simulation",
    "detect_game_regime",
    "GameRegime",
    "RegimeParameters",
    "apply_regime_to_correlation_matrix",
]
