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
VERSION_CODE = "v34.5.0-CEREBRAS-TRIAD-ELITE-COMPLETE-980"

st.set_page_config(
    page_title=f"SIS Universal Knowledge Synthesizer - {SYSTEM_DATE}",
    page_icon="🌳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- NUCLEAR CSS OVERRIDE: OBLITERATING SIDEBAR ARTIFACTS & FIXING VISIBILITY ---
st.markdown("""
<style>
    [data-testid="stSidebar"] [data-testid="stIcon"],
    [data-testid="stSidebar"] button[data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebar"] span[data-testid="stExpanderIcon"],
    [data-testid="stSidebar"] svg[class*="st-emotion-cache"] {
        display: none !important;
        visibility: hidden !important;
        width: 0 !important; height: 0 !important; opacity: 0 !important;
    }

    [data-testid="stSidebar"] {
        background-color: #fcfcfc !important;
        border-right: 2px solid #e9ecef !important;
        min-width: 380px !important;
    }

    [data-testid="stSidebar"] .stMarkdown p, 
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stExpander p,
    [data-testid="stSidebar"] .stMarkdown span {
        color: #1d3557 !important;
        font-size: 0.98em !important;
        font-weight: 600 !important;
        line-height: 1.6 !important;
    }

    .stExpander {
        background-color: #ffffff !important;
        border: 1px solid #d8e2dc !important;
        border-radius: 12px !important;
        margin-bottom: 12px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05) !important;
    }
    
    .stExpander details summary p {
        color: #1d3557 !important;
        font-weight: 800 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
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

    .stButton>button {
        width: 100%; border-radius: 10px; font-weight: 700;
        text-transform: uppercase; letter-spacing: 1px;
    }
</style>
""", unsafe_allow_html=True)

def get_svg_base64(svg_str):
    return base64.b64encode(svg_str.encode('utf-8')).decode('utf-8')

# --- LOGOTIP: ORIGINAL 3D RELIEF (PYRAMID & TREE RESTORED EXACTLY) ---
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
# 1. RENDERING ENGINES & DATA FETCHING
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
                var png64 = cy.png({{ full: true, bg: 'white', scale: 2.5 }});
                var link = document.createElement('a');
                link.href = png64; link.download = 'sis_synergy_graph.png';
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
            ss_url = f"https://api.semanticscholar.org/graph/v1/paper/search?query=author:\"{auth}\"&limit=5&fields=title,year"
            ss_res = requests.get(ss_url, timeout=5).json()
            papers = ss_res.get("data", [])
            if papers:
                biblio += f"\n--- SCHOLAR DATA: {auth.upper()} ---\n"
                for p in papers: biblio += f"• ({p.get('year','n.d.')}) {p['title']}\n"
        except: pass
    return biblio

# =============================================================================
# 2. ARCHITECTURAL ONTOLOGIES (POPOLNI SEZNAMI)
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
    "core_definitions": {
        "Hierarchology": "Interdisciplinary science studying hierarchical associative systems.",
        "Hierarchography": "Descriptive visual mapping of complex topics via workflows and diagrammatic logic.",
        "Scientific Cage": "Cognitive limitations preventing thought beyond established paradigms."
    },
    "hierarchical_levels": {
        "Micro-hierarchology": "Individual thinking and neural inductive logic.",
        "Meso-hierarchology": "Social groups and organizational systems.",
        "Macro-hierarchology": "Fundamental social laws and natural hierarchies."
    }
}

IDEATION_TECHNIQUES = {
    "SCAMPER": "Substitute, Combine, Adapt, Modify, Put to another use, Eliminate, Reverse.",
    "First Principles": "Break down complex problems into basic elements and reassemble them.",
    "TRIZ": "Resolve contradictions using systematic innovation rules.",
    "Lateral Thinking": "Unexpected angles and logic jumps.",
    "Reverse Ideation": "Think of causing the problem, then reverse steps."
}

# =============================================================================
# 3. KNOWLEDGE BASE (CELOTEN 18D+ SEZNAM)
# =============================================================================

KNOWLEDGE_BASE = {
    "Science fields": [
        "Mathematics", "Physics", "Chemistry", "Biology", "Neuroscience", "Psychology", 
        "Sociology", "Computer Science", "Legal science", "Economics", "Forensic sciences", 
        "Engineering", "Medicine", "Psychiatry", "Geology", "Climatology", "Philosophy", 
        "Architecture", "History", "Ecology", "Geography", "Linguistics", "Library Science", "Criminology"
    ],
    "Scientific paradigms": {
        "Empiricism": "Focus on sensory experience and data.",
        "Rationalism": "Reliance on deductive logic.",
        "Constructivism": "Knowledge as a social and cognitive build.",
        "Positivism": "Strict adherence to verifiable facts.",
        "Pragmatism": "Evaluation based on utility and application."
    },
    "Structural models": ["Causal Connections", "Principles & Relations", "Concepts", "Glossary", "Episodes & Sequences", "Generalizations", "Facts & Characteristics"]
}

# =============================================================================
# 4. INTERFACE CONSTRUCTION
# =============================================================================

with st.sidebar:
    st.markdown(f'<div class="sidebar-logo-container"><img src="data:image/svg+xml;base64,{get_svg_base64(SVG_3D_RELIEF)}" width="220"></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="date-badge">{SYSTEM_DATE.upper()}</div>', unsafe_allow_html=True)
    st.header("⚙️ SYSTEM CONTROL")
    cerebras_api_key = st.text_input("Cerebras API Key:", type="password")
    cerebras_id = st.selectbox("Model Endpoint:", ["llama3.1-70b", "llama3.1-8b"], index=0)
    
    st.divider()
    target_authors = st.text_input("👤 Authors for Analysis:", placeholder="Karl Petrič, Samo Kralj")
    sel_sciences = st.multiselect("2. Select Science Fields:", sorted(KNOWLEDGE_BASE["Science fields"]), default=["Sociology", "Forensic sciences", "Neuroscience", "Physics"])
    sel_paradigms = st.multiselect("4. Scientific Paradigms:", list(KNOWLEDGE_BASE["Scientific paradigms"].keys()), default=["Empiricism", "Rationalism", "Pragmatism"])
    sel_models = st.multiselect("5. Structural Models:", KNOWLEDGE_BASE["Structural models"], default=["Concepts", "Causal Connections"])
    
    st.divider()
    with st.expander("🏛️ IMA GRADNJAKI (19)", expanded=False):
        for k in sorted(HUMAN_THINKING_METAMODEL["nodes"].keys()): st.write(f"• {k}")
    with st.expander("🧠 MENTALNI PRISTOPI (20)", expanded=False):
        for m in sorted(MENTAL_APPROACHES_ONTOLOGY["nodes"].keys()): st.write(f"• {m}")
    with st.expander("📚 HIERARHOLOGIJA CORE", expanded=False):
        for k, v in HIERARCHOLOGY_ONTOLOGY["core_definitions"].items(): st.write(f"**{k}**: {v}")
    with st.expander("💡 IDEATION TOOLS", expanded=False):
        for tech, desc in IDEATION_TECHNIQUES.items(): st.write(f"**{tech}**: {desc}")

st.markdown('<h1 class="main-header-gradient">🧱 SIS Cerebras Triad Engine</h1>', unsafe_allow_html=True)
st.markdown(f"**Automated Pure Cerebras Triad Pipeline** | Operating Date: **{SYSTEM_DATE}**")

c1, c2 = st.columns([2, 1])
with c1:
    user_query = st.text_area("❓ STEP 1: Research Inquiry (Vizionarska faza):", height=120)
    idea_query = st.text_area("💡 STEP 2: Innovation Goal (Taktična faza):", height=120)
with c2:
    uploaded_file = st.file_uploader("📂 ATTACH DATA (.txt only):", type=['txt'])
    file_content = uploaded_file.read().decode("utf-8") if uploaded_file else ""
    if uploaded_file: st.success("Data integrated.")

# =============================================================================
# 5. SYNERGY ENGINE (TRIAD LOOP: 0.85 -> 0.65 -> 0.45)
# =============================================================================

if st.button("🚀 EXECUTE PURE CEREBRAS TRIAD PIPELINE", use_container_width=True):
    if not cerebras_api_key:
        st.error("❌ Cerebras API Key required.")
    elif not user_query:
        st.warning("⚠️ Phase 1 Inquiry required.")
    else:
        try:
            client = OpenAI(api_key=cerebras_api_key, base_url="https://api.cerebras.ai/v1")
            
            biblio = fetch_author_bibliographies(target_authors)
            ima_str = json.dumps(HUMAN_THINKING_METAMODEL)
            ma_str = json.dumps(MENTAL_APPROACHES_ONTOLOGY)
            h_ont = json.dumps(HIERARCHOLOGY_ONTOLOGY)
            tech_str = json.dumps(IDEATION_TECHNIQUES)

            # --- PHASE 1: VISIONARY DEVELOPMENT (0.85) ---
            with st.spinner('Faza 1: Generiranje vizionarske podlage (0.85)...'):
                p1_template = """You are a Hierarchology Visionary. 
                IMA: [IMA] | BASIS: [BASIS] | SCIENCES: [SCIENCES]
                TASK: speculative analysis of MICRO, MESO and MACRO hierarchies. 
                Use hard science analogies. Context: [FILE]"""
                p1_c = p1_template.replace("[IMA]", ima_str).replace("[BASIS]", h_ont).replace("[SCIENCES]", str(sel_sciences)).replace("[FILE]", file_content)
                res_p1 = client.chat.completions.create(model=cerebras_id, messages=[{"role": "system", "content": p1_c}, {"role": "user", "content": user_query}], temperature=0.85)
                foundation = res_p1.choices[0].message.content

            st.toast("Phase 1 complete. Cooling down API...")
            time.sleep(5) 

            # --- PHASE 2: TACTICAL INNOVATION (0.65) ---
            with st.spinner('Faza 2: Razvijanje inovacij (0.65)...'):
                p2_template = """You are the SIS Innovation Engine. MA FOCUS: [MA] | TOOLBOX: [TECH] | SCIENCES: [SCIENCES].
                TASK: Generate radical ideas using Analogical Reasoning and SCAMPER."""
                p2_c = p2_template.replace("[MA]", ma_str).replace("[TECH]", tech_str).replace("[SCIENCES]", str(sel_sciences))
                res_p2 = client.chat.completions.create(model=cerebras_id, messages=[{"role": "system", "content": p2_c}, {"role": "user", "content": f"F1 FOUNDATION:\n{foundation}\n\nGOAL:\n{idea_query}"}], temperature=0.65)
                innovation_raw = res_p2.choices[0].message.content

            st.toast("Phase 2 complete. Cooling down API...")
            time.sleep(5)

            # --- PHASE 3: FINAL SYNTHESIS & HIERARCHOGRAPHY (0.45) ---
            with st.spinner('PHASE 3: Finalna verifikacija in mrežni izris (0.45)...'):
                p3_prompt = """Refine into a 'Perfect 10' FINAL SYNERGY REPORT. 
                STRICT RULES:
                1. NO color codes (#...) or technical hex parameters in text.
                2. Use EXACT node labels for linking.
                3. HIERARCHOGRAPHY MESH in JSON: Innovations (star, #FFD700), Macro (octagon, #e63946), Meso (rectangle, #fd7e14), Micro (ellipse, #2a9d8f).
                Output Report, then strictly end with marker '### JSON_DATA' and valid JSON structure."""
                res_p3 = client.chat.completions.create(model=cerebras_id, messages=[{"role": "system", "content": p3_prompt}, {"role": "user", "content": f"F1+F2 IDEAS:\n{innovation_raw}"}], temperature=0.45)
                final_output = res_p3.choices[0].message.content

            # --- DISTRIBUTING DATA & LINKS Mehanizem ---
            display_text = final_output.split("### JSON_DATA")[0]
            graph_json_str = ""
            s_idx, e_idx = final_output.find('{'), final_output.rfind('}')
            if s_idx != -1 and e_idx != -1: graph_json_str = final_output[s_idx:e_idx+1]

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
                        
                        # Python-Forced Color logic to keep text clean
                        color = "#fd7e14" # Default Orange
                        if shape == "star": color = "#FFD700"
                        elif shape == "octagon": color = "#e63946"
                        elif shape == "ellipse": color = "#2a9d8f"
                        elif shape == "diamond": color = "#9b59b6"

                        # Google Search Fuzzy Linking
                        g_url = urllib.parse.quote(lbl)
                        replacement = f'<a href="https://www.google.com/search?q={g_url}" target="_blank" class="semantic-node-highlight">{lbl}</a>'
                        display_text = re.compile(re.escape(lbl), re.IGNORECASE).sub(replacement, display_text)
                        
                        elements.append({"data": {"id": str(nid), "label": str(lbl), "color": color, "shape": shape, "size": 130 if shape == "star" else 105}})

                    for e in g_json.get("edges", []):
                        if isinstance(e, dict) and e.get("source") and e.get("target"):
                            elements.append({"data": {"source": str(e["source"]), "target": str(e["target"]), "rel_type": str(e.get("rel_type", "AS")).upper()}})
                except: pass

            st.subheader("📊 FINAL TRIAD VERIFIED RESULTS")
            st.markdown(display_text, unsafe_allow_html=True)
            if elements:
                st.subheader("🕸️ FINAL CONNECTIVE HIERARCHOGRAPHY NETWORK")
                render_cytoscape_network(elements, f"viz_{int(time.time())}")

            if biblio:
                with st.expander("📚 BIBLIOGRAPHY"): st.text(biblio)

        except Exception as e:
            st.error(f"❌ Triad Synergy Failure: {e}")

st.divider()
st.caption(f"SIS Pure Cerebras Engine | {VERSION_CODE} | {SYSTEM_DATE}")
