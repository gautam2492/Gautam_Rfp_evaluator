import streamlit as st
import json
import os
import pandas as pd
import datetime

import database
import pdf_generator
import orchestrator

st.set_page_config(
    page_title="Agentic RFP Evaluation & Supplier Ranking",
    page_icon="🏆",
    layout="wide"
)

# Initialize Database
database.init_db()

st.title("🏆 Agentic RFP Evaluation & Supplier Ranking System")
st.markdown("""
*An AI-assisted procurement application that reads supplier proposals, scores them against active criteria using an LLM with evidence grounding, validates schema outputs, and applies 100% deterministic scoring, peer benchmarking (PPI), and stable tie-breaker ranking.*
""")

# Sidebar Navigation & API Key Settings
st.sidebar.header("Navigation")
menu_choice = st.sidebar.radio(
    "Select Screen:",
    ["1. Evaluation Criteria", "2. Upload & Evaluate Proposals", "3. Leaderboard & Benchmarks", "4. Detailed Scorecards", "5. Run Details & JSON Export"]
)

st.sidebar.divider()
st.sidebar.subheader("🔑 OpenAI / LLM API Key")
user_openai_key = st.sidebar.text_input("OpenAI API Key:", type="password", help="If provided, evaluation uses OpenAI gpt-4o-mini with structured JSON output.")
if user_openai_key:
    os.environ["OPENAI_API_KEY"] = user_openai_key.strip()

user_gemini_key = st.sidebar.text_input("Gemini API Key:", type="password", help="Alternative LLM: Google Gemini API.")
if user_gemini_key:
    os.environ["GEMINI_API_KEY"] = user_gemini_key.strip()

st.sidebar.subheader("📊 LangSmith Tracing (Observability)")
user_langsmith_key = st.sidebar.text_input("LangSmith API Key:", type="password", help="Enables live prompt & LLM evaluation tracing in LangSmith.")
if user_langsmith_key:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = user_langsmith_key.strip()
    os.environ["LANGCHAIN_PROJECT"] = "agentic-rfp-eval"

# Shared Session State for Run Results
if "latest_run" not in st.session_state:
    st.session_state["latest_run"] = None

# ---------------------------------------------------------
# SCREEN 1: EVALUATION CRITERIA MANAGEMENT
# ---------------------------------------------------------
if menu_choice == "1. Evaluation Criteria":
    st.header("⚙️ Active Evaluation Criteria & Weights")
    st.info("Stored in SQLite database. Weights of active criteria should ideally total 100%.")

    criteria = database.get_all_criteria()
    
    # Render Editable Table / Form
    updated_criteria = []
    total_weight = 0.0

    with st.form("criteria_form"):
        st.subheader("Current Criteria Configuration")
        cols = st.columns([1, 3, 2, 2, 2])
        cols[0].write("**ID**")
        cols[1].write("**Criterion Name**")
        cols[2].write("**Weight (%)**")
        cols[3].write("**Max Score**")
        cols[4].write("**Active?**")

        for c in criteria:
            cid = c["criterion_id"]
            c_cols = st.columns([1, 3, 2, 2, 2])
            c_cols[0].write(f"#{cid}")
            c_cols[1].write(f"**{c['name']}**\n\n_{c['description']}_")
            
            weight_val = c_cols[2].number_input(f"Weight {cid}", min_value=0.0, max_value=100.0, value=float(c["weight"]), step=5.0, key=f"w_{cid}")
            max_s_val = c_cols[3].number_input(f"Max {cid}", min_value=1.0, max_value=100.0, value=float(c["max_score"]), step=1.0, key=f"m_{cid}")
            active_val = c_cols[4].checkbox(f"Active {cid}", value=bool(c["is_active"]), key=f"a_{cid}")

            if active_val:
                total_weight += weight_val

            updated_criteria.append({
                "criterion_id": cid,
                "weight": weight_val,
                "max_score": max_s_val,
                "is_active": 1 if active_val else 0
            })

        submit_btn = st.form_submit_button("Save Criteria Changes")
        if submit_btn:
            for uc in updated_criteria:
                database.update_criterion(uc["criterion_id"], uc["weight"], uc["max_score"], uc["is_active"])
            st.success("Criteria updated successfully in SQLite database!")
            st.rerun()

    # Display Weight Sum Alert
    if abs(total_weight - 100.0) < 0.01:
        st.success(f"✅ Total Active Weight: **{total_weight:.1f}%**")
    else:
        st.warning(f"⚠️ Total Active Weight is **{total_weight:.1f}%** (Recommended: 100%).")

# ---------------------------------------------------------
# SCREEN 2: UPLOAD & EVALUATE PROPOSALS
# ---------------------------------------------------------
elif menu_choice == "2. Upload & Evaluate Proposals":
    st.header("📄 Upload Supplier RFP Proposals")

    col_left, col_right = st.columns([3, 2])

    with col_right:
        st.subheader("💡 Sample Data Generator")
        st.markdown("Quickly generate the 4 required artificial supplier PDFs for testing:")
        if st.button("✨ Generate & Load 4 Sample Supplier PDFs"):
            with st.spinner("Generating artificial PDFs..."):
                gen_map = pdf_generator.generate_supplier_pdfs("sample_pdfs")
                st.session_state["sample_pdfs_generated"] = gen_map
                st.success("Generated Apex Systems, BrightPath Tech, NexaWorks, and Orbit Digital PDFs!")

    with col_left:
        st.subheader("Manual RFP Ingestion")
        uploaded_files = st.file_uploader("Upload Supplier RFP PDFs", type=["pdf"], accept_multiple_files=True)

    supplier_inputs = []

    # If sample PDFs exist, allow quick batch select
    if st.session_state.get("sample_pdfs_generated"):
        st.subheader("Generated Sample Proposals Ready for Evaluation")
        sample_meta = [
            {"supplier_name": "Apex Systems", "pdf_path": "sample_pdfs/RFP_Apex_Systems.pdf", "sub_date": "2026-08-01", "exp": 4.8},
            {"supplier_name": "BrightPath Tech", "pdf_path": "sample_pdfs/RFP_BrightPath_Tech.pdf", "sub_date": "2026-07-15", "exp": 2.0},
            {"supplier_name": "NexaWorks", "pdf_path": "sample_pdfs/RFP_NexaWorks.pdf", "sub_date": "2026-07-28", "exp": 4.5},
            {"supplier_name": "Orbit Digital", "pdf_path": "sample_pdfs/RFP_Orbit_Digital.pdf", "sub_date": "2026-08-05", "exp": 5.0},
        ]
        
        use_samples = st.checkbox("Use all 4 generated sample supplier proposals", value=True)
        if use_samples:
            for sm in sample_meta:
                if os.path.exists(sm["pdf_path"]):
                    supplier_inputs.append({
                        "supplier_name": sm["supplier_name"],
                        "pdf_input": sm["pdf_path"],
                        "submission_date": sm["sub_date"],
                        "experience_rating": sm["exp"]
                    })

    # Add custom uploaded files
    if uploaded_files:
        st.subheader("Uploaded Files Metadata")
        for idx, file in enumerate(uploaded_files):
            c1, c2, c3 = st.columns([3, 2, 2])
            sname = c1.text_input(f"Supplier Name #{idx+1}", value=file.name.replace(".pdf", "").replace("RFP_", "").replace("_", " "))
            sdate = c2.date_input(f"Submission Date #{idx+1}", value=datetime.date.today(), key=f"d_{idx}")
            sexp = c3.number_input(f"Experience Rating (1-5) #{idx+1}", min_value=1.0, max_value=5.0, value=4.0, step=0.5, key=f"e_{idx}")

            supplier_inputs.append({
                "supplier_name": sname,
                "pdf_input": file.read(),
                "submission_date": sdate.isoformat(),
                "experience_rating": sexp
            })

    st.divider()

    if supplier_inputs:
        st.success(f"Ready to evaluate **{len(supplier_inputs)}** supplier proposals.")
        if st.button("🚀 Evaluate RFP Batch Now", type="primary"):
            with st.spinner("Processing documents, invoking LLM evaluator, validating schemas, and ranking suppliers..."):
                try:
                    result = orchestrator.run_rfp_evaluation_pipeline(supplier_inputs)
                    st.session_state["latest_run"] = result
                    st.success(f"Batch evaluation completed successfully! Run ID: `{result['rfp_run_id']}`")
                    st.balloons()
                except Exception as e:
                    st.error(f"Evaluation Pipeline Error: {str(e)}")
    else:
        st.info("Upload PDF documents or generate sample PDFs to evaluate.")

# ---------------------------------------------------------
# SCREEN 3: LEADERBOARD & PEER BENCHMARKS
# ---------------------------------------------------------
elif menu_choice == "3. Leaderboard & Benchmarks":
    st.header("🏆 Final Supplier Leaderboard")

    run_data = st.session_state.get("latest_run")
    if not run_data:
        # Load most recent run from database if available
        all_runs = database.list_all_runs()
        if all_runs:
            latest_id = all_runs[0]["rfp_run_id"]
            run_data = database.get_rfp_run(latest_id)

    if not run_data:
        st.warning("No evaluation run found. Please execute a batch evaluation in Screen #2.")
    else:
        st.subheader(f"Run ID: `{run_data['rfp_run_id']}` | Status: `{run_data['status']}`")

        leaders = run_data["supplier_results"] if "supplier_results" in run_data else run_data.get("leaderboard", [])

        # Leaderboard Summary Table
        df_list = []
        for s in leaders:
            df_list.append({
                "Rank": f"#{s['final_rank']}",
                "Supplier Name": s["supplier_name"],
                "Absolute Score (out of 100)": f"{s['absolute_score']:.2f}",
                "Peer Performance Index (PPI %)": f"{s['ppi']:.2f}%",
                "Submission Date": s.get("submission_date", "N/A"),
                "Exp Rating (1-5)": s.get("experience_rating", 0.0),
                "Tie-Break Details": s.get("tie_break_info", "N/A")
            })

        df_leader = pd.DataFrame(df_list)
        st.dataframe(df_leader, use_container_width=True)

        st.subheader("📊 Performance Index Comparison")
        chart_data = pd.DataFrame({
            "Supplier": [s["supplier_name"] for s in leaders],
            "Absolute Score": [s["absolute_score"] for s in leaders],
            "PPI (%)": [s["ppi"] for s in leaders]
        }).set_index("Supplier")
        
        st.bar_chart(chart_data)

# ---------------------------------------------------------
# SCREEN 4: DETAILED SCORECARDS & EVIDENCE
# ---------------------------------------------------------
elif menu_choice == "4. Detailed Scorecards":
    st.header("🔍 Detailed Supplier Scorecard & Evidence Drilldown")

    run_data = st.session_state.get("latest_run")
    if not run_data:
        all_runs = database.list_all_runs()
        if all_runs:
            run_data = database.get_rfp_run(all_runs[0]["rfp_run_id"])

    if not run_data:
        st.warning("No evaluation run found. Please execute a batch evaluation in Screen #2.")
    else:
        leaders = run_data["supplier_results"] if "supplier_results" in run_data else run_data.get("leaderboard", [])

        supp_names = [s["supplier_name"] for s in leaders]
        selected_supp_name = st.selectbox("Select Supplier to Inspect:", supp_names)

        selected_supp = next(s for s in leaders if s["supplier_name"] == selected_supp_name)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Final Rank", f"#{selected_supp['final_rank']}")
        col2.metric("Absolute Weighted Score", f"{selected_supp['absolute_score']:.2f} / 100")
        col3.metric("Peer Performance Index (PPI)", f"{selected_supp['ppi']:.2f}%")
        col4.metric("Experience Rating", f"{selected_supp.get('experience_rating', 0.0)} / 5.0")

        st.divider()
        st.subheader("Criterion-Wise Breakdown")

        scorecard = selected_supp.get("scorecard", [])
        sc_df_list = []
        for sc in scorecard:
            sc_df_list.append({
                "Criterion ID": sc["criterion_id"],
                "Criterion Name": sc["criterion_name"],
                "Score": f"{sc['score']:.1f} / {sc['max_score']:.1f}",
                "Weight": f"{sc['weight']:.1f}%",
                "Benchmark Leader": f"{sc['benchmark']:.1f}",
                "Gap": f"{sc['gap']:.1f}",
                "Relative Perf %": f"{sc['relative_pct']:.1f}%"
            })
        st.dataframe(pd.DataFrame(sc_df_list), use_container_width=True)

        st.subheader("Evidence & Justifications")
        for sc in scorecard:
            with st.expander(f"📌 {sc['criterion_name']} (Score: {sc['score']} / {sc['max_score']})"):
                st.write(f"**Justification:** {sc['justification']}")
                st.info(f"**Supporting Evidence / Quote:**\n> {sc['evidence']}")

        st.subheader("Identified Risks & Concerns")
        risks = selected_supp.get("risks", [])
        if risks:
            for r in risks:
                st.warning(f"⚠️ {r}")
        else:
            st.success("No critical risks identified.")

        st.subheader("Overall Executive Summary")
        st.write(selected_supp.get("overall_summary", "N/A"))

# ---------------------------------------------------------
# SCREEN 5: RUN DETAILS & JSON EXPORT
# ---------------------------------------------------------
elif menu_choice == "5. Run Details & JSON Export":
    st.header("💾 Run Execution Details & JSON Download")

    all_runs = database.list_all_runs()
    if not all_runs:
        st.warning("No completed RFP runs found in SQLite database.")
    else:
        run_ids = [r["rfp_run_id"] for r in all_runs]
        selected_run_id = st.selectbox("Select RFP Run ID:", run_ids)

        run_details = database.get_rfp_run(selected_run_id)

        st.write(f"**Run Created At:** {run_details['created_at']}")
        st.write(f"**Status:** {run_details['status']}")

        json_str = json.dumps(run_details, indent=2)

        st.subheader("Exported Run JSON")
        st.download_button(
            label="📥 Download Complete RFP Run JSON",
            data=json_str,
            file_name=f"{selected_run_id}_export.json",
            mime="application/json"
        )

        st.code(json_str[:2000] + ("\n... [Truncated for preview]" if len(json_str) > 2000 else ""), language="json")
