from typing import List, Dict, Any

def compute_batch_scoring_and_ranking(
    evaluated_suppliers: List[Dict[str, Any]],
    active_criteria: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Computes absolute weighted scores, criterion benchmarks, gaps, relative percentages,
    weighted Peer Performance Index (PPI), and stable 4-stage tie-breaker ranking.
    """
    if not evaluated_suppliers or not active_criteria:
        return []

    # Map criteria weights and max_scores for fast lookup
    criteria_meta = {c["criterion_id"]: c for c in active_criteria}
    total_active_weight = sum(c["weight"] for c in active_criteria)

    # 1. Calculate Absolute Weighted Score per supplier
    for supp in evaluated_suppliers:
        abs_score = 0.0
        c_map = {c["criterion_id"]: c for c in supp["criteria"]}
        
        for cid, meta in criteria_meta.items():
            sc_item = c_map.get(cid, {"score": 0.0, "max_score": meta["max_score"]})
            score_val = float(sc_item["score"])
            max_s = float(meta["max_score"])
            weight = float(meta["weight"])
            
            if max_s > 0:
                abs_score += (score_val / max_s) * weight
                
        supp["absolute_score"] = round(abs_score, 4)

    # 2. Compute Criterion Benchmark across all suppliers in batch
    benchmarks = {}
    for cid in criteria_meta:
        max_obs = 0.0
        for supp in evaluated_suppliers:
            c_map = {c["criterion_id"]: c for c in supp["criteria"]}
            sc_val = float(c_map.get(cid, {}).get("score", 0.0))
            if sc_val > max_obs:
                max_obs = sc_val
        benchmarks[cid] = max_obs

    # 3. Compute Criterion Gap, Relative %, and PPI per supplier
    for supp in evaluated_suppliers:
        c_map = {c["criterion_id"]: c for c in supp["criteria"]}
        detailed_scorecard = []
        weighted_rel_sum = 0.0

        for cid, meta in criteria_meta.items():
            sc_item = c_map.get(cid, {"score": 0.0, "max_score": meta["max_score"], "justification": "", "evidence": ""})
            score_val = float(sc_item["score"])
            bench_val = float(benchmarks[cid])
            weight = float(meta["weight"])

            # Criterion Gap = score - benchmark score
            gap = round(score_val - bench_val, 4)

            # Relative Performance % = (score / benchmark) * 100
            if bench_val > 0:
                rel_pct = round((score_val / bench_val) * 100.0, 4)
            else:
                rel_pct = 100.0 if score_val == 0 else 0.0

            # Accumulate PPI weighted average
            if total_active_weight > 0:
                weighted_rel_sum += rel_pct * (weight / total_active_weight)

            detailed_scorecard.append({
                "criterion_id": cid,
                "criterion_name": meta["name"],
                "score": score_val,
                "max_score": meta["max_score"],
                "weight": weight,
                "benchmark": bench_val,
                "gap": gap,
                "relative_pct": rel_pct,
                "justification": sc_item.get("justification", ""),
                "evidence": sc_item.get("evidence", "")
            })

        supp["scorecard"] = detailed_scorecard
        supp["ppi"] = round(weighted_rel_sum, 4)

    # 4. Mandatory Tie-Break Order:
    # Sort Key:
    # 1) Higher PPI first -> -ppi
    # 2) Earlier submission date -> submission_date ascending
    # 3) Higher historical experience rating -> -experience_rating
    # 4) Supplier name ascending -> supplier_name.lower()
    def tie_break_key(s: Dict[str, Any]):
        return (
            -float(s["ppi"]),
            str(s.get("submission_date", "9999-99-99")),
            -float(s.get("experience_rating", 0.0)),
            str(s["supplier_name"]).lower()
        )

    ranked_suppliers = sorted(evaluated_suppliers, key=tie_break_key)

    # 5. Assign sequential ranks (1, 2, 3...) & tie-break explanation string
    for idx, supp in enumerate(ranked_suppliers, start=1):
        supp["final_rank"] = idx
        supp["tie_break_info"] = (
            f"Rank #{idx} | PPI: {supp['ppi']:.2f}% | "
            f"Submitted: {supp.get('submission_date', 'N/A')} | "
            f"Exp Rating: {supp.get('experience_rating', 0.0)} | "
            f"Supplier: {supp['supplier_name']}"
        )

    return ranked_suppliers
