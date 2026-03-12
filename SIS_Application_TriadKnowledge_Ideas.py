import streamlit as st
import json
import base64
import requests
import urllib.parse
import re
import time
from datetime import datetime
from openai import OpenAI
import streamlit.components.v1 as components

# =============================================================================
# 0. GLOBAL CONFIGURATION & AUTOMATED DATE
# =============================================================================
SYSTEM_DATE = datetime.now().strftime("%B %d, %Y")
VERSION_CODE = "v27.1.0-CEREBRAS-TRIAD-PURE"

st.set_page_config(
    page_title=f"SIS Cerebras Triad Synthesizer - {SYSTEM_DATE}",
    page_icon="🌳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- NUCLEAR CSS OVERRIDE ---
st.markdown("""
<style>
    [data-testid="stSidebar"] [data-testid="stIcon"],
    [data-testid="stSidebar"] button[data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebar"] span[data-testid="stExpanderIcon"] {
        display: none !important;
        visibility: hidden !important;
    }
    [data-testid="stSidebar"] {
        background-color: #fcfcfc !important;
        border-right: 2px solid #e9ecef !important;
        min-width: 380px !important;
    }
    [data-testid="stSidebar"] .stMarkdown p, 
    [data-testid="stSidebar"] label {
        color: #1d3557 !important;
        font-size: 0.98em !important;
        font-weight: 600 !important;
    }
    .stExpander {
        background-color: #ffffff !important;
        border: 1px solid #d8e2dc !important;
        border-radius: 12px !important;
        margin-bottom: 12px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05) !important;
    }
    .semantic-node-highlight {
        color: #e63946;
        font-weight: bold;
        border-bottom: 2px solid #e63946;
        padding: 0 2px;
        background-color: #fff1f2;
        border-radius: 4px;
        text-decoration: none !important;
    }
    .main-header-gradient {
        background: linear-gradient(90deg, #1d3557, #e63946);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.8rem;
    }
    .date-badge {
        background-color: #1d3557;
        color: white;
        padding: 12px 20px;
        border-radius: 50px;
        font-size: 1em;
        font-weight: 800;
        margin-bottom: 30px;
        display: block;
        text-align: center;
    }
    .hierarchology-box {
        padding: 25px;
        border-radius: 15px;
        background-color: #fff4e6;
        border-left: 8px solid #fd7e14;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

def get_svg_base64(svg_str):
    return base64.b64encode(svg_str.encode('utf-8')).decode('utf-8')

SVG_3D_RELIEF = """
<svg width="240" height="240" viewBox="0 0 240 240" xmlns="http://www.w3.org/2000/svg">
    <circle cx="120" cy="120" r="100" fill="#f0f0f0" stroke="#000000" stroke-width="4" />
    <path d="M120 40 L50 180 L120 200 Z" fill="#bdbdbd" />
    <path d="M120 40 L190 180 L120 200 Z" fill="#9e9e9e" />
    <circle cx="120" cy="85" r="30" fill="#e63946" />
</svg>
"""

# =============================================================================
# 1. CORE RENDERING ENGINES
# =============================================================================

def render_cytoscape_network(elements, container_id="cy_cerebras_triad"):
    cyto_html = f"""
    <div style="position: relative; width: 100%;">
        <div id="{container_id}" style="width: 100%; height: 750px; background: #ffffff; border-radius: 20px; border: 1px solid #e0e0e0;"></div>
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.26.0/cytoscape.min.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            var cy = cytoscape({{
                container: document.getElementById('{container_id}'),
                elements: {json.dumps(elements)},
                style: [
                    {{ selector: 'node', style: {{ 'label': 'data(label)', 'text-valign': 'center', 'background-color': 'data(color)', 'width': 'data(size)', 'height': 'data(size)', 'shape': 'data(shape)', 'font-size': '14px', 'font-weight': '700' }} }},
                    {{ selector: 'edge', style: {{ 'width': 4, 'line-color': '#adb5bd', 'label': 'data(rel_type)', 'target-arrow-shape': 'triangle', 'curve-style': 'bezier', 'font-size': '10px' }} }}
                ],
                layout: {{ name: 'cose', padding: 60 }}
            }});
        }});
    </script>
    """
    components.html(cyto_html, height=850)

def fetch_author_bibliographies(author_input):
    if not author_input: return ""
    author_list = [a.strip() for a in author_input.split(",")]
    biblio = ""
    for auth in author_list:
        try:
            url = f"https://api.semanticscholar.org/graph/v1/paper/search?query=author:\"{auth}\"&limit=5&fields=title,year"
            res = requests.get(url, timeout=5).json()
            papers = res.get("data", [])
            if papers:
                biblio += f"\n--- {auth.upper()} ---\n"
                for p in papers: biblio += f"• ({p.get('year','n.d.')}) {p['title']}\n"
        except: pass
    return biblio

# =============================================================================
# 2. ONTOLOGIES
# =============================================================================

HIERARCHOLOGY_ONTOLOGY = {
    "dimensions": {
        "Micro-hierarchology": "Internal individual thinking and neural inductive logic.",
        "Meso-hierarchology": "Social groups, organizational structures, and intermediate systems.",
        "Macro-hierarchology": "Fundamental social laws, natural hierarchies, and universal orders.",
        "Scientific Cage": "Cognitive limitations preventing thought beyond established paradigms."
    },
    "logic_flows": {"Internal": "Inductive", "External": "Deductive & Dialectical"},
    "hierarchography_tools": ["Workflow Mapping", "Tree Maps", "Oligographs", "UML"]
}

HUMAN_THINKING_METAMODEL = {
    "nodes": {
        "Identity": {"color": "#C6EFCE", "shape": "rectangle"},
        "Mission": {"color": "#92D050", "shape": "rectangle"},
        "Problem": {"color": "#F2DCDB", "shape": "rectangle"},
        "Ethics": {"color": "#FFC000", "shape": "rectangle"}
    }
}

MENTAL_APPROACHES_ONTOLOGY = {
    "nodes": {
        "Dialectics": {"color": "#DDEBF7", "shape": "diamond"},
        "Perspective shifting": {"color": "#00FF00", "shape": "diamond"}
    }
}

IDEATION_TECHNIQUES = {
    "SCAMPER": "Substitute, Combine, Adapt, Modify, Put to another use, Eliminate, Reverse.",
    "First Principles": "Break down complex problems into basic elements and reassemble them.",
    "TRIZ": "Resolve technical or physical contradictions using systematic rules.",
    "Lateral Thinking": "Approach problems from unexpected angles."
}

# =============================================================================
# 3. KNOWLEDGE BASE
# =============================================================================

KNOWLEDGE_BASE = {
    "Science fields": ["Sociology", "Forensic sciences", "Neuroscience", "Physics", "Biology", "Psychology", "Computer Science", "Urbanism", "Geology", "Climatology", "Philosophy"],
    "Scientific paradigms": ["Rationalism", "Positivism", "Pragmatism", "Constructivism"],
    "Structural models": ["Causal Connections", "Principles & Relations", "Concepts"]
}

# =============================================================================
# 4. INTERFACE CONSTRUCTION
# =============================================================================

with st.sidebar:
    st.markdown(f'<div class="sidebar-logo-container"><img src="data:image/svg+xml;base64,{get_svg_base64(SVG_3D_RELIEF)}" width="220"></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="date-badge">{SYSTEM_DATE.upper()}</div>', unsafe_allow_html=True)
    st.header("⚙️ SYSTEM CONTROL")
    cerebras_api_key = st.text_input("Cerebras API Key:", type="password")
    cerebras_id = st.selectbox("Cerebras Model:", ["llama3.1-70b", "llama3.1-8b"], index=0)
    
    st.divider()
    target_authors = st.text_input("👤 Authors for Analysis:", placeholder="Karl Petrič, Samo Kralj")
    sel_sciences = st.multiselect("2. Select Science Fields:", sorted(KNOWLEDGE_BASE["Science fields"]), default=["Sociology", "Neuroscience"])
    sel_paradigms = st.multiselect("4. Scientific Paradigms:", KNOWLEDGE_BASE["Scientific paradigms"], default=["Rationalism"])
    sel_models = st.multiselect("5. Structural Models:", KNOWLEDGE_BASE["Structural models"], default=["Concepts"])
    
    st.divider()
    with st.expander("📚 KNOWLEDGE EXPLORER", expanded=False):
        for k, v in HIERARCHOLOGY_ONTOLOGY["dimensions"].items(): st.write(f"• {k}: {v}")
    with st.expander("💡 IDEATION TOOLS", expanded=False):
        for tech, desc in IDEATION_TECHNIQUES.items(): st.write(f"**{tech}**: {desc}")

st.markdown('<h1 class="main-header-gradient">🧱 SIS Cerebras Triad Engine</h1>', unsafe_allow_html=True)
st.markdown(f"**Pure Cerebras Hierarchology Pipeline** | {VERSION_CODE}")

user_query = st.text_area("❓ STEP 1: Research Inquiry (Factual/Structural):", height=150)
idea_query = st.text_area("💡 STEP 2: Innovation Goal (Generative/Practical):", height=150)
uploaded_file = st.file_uploader("📂 ATTACH DATA (.txt only):", type=['txt'])
file_content = uploaded_file.read().decode("utf-8") if uploaded_file else ""

# =============================================================================
# 5. TRIAD EXECUTION ENGINE (CEREBRAS ONLY: 0.85 -> 0.65 -> 0.45)
# =============================================================================

if st.button("🚀 EXECUTE CEREBRAS TRIAD PIPELINE", use_container_width=True):
    if not cerebras_api_key:
        st.error("❌ Cerebras API Key required.")
    elif not user_query:
        st.warning("⚠️ Inquiry required.")
    else:
        try:
            client = OpenAI(api_key=cerebras_api_key, base_url="https://api.cerebras.ai/v1")
            
            h_ont = json.dumps(HIERARCHOLOGY_ONTOLOGY)
            ima_str = json.dumps(HUMAN_THINKING_METAMODEL)
            ma_str = json.dumps(MENTAL_APPROACHES_ONTOLOGY)
            ideation_str = json.dumps(IDEATION_TECHNIQUES)

            # --- PHASE 1: CEREBRAS (VISIONARY FOUNDATION - 0.85) ---
            with st.spinner('PHASE 1: Cerebras establishing Visionary Foundation (0.85)...'):
                p1_prompt = f"""
                You are a Hierarchology Visionary. 
                IMA: {ima_str} | Basis: {h_ont} | Sciences: {str(sel_sciences)}
                TASK: Speculative foundation. Identify hidden hierarchies across MICRO, MESO and MACRO levels.
                """
                res_p1 = client.chat.completions.create(
                    model=cerebras_id,
                    messages=[{"role": "system", "content": p1_prompt}, {"role": "user", "content": user_query}],
                    temperature=0.85
                )
                foundation = res_p1.choices[0].message.content

            time.sleep(4) 

            # --- PHASE 2: CEREBRAS (INNOVATION BRAINSTORMING - 0.65) ---
            with st.spinner('PHASE 2: Cerebras generating radical ideas (0.65)...'):
                p2_prompt = f"""
                You are the Innovation Engine. 
                MA FOCUS: {ma_str} | TOOLBOX: {ideation_str} | SCIENCES: {str(sel_sciences)}
                TASK: Generate 5 radical ideas. Use 'Analogical Reasoning' from Hard Sciences to Social Stress.
                """
                res_p2 = client.chat.completions.create(
                    model=cerebras_id, 
                    messages=[{"role": "system", "content": p2_prompt}, {"role": "user", "content": f"F1:\n{foundation}\n\nGOAL:\n{idea_query}"}],
                    temperature=0.65
                )
                innovation_raw = res_p2.choices[0].message.content

            time.sleep(4)

            # --- PHASE 3: CEREBRAS (VETTING & STABLE JSON - 0.45) ---
            with st.spinner('PHASE 3: Final Vetting & Hierarchography Output (0.45)...'):
                p3_prompt = """
                Refine innovations into a 'Perfect 10' report. 
                CRITICAL: Use EXACT labels for ideas to enable text-linking.
                
                GRAPH MESH RULE: Connect every Innovation (star) to Micro (ellipse) AND Macro (octagon) nodes.
                
                VISUALS:
                - Ideas: "star" (#FFD700), Macro: "octagon" (#e63946), Meso: "rectangle" (#fd7e14), Micro: "ellipse" (#2a9d8f).
                - Relations: micro_to_meso, meso_to_macro, BT, NT, AS.
                
                Output report first, then strictly JSON between [START_JSON] and [END_JSON].
                """
                res_p3 = client.chat.completions.create(
                    model=cerebras_id,
                    messages=[{"role": "system", "content": p3_prompt}, {"role": "user", "content": f"F1:\n{foundation}\n\nI2:\n{innovation_raw}"}],
                    temperature=0.45
                )
                final_output = res_p3.choices[0].message.content

            # --- OBDELAVA PODATKOV ---
            display_text = final_output.split("[START_JSON]")[0] if "[START_JSON]" in final_output else final_output
            graph_json_str = ""
            start_idx = final_output.find('{')
            end_idx = final_output.rfind('}')
            if start_idx != -1 and end_idx != -1: graph_json_str = final_output[start_idx:end_idx+1]

            elements = []
            if graph_json_str:
                try:
                    g_json = json.loads(graph_json_str.strip().replace('```json', '').replace('```', ''))
                    nodes = g_json.get("nodes", [])
                    nodes.sort(key=lambda x: len(x.get("label", "")) if isinstance(x, dict) else len(str(x)), reverse=True)

                    for n in nodes:
                        lbl = n.get("label", n.get("id", "Node")) if isinstance(n, dict) else str(n)
                        nid = n.get("id", lbl) if isinstance(n, dict) else str(n)
                        shape = n.get("shape", "rectangle").lower() if isinstance(n, dict) else "rectangle"
                        
                        # Barvna logika (vsiljena v Pythonu)
                        color = "#fd7e14" # Default Meso
                        if shape == "star": color = "#FFD700"
                        elif shape == "octagon": color = "#e63946"
                        elif shape == "ellipse": color = "#2a9d8f"
                        elif shape == "diamond": color = "#9b59b6"

                        # Google Linker
                        if len(lbl) > 2:
                            g_url = urllib.parse.quote(lbl)
                            replacement = f'<a href="https://www.google.com/search?q={g_url}" target="_blank" class="semantic-node-highlight">{lbl}</a>'
                            display_text = re.compile(re.escape(lbl), re.IGNORECASE).sub(replacement, display_text)
                        
                        elements.append({"data": {"id": str(nid), "label": str(lbl), "color": color, "shape": shape, "size": 130 if shape == "star" else 105}})

                    for e in g_json.get("edges", []):
                        if isinstance(e, dict) and e.get("source") and e.get("target"):
                            elements.append({"data": {"source": str(e["source"]), "target": str(e["target"]), "rel_type": str(e.get("rel_type", "AS")).upper()}})
                except: pass

            # --- PRIKAZ ---
            st.subheader("📊 CEREBRAS TRIAD VERIFIED RESULTS")
            st.markdown(display_text, unsafe_allow_html=True)

            if elements:
                st.subheader("🕸️ CEREBRAS CONNECTIVE HIERARCHOGRAPHY")
                render_cytoscape_network(elements, f"viz_{int(time.time())}")

        except Exception as e:
            st.error(f"❌ Cerebras Triad Failure: {e}")

# =============================================================================
# 6. FOOTER
# =============================================================================
st.divider()
st.caption(f"SIS Pure Cerebras Engine | {VERSION_CODE} | {SYSTEM_DATE}")
































