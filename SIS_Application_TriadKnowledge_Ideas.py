import streamlit as st
import json
import base64
import requests
import urllib.parse
import re
from datetime import datetime
from openai import OpenAI
import streamlit.components.v1 as components

# =============================================================================
# 0. GLOBAL CONFIGURATION & FULL ONTOLOGIES
# =============================================================================
SYSTEM_DATE = datetime.now().strftime("%B %d, %Y")
VERSION_CODE = "v23.2.0-TRIAD-FULL-DIMENSION"

st.set_page_config(
    page_title=f"SIS Triad Synthesizer - {SYSTEM_DATE}",
    page_icon="🌳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- FULL KNOWLEDGE BASE RESTORATION ---
KNOWLEDGE_BASE = {
    "Science fields": {
        "Mathematics": {"cat": "Formal"}, "Physics": {"cat": "Natural"}, "Chemistry": {"cat": "Natural"},
        "Biology": {"cat": "Natural"}, "Neuroscience": {"cat": "Natural"}, "Psychology": {"cat": "Social"},
        "Sociology": {"cat": "Social"}, "Computer Science": {"cat": "Formal"}, "Medicine": {"cat": "Applied"},
        "Psychiatry": {"cat": "Applied"}, "Engineering": {"cat": "Applied"}, "Economics": {"cat": "Social"},
        "Philosophy": {"cat": "Humanities"}, "Linguistics": {"cat": "Humanities"}, "Ecology": {"cat": "Natural"},
        "History": {"cat": "Humanities"}, "Architecture": {"cat": "Applied"}, "Geology": {"cat": "Natural"},
        "Geography": {"cat": "Natural/Social"}, "Climatology": {"cat": "Natural"}, "Library Science": {"cat": "Applied"},
        "Criminology": {"cat": "Social"}, "Forensic sciences": {"cat": "Applied"}, "Legal science": {"cat": "Social"}
    },
    "Paradigms": ["Empiricism", "Rationalism", "Constructivism", "Positivism", "Pragmatism"],
    "Models": ["Causal Connections", "Principles & Relations", "Episodes & Sequences", "Facts & Characteristics", "Generalizations", "Glossary", "Concepts"]
}

HUMAN_THINKING_METAMODEL = {
    "nodes": {
        "Human mental concentration": "Foundational cognitive focus.",
        "Identity": "Subjective core and ethical parameters.",
        "Autobiographical memory": "Historical database of past cycles.",
        "Mission": "Existential imperative driving inquiry.",
        "Vision": "Mental simulation of desired future.",
        "Goal": "Quantifiable milestones.",
        "Problem": "Gap between current and target state.",
        "Ethics/moral": "Value system filtering solutions.",
        "Hierarchy of interests": "Ordering of needs.",
        "Rule": "Structural and logical constraints.",
        "Decision-making": "Selection pathways.",
        "Problem solving": "Algorithmic process.",
        "Conflict situation": "Goal/rule clashing.",
        "Knowledge": "Internalized facts.",
        "Tool": "External instruments.",
        "Experience": "Wisdom from application.",
        "Classification": "Taxonomic cognitive reduction.",
        "Psychological aspect": "Internal mental states.",
        "Sociological aspect": "External collective impact."
    }
}

MENTAL_APPROACHES_FULL = {
    "Perspective shifting": "Stakeholder rotation.", "Similarity and difference": "Anomaly detection.",
    "Core": "Essence distillation.", "Attraction": "Synthesis force.", "Repulsion": "Noise isolation.",
    "Condensation": "Complexity reduction.", "Framework and foundation": "Boundary logic.",
    "Bipolarity and dialectics": "Synthesis via tension.", "Constant": "Invariants.",
    "Associativity": "Lateral linking.", "Induction": "Theory from field.",
    "Whole and part": "Holistic navigation.", "Mini-max": "Efficiency search.",
    "Addition and composition": "Layered complexity.", "Hierarchy": "Systemic priority.",
    "Balance": "Dynamic equilibrium.", "Deduction": "Laws to specifics.",
    "Abstraction and elimination": "Noise removal.", "Pleasure and displeasure": "Elegance feedback.",
    "Openness and closedness": "Boundary state."
}

# --- CSS & STYLING ---
st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #fcfcfc !important; border-right: 2px solid #e9ecef !important; min-width: 380px !important; }
    [data-testid="stSidebar"] .stMarkdown p, label { color: #1d3557 !important; font-weight: 600 !important; }
    .main-header-gradient { background: linear-gradient(90deg, #1d3557, #457b9d); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800; font-size: 2.5rem; }
    .date-badge { background-color: #1d3557; color: white; padding: 10px; border-radius: 50px; text-align: center; font-weight: 800; margin-bottom: 20px; }
    .semantic-node-highlight { color: #2a9d8f; font-weight: bold; border-bottom: 2px solid #2a9d8f; text-decoration: none !important; }
</style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
def render_cytoscape_network(elements, container_id="cy_triad_full"):
    cyto_html = f"""
    <div id="{container_id}" style="width: 100%; height: 700px; background: #ffffff; border-radius: 20px; border: 1px solid #e0e0e0;"></div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.26.0/cytoscape.min.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            var cy = cytoscape({{
                container: document.getElementById('{container_id}'),
                elements: {json.dumps(elements)},
                style: [
                    {{ selector: 'node', style: {{ 'label': 'data(label)', 'background-color': 'data(color)', 'shape': 'data(shape)', 'width': 70, 'height': 70, 'font-size': '10px', 'text-valign': 'center', 'color': '#000', 'text-outline-width': 1, 'text-outline-color': '#fff' }} }},
                    {{ selector: 'edge', style: {{ 'width': 2, 'line-color': '#adb5bd', 'target-arrow-shape': 'triangle', 'curve-style': 'bezier', 'label': 'data(rel)', 'font-size': '8px' }} }}
                ],
                layout: {{ name: 'cose', padding: 40, nodeRepulsion: 40000 }}
            }});
        }});
    </script>
    """
    components.html(cyto_html, height=750)

# =============================================================================
# 1. SIDEBAR (CONTROLS & EXPLORER)
# =============================================================================

with st.sidebar:
    st.markdown(f'<div class="date-badge">{SYSTEM_DATE.upper()}</div>', unsafe_allow_html=True)
    st.header("⚙️ SYSTEM CONTROL")
    cerebras_api_key = st.text_input("🔑 Cerebras API Key:", type="password")
    cerebras_id = st.selectbox("Model:", ["llama-3.1-70b", "llama3.1-8b"])
    
    st.divider()
    st.subheader("📚 KNOWLEDGE EXPLORER")
    with st.expander("🔬 Science Taxonomy (24 Fields)"):
        for s in sorted(KNOWLEDGE_BASE["Science fields"].keys()): st.write(f"• {s}")
    with st.expander("🧠 Mental Approaches (20 Dimensions)"):
        for m, d in MENTAL_APPROACHES_FULL.items(): st.write(f"**{m}**: {d}")
    with st.expander("🏛️ IMA Metamodel Architecture"):
        for n, d in HUMAN_THINKING_METAMODEL.items(): st.write(f"**{n}**: {d}")

# =============================================================================
# 2. MAIN INTERFACE
# =============================================================================

st.markdown('<h1 class="main-header-gradient">🧱 SIS Triad Full-Dimension Synthesizer</h1>', unsafe_allow_html=True)
st.caption(f"Sequential Cerebras Engine: Phase 1 (0.85) → Phase 2 (0.65) → Phase 3 (0.4)")

# Grid Config
r1c1, r1c2, r1c3 = st.columns(3)
with r1c1: sel_sciences = st.multiselect("Select Sciences:", list(KNOWLEDGE_BASE["Science fields"].keys()), default=["Physics", "Psychology"])
with r1c2: sel_paradigms = st.multiselect("Paradigms:", KNOWLEDGE_BASE["Paradigms"], default=["Positivism", "Rationalism"])
with r1c3: sel_models = st.multiselect("Structural Models:", KNOWLEDGE_BASE["Models"], default=["Concepts"])

st.divider()
col_inq1, col_inq2 = st.columns(2)
with col_inq1:
    user_query = st.text_area("❓ STEP 1: Research Inquiry (IMA Foundation):", height=180, placeholder="Define the factual problem space...")
with col_inq2:
    idea_query = st.text_area("💡 STEP 2: Innovation Prompt (MA Logic):", height=180, placeholder="Target specific innovative outcomes...")

# =============================================================================
# 3. TRIAD EXECUTION ENGINE
# =============================================================================

if st.button("🚀 EXECUTE FULL-DIMENSION TRIAD PIPELINE", use_container_width=True):
    if not cerebras_api_key or not user_query:
        st.error("Missing API Key or Inquiry.")
    else:
        try:
            client = OpenAI(api_key=cerebras_api_key, base_url="https://api.cerebras.ai/v1")
            
            # PHASE 1: IMA FOUNDATION (0.85)
            with st.spinner('PHASE 1: Building Structural Foundation (Temp 0.85)...'):
                p1_sys = f"""You are Phase 1 (Architect). Focus: IMA Architecture {json.dumps(HUMAN_THINKING_METAMODEL)}. 
                Sciences: {sel_sciences}. Paradigms: {sel_paradigms}. Establish the 'Identity', 'Mission', and 'Problem'."""
                p1_res = client.chat.completions.create(
                    model=cerebras_id, messages=[{"role": "system", "content": p1_sys}, {"role": "user", "content": user_query}],
                    temperature=0.85
                )
                p1_text = p1_res.choices[0].message.content

            # PHASE 2: MA INNOVATION (0.65)
            with st.spinner('PHASE 2: Generating Innovative Ideas (Temp 0.65)...'):
                p2_sys = f"""You are Phase 2 (Innovator). Apply these Mental Approaches: {json.dumps(MENTAL_APPROACHES_FULL)}.
                Take the Foundation and generate radical 'Useful Innovative Ideas' using Dialectics, Perspective Shifting, and Core distillation."""
                p2_res = client.chat.completions.create(
                    model=cerebras_id, 
                    messages=[{"role": "system", "content": p2_sys}, {"role": "user", "content": f"Foundation:\n{p1_text}\n\nGoal: {idea_query}"}],
                    temperature=0.65
                )
                p2_text = p2_res.choices[0].message.content

            # PHASE 3: SYNTHESIS & GRAPH (0.4)
            with st.spinner('PHASE 3: Final Synthesis & Semantic Mapping (Temp 0.4)...'):
                p3_sys = """You are Phase 3 (Integrator). Finalize the 18D report. 
                CRITICAL: End with '### SEMANTIC_GRAPH_JSON' + valid JSON.
                Nodes: {"id": "n1", "label": "Text", "color": "#hex", "shape": "rectangle(IMA)|diamond(MA)"}."""
                p3_res = client.chat.completions.create(
                    model=cerebras_id,
                    messages=[{"role": "system", "content": p3_sys}, {"role": "user", "content": f"Context:\n{p1_text}\n{p2_text}"}],
                    temperature=0.4
                )
                p3_text = p3_res.choices[0].message.content

            # --- RENDERING ---
            full_report = f"# 🎓 SIS Full-Dimension Synthesis\n\n## 🏛️ Phase 1: IMA Foundation\n{p1_text}\n\n## 💡 Phase 2: MA Innovations\n{p2_text}\n\n## 🧬 Phase 3: Final Synthesis\n{p3_text}"
            parts = full_report.split("### SEMANTIC_GRAPH_JSON")
            main_markdown = parts[0]
            
            # Semantic Linker
            if len(parts) > 1:
                try:
                    g_json = json.loads(re.search(r'\{.*\}', parts[1], re.DOTALL).group())
                    for n in g_json.get("nodes", []):
                        lbl = n["label"]
                        pattern = re.compile(re.escape(lbl), re.IGNORECASE)
                        replacement = f'<a href="https://www.google.com/search?q={urllib.parse.quote(lbl)}" target="_blank" class="semantic-node-highlight">{lbl}</a>'
                        main_markdown = pattern.sub(replacement, main_markdown, count=1)
                except: pass

            st.markdown(main_markdown, unsafe_allow_html=True)

            # Grapher
            if len(parts) > 1:
                try:
                    g_json = json.loads(re.search(r'\{.*\}', parts[1], re.DOTALL).group())
                    elements = []
                    for n in g_json.get("nodes", []):
                        elements.append({"data": {"id": n["id"], "label": n["label"], "color": n.get("color", "#457b9d"), "shape": n.get("shape", "rectangle")}})
                    for e in g_json.get("edges", []):
                        elements.append({"data": {"source": e["source"], "target": e["target"], "rel": e.get("rel_type", "links")}})
                    render_cytoscape_network(elements)
                except: st.error("Graph rendering failed.")

        except Exception as e:
            st.error(f"Error: {e}")

st.divider()
st.caption(f"SIS Triad | {VERSION_CODE} | Sciences: 24 | Approaches: 20 | Temp Gradient: 0.85/0.65/0.4")



