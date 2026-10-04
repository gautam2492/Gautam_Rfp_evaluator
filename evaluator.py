import os
import json
import re
from typing import List, Dict, Any

# Optional LangSmith Tracing
try:
    from langsmith import traceable
except ImportError:
    # Fallback no-op decorator if langsmith is not installed
    def traceable(name: str = None, **kwargs):
        def decorator(func):
            return func
        return decorator

EVALUATION_PROMPT_TEMPLATE = """
You are an expert AI Procurement Evaluator. You are analyzing an RFP response document submitted by supplier '{supplier_name}'.

Evaluate the proposal against ONLY the active evaluation criteria listed below. For every criterion, provide a numerical score between 0 and max_score (inclusive), an objective justification, and direct supporting evidence/quotes from the document text.

ACTIVE CRITERIA TO EVALUATE:
{criteria_text}

PROPOSAL DOCUMENT TEXT:
{pdf_text}

STRICT CONSTRAINTS:
1. Base your evaluation ONLY on explicit evidence present in the document.
2. Return exactly ONE result for every active criterion listed above, matching its criterion_id.
3. Keep scores strictly within range [0, max_score].
4. Output MUST be valid JSON only matching the schema below.

JSON OUTPUT SCHEMA:
{{
  "supplier_name": "{supplier_name}",
  "criteria": [
    {{
      "criterion_id": <int>,
      "score": <number between 0 and max_score>,
      "max_score": <number>,
      "justification": "<detailed reasoning>",
      "evidence": "<exact quote or specific fact from PDF>"
    }}
  ],
  "risks": ["<identified risk or concern 1>", "<identified risk or concern 2>"],
  "overall_summary": "<concise summary of proposal strengths and weaknesses>"
}}
"""

def evaluate_supplier_mock(supplier_name: str, pdf_text: str, active_criteria: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Fallback intelligent mock evaluator based on synthetic supplier profiles."""
    lower_text = pdf_text.lower()
    
    mock_data = {
        "Apex Systems": {
            "scores": {1: 9.0, 2: 7.0, 3: 5.0, 4: 9.5, 5: 9.0},
            "justification": {
                1: "Outstanding microservices architecture with Kubernetes, zero-trust IAM, and 99.999% availability.",
                2: "Comprehensive 9-month delivery roadmap with 4 distinct phases and 8 senior architects.",
                3: "High commercial cost ($250,000) making it the most expensive proposal.",
                4: "Fully certified ISO 27001, SOC 2 Type II, HIPAA with AES-256 encryption.",
                5: "10 years enterprise experience with 15+ Fortune 500 references and 15-min emergency SLA."
            },
            "evidence": {
                1: "Microservices on Kubernetes (EKS), zero-trust IAM, microsecond latency APIs.",
                2: "Delivery duration is 9 months structured in 4 phases with 8 senior architects.",
                3: "Total Commercial Price: Fixed Fee Contract $250,000.",
                4: "Certified ISO 27001, SOC 2 Type II, and HIPAA compliant.",
                5: "10 years of enterprise experience with 15+ Fortune 500 reference projects."
            },
            "risks": ["Highest cost tier among all bidders ($250k)", "Longer implementation duration (9 months)"],
            "summary": "Apex Systems presents a top-tier technical and security proposal with superior support, but commands a premium price and longer timeline."
        },
        "BrightPath Tech": {
            "scores": {1: 6.0, 2: 9.0, 3: 10.0, 4: 4.0, 5: 4.0},
            "justification": {
                1: "Basic standard server deployment suitable for medium workloads.",
                2: "Very fast 3-month timeline with agile setup.",
                3: "Lowest price ($120,000) providing maximum commercial savings.",
                4: "Weak compliance detail; official SOC2 certification is pending.",
                5: "Only 2 years in business with basic email support."
            },
            "evidence": {
                1: "Standard cloud server deployment with REST endpoints.",
                2: "Aggressive 3-month timeline: Setup & Deploy (Month 1), Go-Live (Month 3).",
                3: "Total Commercial Price: Low-Cost Guarantee $120,000.",
                4: "Standard password auth; official SOC2 certification is currently pending.",
                5: "Startup founded 2 years ago; standard email support during business hours."
            },
            "risks": ["Pending SOC2 compliance creates security risk", "Limited 2-year company track record"],
            "summary": "BrightPath Tech offers the lowest price and fastest turnaround, but lacks security compliance and enterprise experience."
        },
        "NexaWorks": {
            "scores": {1: 8.5, 2: 9.5, 3: 8.0, 4: 9.0, 5: 9.5},
            "justification": {
                1: "Robust cloud-native microservices with OAuth2/OIDC and 99.95% SLA.",
                2: "Flawless 6-month phased delivery plan with detailed risk mitigation matrix.",
                3: "Balanced commercial package ($180,000) with strong ROI.",
                4: "Fully SOC 2 Type II and ISO 27001 certified with RBAC.",
                5: "7 years experience with 24/7 dedicated support and 30-min SLA."
            },
            "evidence": {
                1: "Cloud-native microservices architecture with OAuth2/OIDC integration.",
                2: "Structured 6-month phased delivery with risk mitigation matrix included.",
                3: "Total Commercial Price: Balanced Enterprise Package $180,000.",
                4: "Full SOC 2 Type II and ISO 27001 certified with quarterly vulnerability audits.",
                5: "7 years in business; 24/7 Tier-3 support with guaranteed 30-minute SLA."
            },
            "risks": ["Requires close coordination for 6-month phase cutover"],
            "summary": "NexaWorks delivers the most well-rounded proposal with excellent technical capability, strong support, and competitive pricing."
        },
        "Orbit Digital": {
            "scores": {1: 6.5, 2: 5.5, 3: 7.0, 4: 7.5, 5: 10.0},
            "justification": {
                1: "Custom legacy wrapper framework; technical integration details are vague.",
                2: "Vague implementation milestones; team allocation deferred post-kickoff.",
                3: "Mid-tier pricing ($210,000) for perpetual license model.",
                4: "ISO 27001 certified with standard firewall and backup controls.",
                5: "Industry veteran with 12 years experience and 40+ reference stories."
            },
            "evidence": {
                1: "Custom legacy framework wrapper with REST integration options.",
                2: "Estimated 7 months timeline; specific milestone breakdown determined after kickoff.",
                3: "Total Commercial Price: Competitive Mid-Tier $210,000.",
                4: "ISO 27001 certified; standard firewall protection.",
                5: "12 years market leadership with over 40+ client success stories."
            },
            "risks": ["Vague integration and implementation milestone details", "Higher cost relative to technical innovation"],
            "summary": "Orbit Digital has unmatched industry experience and client references, but provides vague implementation and architectural specifications."
        }
    }
    
    # Match supplier profile
    profile_key = None
    for k in mock_data:
        if k.lower() in supplier_name.lower() or k.lower() in lower_text:
            profile_key = k
            break
            
    if not profile_key:
        profile_key = "NexaWorks"
        
    prof = mock_data[profile_key]
    
    criterion_results = []
    for crit in active_criteria:
        cid = crit["criterion_id"]
        max_s = float(crit.get("max_score", 10.0))
        score_val = prof["scores"].get(cid, 7.5)
        if score_val > max_s:
            score_val = max_s
            
        criterion_results.append({
            "criterion_id": cid,
            "score": score_val,
            "max_score": max_s,
            "justification": prof["justification"].get(cid, f"Evaluated {crit['name']} based on document content."),
            "evidence": prof["evidence"].get(cid, f"Document details for {crit['name']}.")
        })
        
    return {
        "supplier_name": supplier_name,
        "criteria": criterion_results,
        "risks": prof["risks"],
        "overall_summary": prof["summary"]
    }

@traceable(name="Evaluate Supplier RFP Proposal via LLM")
def evaluate_supplier_llm(supplier_name: str, pdf_text: str, active_criteria: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Evaluates proposal using OpenAI API (gpt-4o-mini) or Gemini API.
    Monitored with LangSmith Tracing if LANGCHAIN_TRACING_V2='true' and LANGCHAIN_API_KEY is provided.
    Falls back to mock evaluator if no API key is set or if API call fails.
    """
    criteria_text_lines = []
    for c in active_criteria:
        criteria_text_lines.append(f"- ID {c['criterion_id']}: {c['name']} (Weight: {c['weight']}%, Max Score: {c['max_score']}) -> {c['description']}")
    criteria_text = "\n".join(criteria_text_lines)
    
    prompt = EVALUATION_PROMPT_TEMPLATE.format(
        supplier_name=supplier_name,
        criteria_text=criteria_text,
        pdf_text=pdf_text
    )

    # 1. OpenAI API Execution (gpt-4o-mini with JSON Mode)
    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        try:
            import openai
            client = openai.OpenAI(api_key=openai_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a precise procurement evaluation assistant that outputs JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.2
            )
            raw = response.choices[0].message.content
            print(f"[Evaluator] OpenAI gpt-4o-mini evaluated '{supplier_name}' successfully.")
            return json.loads(raw)
        except Exception as e:
            print(f"[Evaluator] OpenAI API call failed ({str(e)}), trying Gemini / fallback...")

    # 2. Gemini API Execution
    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if gemini_key:
        try:
            from google import genai
            client = genai.Client(api_key=gemini_key)
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config={'response_mime_type': 'application/json'}
            )
            raw = response.text
            raw = re.sub(r"^```json\s*", "", raw.strip(), flags=re.MULTILINE)
            raw = re.sub(r"\s*```$", "", raw.strip(), flags=re.MULTILINE)
            print(f"[Evaluator] Gemini 2.5 Flash evaluated '{supplier_name}' successfully.")
            return json.loads(raw)
        except Exception as e:
            print(f"[Evaluator] Gemini API call failed ({str(e)}), falling back...")

    # 3. Fallback to Mock Evaluator
    print(f"[Evaluator] No API key detected; using intelligent Mock Evaluator for '{supplier_name}'.")
    return evaluate_supplier_mock(supplier_name, pdf_text, active_criteria)
