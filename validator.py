from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Any, Optional

class CriterionScoreModel(BaseModel):
    criterion_id: int
    score: float
    max_score: float = 10.0
    justification: str = ""
    evidence: str = ""

class EvaluationOutputModel(BaseModel):
    supplier_name: str
    criteria: List[CriterionScoreModel]
    risks: List[str] = Field(default_factory=list)
    overall_summary: str = ""

def validate_and_normalize_evaluation(
    raw_llm_output: Dict[str, Any],
    active_criteria: List[Dict[str, Any]],
    supplier_name_fallback: str = "Unknown Supplier"
) -> Dict[str, Any]:
    """
    Validates LLM raw output against Pydantic schema, fills missing active criteria,
    clips out-of-range scores to [0, max_score], and records audit warnings.
    """
    warnings = []
    normalized_criteria_map = {}
    
    # Extract criteria list from raw output
    raw_criteria = raw_llm_output.get("criteria", []) if isinstance(raw_llm_output, dict) else []
    supplier_name = raw_llm_output.get("supplier_name", supplier_name_fallback) if isinstance(raw_llm_output, dict) else supplier_name_fallback

    # Process raw criterion items
    for item in raw_criteria:
        if not isinstance(item, dict):
            warnings.append(f"Skipped invalid non-dict criterion item: {item}")
            continue
            
        cid = item.get("criterion_id")
        if cid is None:
            warnings.append(f"Criterion item missing 'criterion_id': {item}")
            continue
            
        # Pydantic validation for individual criterion
        try:
            crit_obj = CriterionScoreModel(
                criterion_id=int(cid),
                score=float(item.get("score", 0.0)),
                max_score=float(item.get("max_score", 10.0)),
                justification=str(item.get("justification", "")),
                evidence=str(item.get("evidence", ""))
            )
        except Exception as e:
            warnings.append(f"Malformed criterion {cid} coerced to defaults: {str(e)}")
            crit_obj = CriterionScoreModel(
                criterion_id=int(cid),
                score=0.0,
                max_score=10.0,
                justification="Coerced default due to schema error",
                evidence="N/A"
            )
            
        # Score clipping & range checks
        active_match = next((c for c in active_criteria if c["criterion_id"] == crit_obj.criterion_id), None)
        expected_max = active_match["max_score"] if active_match else crit_obj.max_score
        
        if crit_obj.score < 0:
            warnings.append(f"Criterion ID {cid} score ({crit_obj.score}) clipped to 0.0")
            crit_obj.score = 0.0
        elif crit_obj.score > expected_max:
            warnings.append(f"Criterion ID {cid} score ({crit_obj.score}) clipped to max ({expected_max})")
            crit_obj.score = expected_max
            
        crit_obj.max_score = expected_max
        normalized_criteria_map[crit_obj.criterion_id] = crit_obj

    # Fill in missing active criteria
    final_criteria_list = []
    for ac in active_criteria:
        cid = ac["criterion_id"]
        if cid in normalized_criteria_map:
            final_criteria_list.append(normalized_criteria_map[cid].model_dump())
        else:
            warnings.append(f"Missing score for active criterion ID {cid} ('{ac['name']}'); filled default score 0.0")
            missing_item = CriterionScoreModel(
                criterion_id=cid,
                score=0.0,
                max_score=ac["max_score"],
                justification="Default fill-in for missing active criterion.",
                evidence="N/A (Not provided in LLM evaluation)"
            )
            final_criteria_list.append(missing_item.model_dump())

    # Build validated output
    risks = raw_llm_output.get("risks", []) if isinstance(raw_llm_output, dict) else []
    summary = raw_llm_output.get("overall_summary", "No summary provided.") if isinstance(raw_llm_output, dict) else "No summary provided."
    
    validated_model = EvaluationOutputModel(
        supplier_name=supplier_name,
        criteria=[CriterionScoreModel(**c) for c in final_criteria_list],
        risks=[str(r) for r in risks],
        overall_summary=str(summary)
    )

    result = validated_model.model_dump()
    result["warnings"] = warnings
    return result
