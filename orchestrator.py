import datetime
import uuid
from typing import List, Dict, Any, Union
import database
import pdf_extractor
import evaluator
import validator
import ranker

def run_rfp_evaluation_pipeline(
    supplier_inputs: List[Dict[str, Any]],
    db_path: str = database.DB_PATH
) -> Dict[str, Any]:
    """
    Main Orchestrator Agent Pipeline.
    
    supplier_inputs format:
    [
      {
        "supplier_name": "Apex Systems",
        "pdf_input": <str filepath or bytes>,
        "submission_date": "2026-08-01",
        "experience_rating": 4.8
      },
      ...
    ]
    """
    # 1. Generate Batch Run Identifier
    run_timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    rfp_run_id = f"RFP-RUN-{run_timestamp}-{str(uuid.uuid4())[:4]}"

    # 2. Fetch active criteria from SQLite
    active_criteria = database.get_active_criteria(db_path)
    if not active_criteria:
        raise ValueError("No active criteria found in SQLite database.")

    evaluated_suppliers = []
    run_warnings = []

    # 3. Ingest, Extract & Evaluate each supplier PDF independently
    for s_in in supplier_inputs:
        supp_name = s_in.get("supplier_name", "Unknown Supplier")
        pdf_inp = s_in["pdf_input"]
        sub_date = s_in.get("submission_date", datetime.date.today().isoformat())
        exp_rating = float(s_in.get("experience_rating", 3.0))

        # Document Tool: Extract text
        try:
            pdf_text = pdf_extractor.extract_pdf_text(pdf_inp)
        except Exception as e:
            w_msg = f"Failed to extract text from PDF for '{supp_name}': {str(e)}"
            run_warnings.append(w_msg)
            pdf_text = f"Proposal submitted by {supp_name}."

        # Evaluation Agent: Call LLM
        raw_eval = evaluator.evaluate_supplier_llm(supp_name, pdf_text, active_criteria)

        # Validation Tool: Pydantic normalization & warning check
        val_eval = validator.validate_and_normalize_evaluation(raw_eval, active_criteria, supp_name)
        if val_eval.get("warnings"):
            for w in val_eval["warnings"]:
                run_warnings.append(f"[{supp_name}] {w}")

        val_eval["submission_date"] = sub_date
        val_eval["experience_rating"] = exp_rating
        evaluated_suppliers.append(val_eval)

    # 4. Ranking Tool: Deterministic scoring, peer benchmarking, PPI, and tie-breakers
    final_ranked_suppliers = ranker.compute_batch_scoring_and_ranking(evaluated_suppliers, active_criteria)

    # 5. Persist complete RFP run results in SQLite
    database.save_rfp_run(rfp_run_id, "COMPLETED", final_ranked_suppliers, db_path)

    # 6. Return comprehensive structured result
    return {
        "rfp_run_id": rfp_run_id,
        "status": "COMPLETED",
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "active_criteria_used": active_criteria,
        "total_suppliers_evaluated": len(final_ranked_suppliers),
        "pipeline_warnings": run_warnings,
        "leaderboard": final_ranked_suppliers
    }
