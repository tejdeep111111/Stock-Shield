from __future__ import annotations


def optimize_recommendation(strategies: list[dict], budget: float) -> dict:
    feasible = [s for s in strategies if s["cost"] <= budget]
    if not feasible:
        return {
            "recommended_action": "No feasible action within budget",
            "expected_revenue_protected": 0.0,
            "intervention_cost": 0.0,
            "net_value": 0.0,
            "confidence": 0.5,
            "reasoning": ["Budget constraint prevents intervention"],
        }

    try:
        from ortools.linear_solver import pywraplp  # type: ignore

        solver = pywraplp.Solver.CreateSolver("SCIP")
        if solver is None:
            raise RuntimeError("solver unavailable")
        vars_ = [solver.BoolVar(f"x_{idx}") for idx, _ in enumerate(feasible)]
        solver.Add(sum(v * s["cost"] for v, s in zip(vars_, feasible)) <= budget)
        solver.Add(sum(vars_) == 1)
        solver.Maximize(sum(v * s["net_value"] for v, s in zip(vars_, feasible)))
        status = solver.Solve()
        if status != pywraplp.Solver.OPTIMAL:
            raise RuntimeError("non optimal")
        chosen_idx = max(range(len(feasible)), key=lambda i: vars_[i].solution_value())
        chosen = feasible[chosen_idx]
    except Exception:
        chosen = max(feasible, key=lambda s: (s["net_value"], s["revenue_protected"]))

    return {
        "recommended_action": chosen["strategy"],
        "expected_revenue_protected": chosen["revenue_protected"],
        "intervention_cost": chosen["cost"],
        "net_value": chosen["net_value"],
        "confidence": min(0.99, 0.65 + (chosen["success_probability"] * 0.3)),
        "reasoning": [
            "Selected action maximizes expected net revenue protection",
            f"Arrival in {chosen['arrival_days']} day(s) with {chosen['success_probability']:.0%} success chance",
            f"Budget considered: {budget:.0f}",
        ],
    }
