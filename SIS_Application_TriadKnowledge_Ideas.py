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
# 0. GLOBAL CONFIGURATION & FULL DIMENSION DATA
# =============================================================================
SYSTEM_DATE = "February 24, 2026"
VERSION_CODE = "v23.8.0-TRIAD-HIERARCHOLOGY-ULTRA"

st.set_page_config(
    page_title=f"SIS Triad Synthesizer - {SYSTEM_DATE}",
    page_icon="🌳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- IDEA GENERATION TECHNIQUES ---
IDEA_TECHNIQUES = {
    "SCAMPER": "Substitute, Combine, Adapt, Modify, Put to another use, Eliminate, Reverse.",
    "TRIZ": "Theory of Inventive Problem Solving (40 Principles of contradiction resolution).",
    "First Principles": "Breaking down problems to fundamental truths to build up.",
    "Six Thinking Hats": "Parallel logic (Facts, Emotions, Risks, Benefits, Ideas, Control).",
    "Lateral Thinking": "Provocation and movement to bypass established thought patterns.",
    "Synectics": "Using analogies (Personal, Direct, Symbolic) for new perspectives."
}

# --- HIERARCHOLOGY & METAMODEL DATA ---
HIERARCHOLOGY_ONTOLOGY = {
    "core": ["Micro-hierarchology", "Meso-hierarchology", "Macro-hierarchology", "Scientific Cage", "Hierarchography"],
    "logic": "Inductive (Internal) vs Deductive (External)."
}

KNOWLEDGE_BASE = {
    "Science fields": [
        "Mathematics", "Physics", "Chemistry", "Biology", "Neuroscience", "Psychology", 
        "Sociology", "Computer Science", "Medicine", "Psychiatry", "Engineering", "Economics", 
        "Philosophy", "Linguistics", "Ecology", "History", "Architecture", "Geology", 
        "Geography", "Climatology", "Library Science", "Criminology", "Forensic sciences", "Legal science"
    ],
    "Paradigms": ["Empiricism", "Rationalism", "Constructivism", "Positivism", "Pragmatism"],
    "Models": ["Causal Connections", "Principles & Relations", "Episodes & Sequences", "Facts & Characteristics", "Concepts"]
}

# --- CSS OVERRIDE (MATCHING YOUR STYLE) ---
st.markdown("""
<style>
    [data-testid="stSidebar"] [data-testid="stIcon"],
    [data-testid="stSidebar"] button[data-testid="stSidebarCollapseButton"] { display: none !important; }
    [data-testid="stSidebar"] { background-color: #fcfcfc !important; border-right: 2px solid #e9ecef !important; min-width: 380px !important; }
    [data-testid="stSidebar"] .stMarkdown p, label { color: #1d3557 !important; font-weight: 600 !important; }
    .main-header-gradient { background: linear-gradient(90deg, #1d3557, #457b9d); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800; font-size: 2.8rem; }
    .date-badge { background-color: #1d3557; color: white; padding: 12px; border-radius: 50px; text-align: center; font-weight: 800; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(29, 53, 87, 0.3); }
    .metamodel-box { padding: 20px; border-radius: 12px; background-color: #f8f9fa; border-left: 8px solid #00B0F0; margin-bottom: 15px; }
    .semantic-node-highlight { color: #2a9d8f; font-weight: bold; border-bottom: 2px solid #2a9d8f; text-decoration: none !important; }
</style>
""", unsafe_allow_html=True)

def get_svg_base64(svg_str):
    return base64.b64encode(svg_str.encode('utf-8')).decode('utf-8')

# (Logo SVG truncated for brevity, same as yours)
SVG_3D_RELIEF = """<svg width="240" height="240" viewBox="0 0 240 240" xmlns="http://www.w3.org/2000/svg">...</svg>"""

def render_cytoscape_network(elements, container_id="cy_triad"):
    cyto_html = f"""
    <div id="{container_id}" style="width: 100%; height: 700px; background: #ffffff; border-radius: 20px; border: 1px solid #e0e0e0; box-shadow: 0 4px 20px rgba(0,0,0,0.05);"></div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.26.0/cytoscape.min.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            var cy = cytoscape({{
                container: document.getElementById('{container_id}'),
                elements: {json.dumps(elements)},
                style: [
                    {{ selector: 'node', style: {{ 'label': 'data(label)', 'background-color': 'data(color)', 'shape': 'data(shape)', 'width': 80, 'height': 80, 'font-size': '12px', 'text-valign': 'center', 'color': '#000', 'text-outline-width': 2, 'text-outline-color': '#fff' }} }},
                    {{ selector: 'edge', style: {{ 'width': 4, 'line-color': '#adb5bd', 'target-arrow-shape': 'triangle', 'curve-style': 'bezier', 'label': 'data(rel)', 'font-size': '10px' }} }}
                ],
                layout: {{ name: 'cose', padding: 50 }}
            }});
        }});
    </script>
    """
    components.html(cyto_html, height=750)

# =============================================================================
# 1. SIDEBAR CONFIGURATION
# =============================================================================
with st.sidebar:
    st.markdown(f'<div class="date-badge">{SYSTEM_DATE.upper()}</div>', unsafe_allow_html=True)
    st.header("⚙️ SYSTEM CONTROL")
    cerebras_api_key = st.text_input("🔑 Cerebras API Key:", type="password")
    cerebras_id = st.selectbox("Model:", ["llama-3.1-70b", "llama3.1-8b"])
    
    st.divider()
    st.subheader("📚 KNOWLEDGE EXPLORER")
    with st.expander("💡 Ideation Techniques"):
        for k, v in IDEA_TECHNIQUES.items(): st.markdown(f"**{k}**: {v}")
    with st.expander("📐 Hierarchology"):
        st.write(HIERARCHOLOGY_ONTOLOGY)
    with st.expander("🔬 Science Fields"):
        for s in sorted(KNOWLEDGE_BASE["Science fields"]): st.markdown(f"• {s}")

# =============================================================================
# 2. MAIN INTERFACE
# =============================================================================
st.markdown('<h1 class="main-header-gradient">🧱 SIS Triad Hierarchology Synthesizer</h1>', unsafe_allow_html=True)
st.caption(f"Cerebras Exclusive Sequential Pipeline | Gradient: 0.85 → 0.65 → 0.4")

r1c1, r1c2, r1c3 = st.columns(3)
with r1c1: sel_sciences = st.multiselect("Sciences:", KNOWLEDGE_BASE["Science fields"], default=["Physics", "Psychology"])
with r1c2: sel_paradigms = st.multiselect("Paradigms:", KNOWLEDGE_BASE["Paradigms"], default=["Positivism", "Rationalism"])
with r1c3: sel_techniques = st.multiselect("Ideation Techniques:", list(IDEA_TECHNIQUES.keys()), default=["SCAMPER", "TRIZ"])

st.divider()
col_inq1, col_inq2 = st.columns(2)
with col_inq1:
    user_query = st.text_area("❓ PHASE 1: Research Foundation (IMA & Hierarchology):", height=180, placeholder="Identify the Scientific Cage and problem levels...")
with col_inq2:
    innovation_goal = st.text_area("💡 PHASE 2: Innovation Target (MA & Ideation):", height=180, placeholder="Apply SCAMPER/TRIZ to generate radical ideas...")

# =============================================================================
# 3. TRIAD EXECUTION ENGINE (0.85 -> 0.65 -> 0.4)
# =============================================================================
if st.button("🚀 EXECUTE MULTI-DIMENSIONAL TRIAD PIPELINE", use_container_width=True):
    if not cerebras_api_key or not user_query:
        st.error("Missing Key or Query.")
    else:
        try:
            client = OpenAI(api_key=cerebras_api_key, base_url="https://api.cerebras.ai/v1")
            
            # PHASE 1: FOUNDATION (Temp 0.85)
            with st.spinner('PHASE 1: Architecting Foundation (Temp 0.85)...'):
                p1_sys = f"You are Phase 1 (Architect). Focus: Hierarchology (Micro/Meso/Macro) & IMA. Sciences: {sel_sciences}. Paradigm: {sel_paradigms}."
                p1_res = client.chat.completions.create(
                    model=cerebras_id, messages=[{"role": "system", "content": p1_sys}, {"role": "user", "content": user_query}],
                    temperature=0.85
                )
                phase1_out = p1_res.choices[0].message.content

            # PHASE 2: INNOVATION (Temp 0.65)
            with st.spinner('PHASE 2: Generating Innovations (Temp 0.65)...'):
                p2_sys = f"You are Phase 2 (Innovator). Apply Ideation Techniques: {sel_techniques}. Break the Scientific Cage using Mental Approaches (MA)."
                p2_prompt = f"Foundation Context:\n{phase1_out}\n\nInnovation Targets: {innovation_goal}"
                p2_res = client.chat.completions.create(
                    model=cerebras_id, messages=[{"role": "system", "content": p2_sys}, {"role": "user", "content": p2_prompt}],
                    temperature=0.65
                )
                phase2_out = p2_res.choices[0].message.content

            # PHASE 3: SYNTHESIS (Temp 0.4)
            with st.spinner('PHASE 3: Final Hierarchography & Mapping (Temp 0.4)...'):
                p3_sys = "You are Phase 3 (Integrator). Finalize the 18D report. End with '### SEMANTIC_GRAPH_JSON' + valid JSON."
                p3_prompt = f"Data:\n{phase1_out}\n{phase2_out}\n\nConsolidate and create the semantic network."
                p3_res = client.chat.completions.create(
                    model=cerebras_id, messages=[{"role": "system", "content": p3_sys}, {"role": "user", "content": p3_prompt}],
                    temperature=0.4
                )
                phase3_out = p3_res.choices[0].message.content

            # --- DISPLAY INTEGRATED RESULTS ---
            full_report = f"# 🎓 SIS Universal Synthesis\n\n## 🏛️ Phase 1: Foundation\n{phase1_out}\n\n## 💡 Phase 2: Innovations\n{phase2_out}\n\n## 🧬 Phase 3: Final Synthesis\n{phase3_out}"
            parts = full_report.split("### SEMANTIC_GRAPH_JSON")
            st.markdown(parts[0], unsafe_allow_html=True)

            if len(parts) > 1:
                try:
                    g_json = json.loads(re.search(r'\{.*\}', parts[1], re.DOTALL).group())
                    elements = []
                    for n in g_json.get("nodes", []):
                        elements.append({"data": {"id": n["id"], "label": n["label"], "color": n.get("color", "#fd7e14"), "shape": n.get("shape", "rectangle")}})
                    for e in g_json.get("edges", []):
                        elements.append({"data": {"source": e["source"], "target": e["target"], "rel": e.get("rel_type", "leads_to")}})
                    render_cytoscape_network(elements)
                except: st.warning("Graph rendering failed.")

        except Exception as e:
            st.error(f"Error: {e}")

st.divider()
st.caption(f"SIS Triad | {VERSION_CODE} | Temperature Gradient Strategy: 0.85/0.65/0.4")





