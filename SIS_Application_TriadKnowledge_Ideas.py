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
# 0. GLOBALNA KONFIGURACIJA IN AVTOMATSKI DATUM
# =============================================================================
SYSTEM_DATE = datetime.now().strftime("%B %d, %Y")
VERSION_CODE = "v32.5.0-CEREBRAS-TRIAD-ULTIMATE"

st.set_page_config(
    page_title=f"SIS Universal Knowledge Synthesizer - {SYSTEM_DATE}",
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
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stExpander p {
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
        color: #e63946 !important;
        font-weight: bold !important;
        border-bottom: 2px solid #e63946 !important;
        padding: 0 2px;
        background-color: #fff1f2;
        border-radius: 4px;
        text-decoration: none !important;
    }
    .metamodel-box {
        padding: 25px; border-radius: 15px; background-color: #f8f9fa;
        border-left: 8px solid #00B0F0; margin-bottom: 20px;
    }
    .hierarchology-box {
        padding: 25px; border-radius: 15px; background-color: #fff4e6;
        border-left: 8px solid #fd7e14; margin-bottom: 20px;
    }
    .main-header-gradient {
        background: linear-gradient(90deg, #1d3557, #e63946);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800; font-size: 2.8rem;
    }
    .date-badge {
        background-color: #1d3557; color: white; padding: 12px 20px;
        border-radius: 50px; font-size: 1em; font-weight: 800;
        margin-bottom: 30px; display: block; text-align: center;
        box-shadow: 0 4px 15px rgba(29, 53, 87, 0.3);
    }
    .sidebar-logo-container { display: flex; justify-content: center; padding: 10px 0; margin-bottom: 5px; }
</style>
""", unsafe_allow_html=True)

def get_svg_base64(svg_str):
    return base64.b64encode(svg_str.encode('utf-8')).decode('utf-8')

# --- LOGOTIP: ORIGINAL 3D RELIEF ---
SVG_3D_RELIEF = """
<svg width="240" height="240" viewBox="0 0 240 240" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <filter id="reliefShadow" x="-20%" y="-20%" width="150%" height="150%">
            <feDropShadow dx="4" dy="4" stdDeviation="3" flood-color="#000" flood-opacity="0.4"/>
        </filter>
        <linearGradient id="pyramidSide" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#e0e0e0;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#bdbdbd;stop-opacity:1" />
        </linearGradient>
        <linearGradient id="treeGrad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" style="stop-color:#66bb6a;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#2e7d32;stop-opacity:1" />
        </linearGradient>
    </defs>
    <circle cx="120" cy="120" r="100" fill="#f0f0f0" stroke="#000000" stroke-width="4" filter="url(#reliefShadow)" />
    <path d="M120 40 L50 180 L120 200 Z" fill="url(#pyramidSide)" />
    <path d="M120 40 L190 180 L120 200 Z" fill="#9e9e9e" />
    <rect x="116" y="110" width="8" height="70" rx="2" fill="#5d4037" />
    <circle cx="120" cy="85" r="30" fill="url(#treeGrad)" filter="url(#reliefShadow)" />
    <circle cx="95" cy="125" r="22" fill="#43a047" filter="url(#reliefShadow)" />
    <circle cx="145" cy="125" r="22" fill="#43a047" filter="url(#reliefShadow)" />
    <rect x="70" y="170" width="20" height="12" rx="2" fill="#1565c0" filter="url(#reliefShadow)" />
    <rect x="150" y="170" width="20" height="12" rx="2" fill="#c62828" filter="url(#reliefShadow)" />
    <rect x="110" y="185" width="20" height="12" rx="2" fill="#f9a825" filter="url(#reliefShadow)" />
</svg>
"""

# =============================================================================
# 1. RENDERING ENGINE & API FETCH
# =============================================================================

def render_cytoscape_network(elements, container_id="cy_mesh"):
    cyto_html = f"""
    <div style="position: relative; width: 100%;">
        <button id="save_btn" style="position: absolute; top: 15px; right: 15px; z-index: 1000; padding: 12px 18px; background: #2a9d8f; color: white; border: none; border-radius: 8px; cursor: pointer; font-family: sans-serif; font-size: 13px; font-weight: 800;">💾 EXPORT GRAPH PNG</button>
        <div id="{container_id}" style="width: 100%; height: 750px; background: #ffffff; border-radius: 20px; border: 1px solid #e0e0e0; box-shadow: 0 8px 30px rgba(0,0,0,0.06);"></div>
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.26.0/cytoscape.min.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            var cy = cytoscape({{
                container: document.getElementById('{container_id}'),
                elements: {json.dumps(elements)},
                style: [
                    {{ selector: 'node', style: {{ 'label': 'data(label)', 'text-valign': 'center', 'color': '#212529', 'background-color': 'data(color)', 'width': 'data(size)', 'height': 'data(size)', 'shape': 'data(shape)', 'font-size': '14px', 'font-weight': '700' }} }},
                    {{ selector: 'edge', style: {{ 'width': 4, 'line-color': '#adb5bd', 'label': 'data(rel_type)', 'target-arrow-shape': 'triangle', 'curve-style': 'bezier', 'font-size': '10px', 'color': '#1d3557' }} }}
                ],
                layout: {{ name: 'cose', padding: 60 }}
            }});
            document.getElementById('save_btn').addEventListener('click', function() {{
                var png64 = cy.png({{ full: true, bg: 'white', scale: 2 }});
                var link = document.createElement('a');
                link.href = png64; link.download = 'sis_graph.png';
                document.body.appendChild(link); link.click(); document.body.removeChild(link);
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
# 2. ONTOLOGIJE (CELOTNI SEZNAMI)
# =============================================================================

HUMAN_THINKING_METAMODEL = {
    "nodes": {
        "Human mental concentration": {"color": "#ADB5BD", "shape": "rectangle"},
        "Identity": {"color": "#C6EFCE", "shape": "rectangle"},
        "Autobiographical memory": {"color": "#C6EFCE", "shape": "rectangle"},
        "Mission": {"color": "#92D050", "shape": "rectangle"},
        "Vision": {"color": "#FFFF00", "shape": "rectangle"},
        "Goal": {"color": "#00B0F0", "shape": "rectangle"},
        "Problem": {"color": "#F2DCDB", "shape": "rectangle"},
        "Ethics/moral": {"color": "#FFC000", "shape": "rectangle"},
        "Hierarchy of interests": {"color": "#F8CBAD", "shape": "rectangle"},
        "Rule": {"color": "#F2F2F2", "shape": "rectangle"},
        "Decision-making": {"color": "#FFFF99", "shape": "rectangle"},
        "Problem solving": {"color": "#D9D9D9", "shape": "rectangle"},
        "Conflict situation": {"color": "#00FF00", "shape": "rectangle"},
        "Knowledge": {"color": "#DDEBF7", "shape": "rectangle"},
        "Tool": {"color": "#00B050", "shape": "rectangle"},
        "Experience": {"color": "#00B050", "shape": "rectangle"},
        "Classification": {"color": "#CCC0DA", "shape": "rectangle"},
        "Psychological aspect": {"color": "#F8CBAD", "shape": "rectangle"},
        "Sociological aspect": {"color": "#00FFFF", "shape": "rectangle"}
    }
}

MENTAL_APPROACHES_ONTOLOGY = {
    "nodes": {
        "Perspective shifting": {"color": "#00FF00", "shape": "diamond"},
        "Similarity and difference": {"color": "#FFFF00", "shape": "diamond"},
        "Core": {"color": "#FFC000", "shape": "diamond"},
        "Attraction": {"color": "#F2A6A2", "shape": "diamond"},
        "Repulsion": {"color": "#D9D9D9", "shape": "diamond"},
        "Condensation": {"color": "#CCC0DA", "shape": "diamond"},
        "Framework and foundation": {"color": "#F8CBAD", "shape": "diamond"},
        "Bipolarity and dialectics": {"color": "#DDEBF7", "shape": "diamond"},
        "Constant": {"color": "#E1C1D1", "shape": "diamond"},
        "Associativity": {"color": "#E1C1D1", "shape": "diamond"},
        "Induction": {"color": "#B4C6E7", "shape": "diamond"},
        "Whole and part": {"color": "#00FF00", "shape": "diamond"},
        "Mini-max": {"color": "#00FF00", "shape": "diamond"},
        "Addition and composition": {"color": "#FF00FF", "shape": "diamond"},
        "Hierarchy": {"color": "#C6EFCE", "shape": "diamond"},
        "Balance": {"color": "#00B0F0", "shape": "diamond"},
        "Deduction": {"color": "#92D050", "shape": "diamond"},
        "Abstraction and elimination": {"color": "#00B0F0", "shape": "diamond"},
        "Pleasure and displeasure": {"color": "#00FF00", "shape": "diamond"},
        "Openness and closedness": {"color": "#FFC000", "shape": "diamond"}
    }
}

HIERARCHOLOGY_ONTOLOGY = {
    "dimensions": {
        "Micro-hierarchology": "Internal neural logic.",
        "Meso-hierarchology": "Social organizations.",
        "Macro-hierarchology": "Societal laws.",
        "Scientific Cage": "Cognitive limitations."
    },
    "hierarchography_tools": ["Workflow Mapping", "Tree Maps", "Structural diagrams", "Oligographs", "UML", "Mind Mapping"]
}

IDEATION_TECHNIQUES = {
    "SCAMPER": "Substitute, Combine, Adapt, Modify, Put to another use, Eliminate, Reverse.",
    "First Principles": "Break down complex problems into basic elements.",
    "TRIZ": "Resolve technical contradictions using systematic innovation rules.",
    "Lateral Thinking": "Approach problems from unexpected angles.",
    "Reverse Ideation": "Think of causing the problem, then reverse steps."
}

# =============================================================================
# 3. KNOWLEDGE BASE
# =============================================================================

KNOWLEDGE_BASE = {
    "Science fields": [
        "Mathematics", "Physics", "Chemistry", "Biology", "Neuroscience", "Psychology", 
        "Sociology", "Computer Science", "Legal science", "Economics", "Forensic sciences", 
        "Engineering", "Medicine", "Psychiatry", "Geology", "Climatology", "Philosophy", 
        "Architecture", "History", "Ecology", "Geography", "Linguistics", "Library Science", "Criminology"
    ],
    "Scientific paradigms": {
        "Empiricism": "Focus on sensory experience.",
        "Rationalism": "Reliance on deductive logic.",
        "Constructivism": "Knowledge as social build.",
        "Positivism": "Strict verifiable facts.",
        "Pragmatism": "Evaluation by utility."
    },
    "Structural models": ["Causal Connections", "Principles & Relations", "Concepts", "Glossary", "Episodes", "Generalizations"]
}

# =============================================================================
# 4. VMESNIK (SIDEBAR IN MAIN AREA)
# =============================================================================

with st.sidebar:
    st.markdown(f'<div class="sidebar-logo-container"><img src="data:image/svg+xml;base64,{get_svg_base64(SVG_3D_RELIEF)}" width="220"></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="date-badge">{SYSTEM_DATE.upper()}</div>', unsafe_allow_html=True)
    st.header("⚙️ SYSTEM CONTROL")
    cerebras_api_key = st.text_input("Cerebras API Key:", type="password")
    cerebras_id = st.selectbox("Model Endpoint:", ["llama3.1-70b", "llama3.1-8b"], index=0)
    
    st.divider()
    target_authors = st.text_input("👤 Authors for Analysis:", placeholder="Karl Petrič, Samo Kralj")
    sel_sciences = st.multiselect("2. Science Fields:", sorted(KNOWLEDGE_BASE["Science fields"]), default=["Sociology", "Forensic sciences", "Physics"])
    sel_paradigms = st.multiselect("4. Paradigms:", list(KNOWLEDGE_BASE["Scientific paradigms"].keys()), default=["Empiricism", "Rationalism"])
    sel_models = st.multiselect("5. Models:", KNOWLEDGE_BASE["Structural models"], default=["Concepts", "Causal Connections"])
    
    st.divider()
    with st.expander("📚 HIERARCHOLOGY EXPLORER"):
        for k, v in HIERARCHOLOGY_ONTOLOGY["dimensions"].items(): st.write(f"• **{k}**: {v}")
    with st.expander("🧠 MENTAL APPROACHES"):
        for m in sorted(MENTAL_APPROACHES_ONTOLOGY["nodes"].keys()): st.write(f"• {m}")

st.markdown('<h1 class="main-header-gradient">🧱 SIS Cerebras Triad Engine</h1>', unsafe_allow_html=True)

# VNOSNA POLJA IN PRIPENJANJE DATOTEKE
c1, c2 = st.columns([2, 1])
with c1:
    user_query = st.text_area("❓ STEP 1: Research Inquiry (Speculative):", height=120)
    idea_query = st.text_area("💡 STEP 2: Innovation Goal (Practical):", height=120)
with c2:
    uploaded_file = st.file_uploader("📂 ATTACH DATA (.txt only):", type=['txt'])
    file_content = uploaded_file.read().decode("utf-8") if uploaded_file else ""
    if uploaded_file: st.success("Data integrated.")

# =============================================================================
# 5. SYNERGY ENGINE (TRIAD LOOP: 0.85 -> 0.65 -> 0.45)
# =============================================================================

if st.button("🚀 EXECUTE CEREBRAS TRIAD PIPELINE", use_container_width=True):
    if not cerebras_api_key:
        st.error("❌ Cerebras API Key required.")
    else:
        try:
            client = OpenAI(api_key=cerebras_api_key, base_url="https://api.cerebras.ai/v1")
            
            # --- PHASE 1: VISIONARY (0.85) ---
            with st.spinner('Faza 1: Vizionarska podlaga...'):
                p1_c = f"Hierarchology Visionary. IMA: {json.dumps(HUMAN_THINKING_METAMODEL)}. Sciences: {str(sel_sciences)}. Context: {file_content}"
                res_p1 = client.chat.completions.create(model=cerebras_id, messages=[{"role": "system", "content": p1_c}, {"role": "user", "content": user_query}], temperature=0.85)
                foundation = res_p1.choices[0].message.content

            time.sleep(4)

            # --- PHASE 2: INNOVATION (0.65) ---
            with st.spinner('Faza 2: Brainstorming inovacij...'):
                p2_c = f"Innovation Engine. MA Logic: {json.dumps(MENTAL_APPROACHES_ONTOLOGY)}. Toolbox: {json.dumps(IDEATION_TECHNIQUES)}."
                res_p2 = client.chat.completions.create(model=cerebras_id, messages=[{"role": "system", "content": p2_c}, {"role": "user", "content": f"F1:\n{foundation}\n\nGOAL:\n{idea_query}"}], temperature=0.65)
                innovation_raw = res_p2.choices[0].message.content

            time.sleep(4)

            # --- PHASE 3: VETTING & JSON (0.45) ---
            with st.spinner('Faza 3: Končna verifikacija in Hierarhografija...'):
                p3_prompt = """Refine into a 'Perfect 10' report. Use exact node labels. 
                Visual Rules for JSON: Innovations (star, #FFD700), Macro (octagon, #e63946), Meso (rectangle, #fd7e14), Micro (ellipse, #2a9d8f).
                End strictly with '### JSON_DATA' followed by valid JSON structure."""
                res_p3 = client.chat.completions.create(model=cerebras_id, messages=[{"role": "system", "content": p3_prompt}, {"role": "user", "content": f"F1:\n{foundation}\n\nI2:\n{innovation_raw}"}], temperature=0.45)
                final_output = res_p3.choices[0].message.content

            # --- DISTRIBUTING DATA & LINKS Mehanizem ---
            display_text = final_output.split("### JSON_DATA")[0]
            graph_json_str = ""
            s_idx = final_output.find('{')
            e_idx = final_output.rfind('}')
            if s_idx != -1 and e_idx != -1: graph_json_str = final_output[s_idx:e_idx+1]

            elements = []
            if graph_json_str:
                try:
                    g_json = json.loads(graph_json_str.strip())
                    nodes = g_json.get("nodes", [])
                    # Razvrstimo vozlišča po dolžini imena (najprej dolga), da se izognemo napačnim zamenjavam v linkih
                    nodes.sort(key=lambda x: len(x.get("label", "")) if isinstance(x, dict) else len(str(x)), reverse=True)

                    for n in nodes:
                        lbl = n.get("label", n.get("id", "Node")) if isinstance(n, dict) else str(n)
                        nid = n.get("id", lbl) if isinstance(n, dict) else str(n)
                        shape = n.get("shape", "rectangle").lower() if isinstance(n, dict) else "rectangle"
                        color = n.get("color", "#fd7e14") if isinstance(n, dict) else "#fd7e14"

                        # Google Search Linking (Fuzzy CASE-INSENSITIVE)
                        g_url = urllib.parse.quote(lbl)
                        replacement = f'<a href="https://www.google.com/search?q={g_url}" target="_blank" class="semantic-node-highlight">{lbl}</a>'
                        pattern = re.compile(re.escape(lbl), re.IGNORECASE)
                        display_text = pattern.sub(replacement, display_text)
                        
                        elements.append({"data": {"id": str(nid), "label": str(lbl), "color": color, "shape": shape, "size": 130 if shape == "star" else 105}})

                    for e in g_json.get("edges", []):
                        if isinstance(e, dict) and e.get("source") and e.get("target"):
                            elements.append({"data": {"source": str(e["source"]), "target": str(e["target"]), "rel_type": str(e.get("rel_type", "AS")).upper()}})
                except: pass

            st.subheader("📊 FINAL TRIAD VERIFIED RESULTS")
            st.markdown(display_text, unsafe_allow_html=True)
            if elements:
                st.subheader("🕸️ FINAL CONNECTIVE HIERARCHOGRAPHY")
                render_cytoscape_network(elements, f"viz_{int(time.time())}")

        except Exception as e:
            st.error(f"❌ Triad Failure: {e}")

st.divider()
st.caption(f"SIS Universal Triad Engine | {VERSION_CODE} | {SYSTEM_DATE}")
