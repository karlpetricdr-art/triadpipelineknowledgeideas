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
# 0. GLOBAL CONFIGURATION
# =============================================================================
SYSTEM_DATE = datetime.now().strftime("%B %d, %Y")
VERSION_CODE = "v23.1.0-CEREBRAS-TRIAD"

st.set_page_config(
    page_title=f"SIS Triad Synthesizer - {SYSTEM_DATE}",
    page_icon="🌳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- NUCLEAR CSS OVERRIDE ---
st.markdown("""
<style>
    [data-testid="stSidebar"] [data-testid="stIcon"],
    [data-testid="stSidebar"] button[data-testid="stSidebarCollapseButton"] { display: none !important; }
    [data-testid="stSidebar"] { background-color: #fcfcfc !important; border-right: 2px solid #e9ecef !important; min-width: 380px !important; }
    [data-testid="stSidebar"] .stMarkdown p, label { color: #1d3557 !important; font-weight: 500 !important; }
    .stExpander { background-color: #f8f9fa !important; border-radius: 12px !important; margin-bottom: 10px !important; }
    .semantic-node-highlight { color: #2a9d8f; font-weight: bold; border-bottom: 2px solid #2a9d8f; text-decoration: none !important; }
    .metamodel-box { padding: 20px; border-radius: 15px; background-color: #f8f9fa; border-left: 8px solid #00B0F0; margin-bottom: 20px; }
    .mental-approach-box { padding: 20px; border-radius: 15px; background-color: #f0f7ff; border-left: 8px solid #6366f1; margin-bottom: 20px; }
    .main-header-gradient { background: linear-gradient(90deg, #1d3557, #457b9d); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800; font-size: 2.5rem; }
    .date-badge { background-color: #1d3557; color: white; padding: 10px; border-radius: 50px; text-align: center; font-weight: 800; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 1. CORE UTILITIES & ONTOLOGIES
# =============================================================================

HUMAN_THINKING_METAMODEL = {
    "nodes": {
        "Identity": {"color": "#C6EFCE", "shape": "rectangle", "desc": "Subjective core/ethical parameters."},
        "Mission": {"color": "#92D050", "shape": "rectangle", "desc": "Existential imperative."},
        "Goal": {"color": "#00B0F0", "shape": "rectangle", "desc": "Quantifiable milestones."},
        "Problem": {"color": "#F2DCDB", "shape": "rectangle", "desc": "Gaps/Obstructions."}
    }
}

MENTAL_APPROACHES_ONTOLOGY = {
    "nodes": {
        "Perspective shifting": {"color": "#00FF00", "shape": "diamond", "desc": "Stakeholder rotation."},
        "Dialectics": {"color": "#DDEBF7", "shape": "diamond", "desc": "Synthesis through tension."},
        "Induction": {"color": "#B4C6E7", "shape": "diamond", "desc": "Theory building."}
    }
}

KNOWLEDGE_BASE = {
    "Science fields": ["Physics", "Psychology", "Sociology", "Mathematics", "Neuroscience", "Economics", "Computer Science"],
    "Paradigms": ["Rationalism", "Empiricism", "Constructivism", "Pragmatism"],
    "Models": ["Concepts", "Causal Connections", "Principles & Relations"]
}

def render_cytoscape_network(elements, container_id="cy_triad"):
    cyto_html = f"""
    <div id="{container_id}" style="width: 100%; height: 600px; background: #ffffff; border-radius: 20px; border: 1px solid #e0e0e0;"></div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.26.0/cytoscape.min.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            var cy = cytoscape({{
                container: document.getElementById('{container_id}'),
                elements: {json.dumps(elements)},
                style: [
                    {{ selector: 'node', style: {{ 'label': 'data(label)', 'background-color': 'data(color)', 'shape': 'data(shape)', 'width': 80, 'height': 80, 'font-size': '12px', 'text-valign': 'center' }} }},
                    {{ selector: 'edge', style: {{ 'width': 3, 'line-color': '#adb5bd', 'target-arrow-shape': 'triangle', 'curve-style': 'bezier' }} }}
                ],
                layout: {{ name: 'cose', padding: 50 }}
            }});
        }});
    </script>
    """
    components.html(cyto_html, height=650)

def fetch_author_bibliographies(author_input):
    if not author_input: return ""
    return f"Bibliographic placeholder for: {author_input}" # Simplified for this build

# =============================================================================
# 2. SIDEBAR (CEREBRAS ONLY)
# =============================================================================

with st.sidebar:
    st.markdown(f'<div class="date-badge">{SYSTEM_DATE.upper()}</div>', unsafe_allow_html=True)
    st.header("⚙️ SYSTEM CONTROL")
    
    # ONLY CEREBRAS KEY
    cerebras_api_key = st.text_input("🔑 Cerebras API Key:", type="password")
    cerebras_id = st.selectbox("Model Endpoint:", ["llama-3.1-70b", "llama3.1-8b"], index=0)
    
    st.divider()
    if st.button("♻️ RESET SYSTEM"):
        st.rerun()

    st.subheader("📚 KNOWLEDGE EXPLORER")
    with st.expander("🏛️ IMA Metamodel", expanded=False):
        for n, d in HUMAN_THINKING_METAMODEL["nodes"].items(): st.markdown(f"• **{n}**: {d['desc']}")
    with st.expander("🧠 MA Approaches", expanded=False):
        for n, d in MENTAL_APPROACHES_ONTOLOGY["nodes"].items(): st.markdown(f"• **{n}**: {d['desc']}")

# =============================================================================
# 3. MAIN INTERFACE
# =============================================================================

st.markdown('<h1 class="main-header-gradient">🧱 SIS Triad Knowledge Synthesizer</h1>', unsafe_allow_html=True)
st.info("**Triad System Pipeline (Cerebras Exclusive)**: Phase 1 (0.85) → Phase 2 (0.65) → Phase 3 (0.4)")

col1, col2 = st.columns(2)
with col1:
    target_authors = st.text_input("👤 Authors:", placeholder="e.g. Karl Petrič")
    sel_sciences = st.multiselect("Sciences:", KNOWLEDGE_BASE["Science fields"], default=["Physics"])
with col2:
    sel_paradigms = st.multiselect("Paradigms:", KNOWLEDGE_BASE["Paradigms"], default=["Rationalism"])
    expertise = st.select_slider("Level:", ["Novice", "Expert"])

st.divider()
col_inq1, col_inq2 = st.columns(2)
with col_inq1:
    user_query = st.text_area("❓ STEP 1: Research Inquiry (Foundation):", placeholder="The factual starting point...", height=150)
with col_inq2:
    idea_query = st.text_area("💡 STEP 2: Innovation Prompt (Idea Targets):", placeholder="What specific innovations should we target?", height=150)

# =============================================================================
# 4. TRIAD EXECUTION ENGINE
# =============================================================================

if st.button("🚀 EXECUTE CEREBRAS TRIAD PIPELINE", use_container_width=True):
    if not cerebras_api_key:
        st.error("❌ Please provide a Cerebras API Key in the sidebar.")
    elif not user_query:
        st.warning("⚠️ Inquiry required.")
    else:
        try:
            client = OpenAI(api_key=cerebras_api_key, base_url="https://api.cerebras.ai/v1")
            
            # --- PHASE 1: FOUNDATION (TEMP 0.85) ---
            with st.spinner('PHASE 1: Establishing Foundation (Temp 0.85)...'):
                p1_sys = f"You are Phase 1 (Architect). Focus: IMA Architecture. Sciences: {sel_sciences}."
                p1_res = client.chat.completions.create(
                    model=cerebras_id,
                    messages=[{"role": "system", "content": p1_sys}, {"role": "user", "content": user_query}],
                    temperature=0.85
                )
                p1_text = p1_res.choices[0].message.content

            # --- PHASE 2: INNOVATION (TEMP 0.65) ---
            with st.spinner('PHASE 2: Generating Innovations (Temp 0.65)...'):
                p2_sys = f"You are Phase 2 (Innovator). Use Mental Approaches (MA) like Dialectics and Perspective Shifting."
                p2_prompt = f"Foundation Context:\n{p1_text}\n\nUser Innovation Goal: {idea_query}"
                p2_res = client.chat.completions.create(
                    model=cerebras_id,
                    messages=[{"role": "system", "content": p2_sys}, {"role": "user", "content": p2_prompt}],
                    temperature=0.65
                )
                p2_text = p2_res.choices[0].message.content

            # --- PHASE 3: SYNTHESIS & GRAPH (TEMP 0.4) ---
            with st.spinner('PHASE 3: Final Logic & Mapping (Temp 0.4)...'):
                p3_sys = f"""You are Phase 3 (Integrator). Consolidate all phases into a rigorous 18D report. 
                End your response with '### SEMANTIC_GRAPH_JSON' followed by a JSON network using:
                Nodes: {{"id": "n1", "label": "Text", "color": "#hex", "shape": "rectangle|diamond"}}.
                Edges: {{"source": "n1", "target": "n2", "rel_type": "leads_to"}}."""
                
                p3_prompt = f"Phase 1 Foundation:\n{p1_text}\n\nPhase 2 Innovations:\n{p2_text}\n\nFinalize logic and create graph."
                p3_res = client.chat.completions.create(
                    model=cerebras_id,
                    messages=[{"role": "system", "content": p3_sys}, {"role": "user", "content": p3_prompt}],
                    temperature=0.4
                )
                p3_text = p3_res.choices[0].message.content

            # --- DISPLAY ---
            st.divider()
            full_content = f"## 📚 Phase 1: Foundation\n{p1_text}\n\n## 💡 Phase 2: Innovations\n{p2_text}\n\n## 🏛️ Phase 3: Final Synthesis\n{p3_text}"
            
            parts = full_content.split("### SEMANTIC_GRAPH_JSON")
            main_markdown = parts[0]
            
            # Process Semantic Links
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

            if len(parts) > 1:
                try:
                    g_json = json.loads(re.search(r'\{.*\}', parts[1], re.DOTALL).group())
                    elements = []
                    for n in g_json.get("nodes", []):
                        elements.append({"data": {"id": n["id"], "label": n["label"], "color": n.get("color", "#2a9d8f"), "shape": n.get("shape", "rectangle")}})
                    for e in g_json.get("edges", []):
                        elements.append({"data": {"source": e["source"], "target": e["target"]}})
                    render_cytoscape_network(elements)
                except: st.error("Failed to render graph JSON.")

        except Exception as e:
            st.error(f"Execution Error: {e}")

st.divider()
st.caption(f"SIS Triad Synthesizer | {VERSION_CODE} | Operating Date: {SYSTEM_DATE}")


