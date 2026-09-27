class ExplainableAIAgent:
    def explain(self, opportunity: dict) -> str:
        factors = []
        if opportunity.get("demand_score", 0) > 0.6:
            factors.append(f"High market demand ({opportunity['demand_score']:.2f})")
        if opportunity.get("research_gap_score", 0) > 0.5:
            factors.append(f"Significant research gap ({opportunity['research_gap_score']:.2f})")
        if opportunity.get("trend_score", 0) > 0.5:
            factors.append(f"Strong technology trend ({opportunity['trend_score']:.2f})")
        if opportunity.get("feasibility_score", 0) > 0.6:
            factors.append(f"Good technical feasibility ({opportunity['feasibility_score']:.2f})")

        return (
            f"This opportunity scored {opportunity.get('opportunity_score', 0):.2f}. "
            f"Contributing factors: {'; '.join(factors) if factors else 'Multiple moderate signals'}. "
            f"Confidence: {opportunity.get('confidence_score', 0):.2f}."
        )
