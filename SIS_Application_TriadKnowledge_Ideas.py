import streamlit as st
import json
import base64
import requests
import urllib.parse
import re
import time
from datetime import datetime
from openai import OpenAI
from cerebras.cloud.sdk import Cerebras
import streamlit.components.v1 as components

# =============================================================================
# 0. GLOBAL CONFIGURATION & SESSION DATE (FEBRUARY 24, 2026)
# =============================================================================
SYSTEM_DATE = datetime.now().strftime("%B %d, %Y")
VERSION_CODE = "v22.8.0-ULTRA-SYNERGY-FINAL-950"

# =============================================================================
# INITIALIZATION FIX: Preprečuje AttributeError pri zagonu in resetiranju
# =============================================================================
if 'show_user_guide' not in st.session_state:
    st.session_state.show_user_guide = False

# Zagotovimo, da so vsi ključi prisotni v session_state pred prvo uporabo
if 'groq_synthesis' not in st.session_state:
    st.session_state.groq_synthesis = ""

st.set_page_config(
    page_title=f"SIS Universal Knowledge Synthesizer - {SYSTEM_DATE}",
    page_icon="🌳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- NUCLEAR CSS OVERRIDE: OBLITERATING SIDEBAR ARTIFACTS & FIXING VISIBILITY ---
# Targets the 'keyboard_double_arrow_right' artifact and forced navy-black contrast.
# This section ensures the Knowledge Explorer is perfectly visible.
st.markdown("""
<style>
    /* 1. OBLITERATE ARROW ARTIFACTS & SIDEBAR ICONS */
    /* Hides the specific Streamlit containers where "keyboard_double_arrow_right" appears as text */
    [data-testid="stSidebar"] [data-testid="stIcon"],
    [data-testid="stSidebar"] button[data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebar"] .st-emotion-cache-16idsys,
    [data-testid="stSidebar"] .st-emotion-cache-6qob1r,
    [data-testid="stSidebar"] span[data-testid="stExpanderIcon"],
    [data-testid="stSidebar"] svg[class*="st-emotion-cache"] {
        display: none !important;
        visibility: hidden !important;
        width: 0 !important;
        height: 0 !important;
        opacity: 0 !important;
    }

    /* 2. FORCE SIDEBAR VISIBILITY & HIGH CONTRAST */
    [data-testid="stSidebar"] {
        background-color: #fcfcfc !important;
        border-right: 2px solid #e9ecef !important;
        min-width: 380px !important;
    }

    /* Force all sidebar text to be deep black/navy for perfect visibility */
    [data-testid="stSidebar"] .stMarkdown p, 
    [data-testid="stSidebar"] .stMarkdown li,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stExpander p,
    [data-testid="stSidebar"] .stExpander li,
    [data-testid="stSidebar"] .stMarkdown span,
    [data-testid="stSidebar"] .stMarkdown div {
        color: #ffffff !important; /* Maximum Contrast */
        font-size: 0.98em !important;
        font-weight: 500 !important;
        line-height: 1.6 !important;
        opacity: 1 !important;
    }

    /* 3. RE-STYLE EXPANDERS FOR PROFESSIONAL DENSITY */
    .stExpander {
        background-color: #A9A9A9 !important;
        border: 1px solid #d8e2dc !important;
        border-radius: 12px !important;
        margin-bottom: 12px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05) !important;
    }
    
    .stExpander details summary p {
        color: #1d3557 !important;
        font-weight: 800 !important;
        font-size: 1.05em !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* 4. CONTENT HIGHLIGHTING & NAVIGATION */
    .semantic-node-highlight {
        color: #2a9d8f;
        font-weight: bold;
        border-bottom: 2px solid #2a9d8f;
        padding: 0 2px;
        background-color: #f0fdfa;
        border-radius: 4px;
        transition: all 0.3s ease;
        text-decoration: none !important;
    }
    .semantic-node-highlight:hover {
        background-color: #ccfbf1;
        color: #264653;
        border-bottom: 2px solid #e76f51;
    }
    
    .author-search-link {
        color: #1d3557;
        font-weight: bold;
        text-decoration: none;
        border-bottom: 1px double #457b9d;
        padding: 0 1px;
    }
    .author-search-link:hover {
        color: #e63946;
        background-color: #f1faee;
    }
    
    .google-icon {
        font-size: 0.75em;
        vertical-align: super;
        margin-left: 2px;
        color: #457b9d;
        opacity: 0.8;
    }

    .stMarkdown {
        line-height: 1.9;
        font-size: 1.05em;
    }

    /* 5. ARCHITECTURAL FOCUS BOXES */
    .metamodel-box {
        padding: 25px;
        border-radius: 15px;
        background-color: #f8f9fa;
        border-left: 8px solid #00B0F0;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .mental-approach-box {
        padding: 25px;
        border-radius: 15px;
        background-color: #f0f7ff;
        border-left: 8px solid #6366f1;
        margin-bottom: 30px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    
    .main-header-gradient {
        background: linear-gradient(90deg, #1d3557, #457b9d);
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
        box-shadow: 0 4px 15px rgba(29, 53, 87, 0.3);
        letter-spacing: 1px;
    }

    .sidebar-logo-container {
        display: flex;
        justify-content: center;
        padding: 10px 0;
        margin-bottom: 5px;
    }

    .stButton>button {
        width: 100%;
        border-radius: 10px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.3s ease;
    }
</style>
""", unsafe_allow_html=True)

def get_svg_base64(svg_str):
    """Encodes SVG for reliable display in Streamlit sidebar."""
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
# 1. CORE RENDERING ENGINES & DATA FETCHING
# =============================================================================

def render_cytoscape_network(elements, layout_type="organic", container_id="cy_canvas"):
    """
    ULTRA-SYNERGY Multi-Perspective Hierarchographical Engine.
    
    EXHAUSTIVE RELATIONSHIP TAXONOMY:
    - ISO 25964 Thesaurus: TT, BT, NT, RT (non-dir), EQ (non-dir), AS, IN (Inheritance)
    - UML 2.5 Structural: Composition, Aggregation, Generalization, Specialization, 
                         Realization, Dependency, Containment, Conflict (bi-dir)
    - Logic Operators: AND, OR, XOR, NOT, IF-THEN (chevron flow)
    - Innovation Logic: EX (Epiplexity Fusion), HA (Hierarchical-Associative)
    """
    
    layout_configs = {
        "organic": "{ name: 'cose', idealEdgeLength: 150, nodeOverlap: 100, refresh: 20, fit: true, padding: 50, nodeRepulsion: 1000000, edgeElasticity: 100, nestingFactor: 1.2, numIter: 1500 }",
        "hierarchical": "{ name: 'breadthfirst', directed: true, padding: 50, circle: false, spacingFactor: 1.75, maximal: true }",
        "circular": "{ name: 'circle', padding: 50, radius: 400, spacingFactor: 0.8 }",
        "concentric": "{ name: 'concentric', minNodeSpacing: 80, concentric: function(node){ return node.data('size'); }, levelWidth: function(nodes){ return 10; }, padding: 50 }",
        "grid": "{ name: 'grid', rows: 5, padding: 50, spacingFactor: 1.2 }"
    }

    selected_layout = layout_configs.get(layout_type, layout_configs["organic"])

    cyto_html = f"""
    <div style="position: relative; width: 100%;">
        <button id="save_btn" style="position: absolute; top: 15px; right: 15px; z-index: 1000; padding: 10px 15px; background: #1d3557; color: white; border: none; border-radius: 8px; cursor: pointer; font-family: sans-serif; font-size: 12px; font-weight: 800; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">💾 EXPORT {layout_type.upper()} PNG</button>
        <div id="{container_id}" style="width: 100%; height: 850px; background: #ffffff; border-radius: 20px; border: 1px solid #e0e0e0; box-shadow: 0 10px 40px rgba(0,0,0,0.08);"></div>
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.26.0/cytoscape.min.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            var cy = cytoscape({{
                container: document.getElementById('{container_id}'),
                elements: {json.dumps(elements)},
                style: [
                    {{
                        selector: 'node',
                        style: {{
                            'label': 'data(label)',
                            'text-valign': 'center',
                            'text-halign': 'center',
                            'color': '#1d3557',
                            'background-color': 'data(color)',
                            'width': 'data(size)',
                            'height': 'data(size)',
                            'shape': 'data(shape)',
                            'font-size': '12px',
                            'font-weight': 'bold',
                            'text-wrap': 'wrap',
                            'text-max-width': '80px',
                            'border-width': 3,
                            'border-color': '#ffffff',
                            'text-outline-color': '#ffffff',
                            'text-outline-width': 2
                        }}
                    }},
                    {{
                        selector: 'edge',
                        style: {{
                            'width': 2,
                            'line-color': 'data(color)',
                            'label': 'data(rel_type)',
                            'font-size': '9px',
                            'font-weight': 'bold',
                            'color': '#1d3557',
                            'curve-style': 'unbundled-bezier',
                            'control-point-step-size': 40,
                            'target-arrow-color': 'data(color)',
                            'target-arrow-shape': 'vee',
                            'text-background-opacity': 1,
                            'text-background-color': '#ffffff',
                            'text-background-padding': '3px',
                            'text-background-shape': 'roundrectangle',
                            'edge-distances': 'node-position',
                            'opacity': 0.85
                        }}
                    }},
                    
                    /* --- I. ISO 25964 THESAURUS & INHERITANCE --- */
                    {{ selector: 'edge[rel_type="TT"], edge[rel_type="BT"]', style: {{ 'width': 7, 'line-color': '#1d3557', 'target-arrow-shape': 'triangle', 'target-arrow-scale': 1.6 }} }},
                    {{ selector: 'edge[rel_type="NT"]', style: {{ 'width': 4, 'line-color': '#1d3557', 'target-arrow-shape': 'vee' }} }},
                    {{ selector: 'edge[rel_type="RT"]', style: {{ 'width': 3, 'line-color': '#2a9d8f', 'line-style': 'dotted', 'target-arrow-shape': 'none' }} }},
                    {{ selector: 'edge[rel_type="EQ"]', style: {{ 'width': 6, 'line-color': '#f1c40f', 'line-style': 'double', 'target-arrow-shape': 'none' }} }},
                    {{ selector: 'edge[rel_type="AS"]', style: {{ 'width': 4, 'line-color': '#7b2cb1', 'line-style': 'dashed', 'target-arrow-shape': 'vee' }} }},
                    {{ selector: 'edge[rel_type="IN"]', style: {{ 'width': 5, 'line-color': '#0077b6', 'line-style': 'solid', 'target-arrow-shape': 'triangle', 'target-arrow-fill': 'hollow' }} }},

                    /* --- II. UML 2.5 STRUCTURAL RELATIONS --- */
                    {{ selector: 'edge[rel_type="Composition"]', style: {{ 'width': 6, 'line-color': '#1d3557', 'source-arrow-shape': 'diamond', 'source-arrow-fill': 'filled' }} }},
                    {{ selector: 'edge[rel_type="Aggregation"]', style: {{ 'width': 5, 'line-color': '#1d3557', 'source-arrow-shape': 'diamond', 'source-arrow-fill': 'hollow' }} }},
                    {{ selector: 'edge[rel_type="Generalization"]', style: {{ 'width': 5, 'line-color': '#1d3557', 'target-arrow-shape': 'triangle', 'target-arrow-fill': 'hollow' }} }},
                    {{ selector: 'edge[rel_type="Specialization"]', style: {{ 'width': 4, 'line-color': '#000000', 'line-style': 'dashed', 'target-arrow-shape': 'triangle', 'target-arrow-fill': 'filled' }} }},
                    {{ selector: 'edge[rel_type="Realization"]', style: {{ 'width': 3, 'line-color': '#1d3557', 'line-style': 'dashed', 'target-arrow-shape': 'triangle', 'target-arrow-fill': 'hollow' }} }},
                    {{ selector: 'edge[rel_type="Dependency"]', style: {{ 'width': 3, 'line-color': '#457b9d', 'line-style': 'dashed', 'target-arrow-shape': 'vee' }} }},
                    {{ selector: 'edge[rel_type="Containment"]', style: {{ 'width': 6, 'line-color': '#1d3557', 'target-arrow-shape': 'circle', 'target-arrow-fill': 'hollow' }} }},
                    {{ selector: 'edge[rel_type="Conflict"]', style: {{ 'width': 8, 'line-color': '#b91d1d', 'line-style': 'solid', 'target-arrow-shape': 'triangle-cross', 'source-arrow-shape': 'triangle-cross' }} }},

                    /* --- III. LOGIC OPERATORS & INNOVATION --- */
                    {{ selector: 'edge[rel_type="AND"]', style: {{ 'width': 6, 'line-color': '#00FF00', 'target-arrow-shape': 'chevron', 'line-style': 'dashed' }} }},
                    {{ selector: 'edge[rel_type="OR"]', style: {{ 'width': 4, 'line-color': '#00BFFF', 'target-arrow-shape': 'chevron', 'line-style': 'dashed' }} }},
                    {{ selector: 'edge[rel_type="XOR"]', style: {{ 'width': 5, 'line-color': '#FF8C00', 'line-style': 'double', 'target-arrow-shape': 'diamond' }} }},
                    {{ selector: 'edge[rel_type="NOT"]', style: {{ 'width': 5, 'line-color': '#FF0000', 'line-style': 'dashed', 'target-arrow-shape': 'tee' }} }},
                    {{ selector: 'edge[rel_type="IF-THEN"]', style: {{ 'width': 5, 'line-color': '#FFD700', 'target-arrow-shape': 'triangle', 'arrow-scale': 1.6 }} }},
                    {{ selector: 'edge[rel_type="EX"]', style: {{ 'width': 9, 'line-color': '#ff00ff', 'line-style': 'dashed', 'target-arrow-shape': 'star', 'arrow-scale': 2.0 }} }},
                    {{ selector: 'edge[rel_type="HA"]', style: {{ 'width': 6, 'line-color': '#7b2cb1', 'line-style': 'dashed', 'target-arrow-shape': 'triangle-tee', 'source-arrow-shape': 'circle', 'source-arrow-fill': 'hollow' }} }},

                    /* --- IV. GEOMETRIC TAXONOMY (Shapes & Sizes) --- */
                    {{ selector: 'node[shape="star"]', style: {{ 'width': 150, 'height': 150, 'border-width': 6, 'border-color': '#FFD700', 'font-size': '14px' }} }},
                    {{ selector: 'node[shape="hexagon"]', style: {{ 'width': 120, 'height': 120, 'border-width': 4, 'border-color': '#1d3557' }} }},
                    {{ selector: 'node[shape="diamond"]', style: {{ 'width': 125, 'height': 125, 'border-width': 5, 'border-color': '#fd7e14' }} }},
                    {{ selector: 'node[shape="octagon"]', style: {{ 'width': 110, 'height': 110, 'border-width': 4, 'border-color': '#dc3545' }} }},
                    {{ selector: 'node[shape="triangle"]', style: {{ 'width': 100, 'height': 100, 'border-width': 3, 'border-color': '#28a745' }} }},
                    {{ selector: 'node[shape="ellipse"]', style: {{ 'width': 105, 'height': 105, 'border-width': 3, 'border-color': '#17a2b8' }} }},
                    {{ selector: 'node[shape="rectangle"]', style: {{ 'width': 95, 'height': 95, 'border-width': 2, 'border-color': '#6c757d' }} }}
                ],
                layout: {selected_layout}
            }});

            document.getElementById('save_btn').addEventListener('click', function() {{
                var png64 = cy.png({{full: true, bg: 'white', scale: 3}});
                var link = document.createElement('a');
                var timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
                link.href = png64; 
                link.download = 'sis_universal_graph_' + timestamp + '.png';
                link.click();
            }});
        }});
    </script>
    """
    components.html(cyto_html, height=900)


def fetch_author_bibliographies(author_input):
    """Retrieves bibliography via ORCID API search and record lookup."""
    if not author_input: return ""
    author_list = [a.strip() for a in author_input.split(",")]
    comprehensive_biblio = ""
    headers = {"Accept": "application/json"}
    for auth in author_list:
        try:
            s_res = requests.get(f"https://pub.orcid.org/v3.0/search/?q={auth}", headers=headers, timeout=8).json()
            if s_res.get('result'):
                orcid_id = s_res['result'][0]['orcid-identifier']['path']
                r_res = requests.get(f"https://pub.orcid.org/v3.0/{orcid_id}/record", headers=headers, timeout=8).json()
                works = r_res.get('activities-summary', {}).get('works', {}).get('group', [])
                comprehensive_biblio += f"#### 🆔 ORCID: {auth.upper()} ({orcid_id})\\n"
                for work in works[:12]:
                    summary = work.get('work-summary', [{}])[0]
                    title = summary.get('title', {}).get('title', {}).get('value', 'Unknown Title')
                    pub_date = summary.get('publication-date')
                    year = pub_date.get('year', {}).get('value', 'n.d.') if pub_date else 'n.d.'
                    comprehensive_biblio += f"- **{year}**: {title}\\n"
                comprehensive_biblio += "\\n---\\n"
        except Exception:
            pass
    return comprehensive_biblio

def fetch_author_bibliographies(author_input):
    """Retrieves bibliography via ORCID API search and record lookup."""
    if not author_input: return ""
    author_list = [a.strip() for a in author_input.split(",")]
    comprehensive_biblio = ""
    headers = {"Accept": "application/json"}
    for auth in author_list:
        try:
            s_res = requests.get(f"https://pub.orcid.org/v3.0/search/?q={auth}", headers=headers, timeout=8).json()
            if s_res.get('result'):
                orcid_id = s_res['result'][0]['orcid-identifier']['path']
                r_res = requests.get(f"https://pub.orcid.org/v3.0/{orcid_id}/record", headers=headers, timeout=8).json()
                works = r_res.get('activities-summary', {}).get('works', {}).get('group', [])
                comprehensive_biblio += f"#### 🆔 ORCID: {auth.upper()} ({orcid_id})\\n"
                for work in works[:12]:
                    summary = work.get('work-summary', [{}])[0]
                    title = summary.get('title', {}).get('title', {}).get('value', 'Unknown Title')
                    pub_date = summary.get('publication-date')
                    year = pub_date.get('year', {}).get('value', 'n.d.') if pub_date else 'n.d.'
                    comprehensive_biblio += f"- **{year}**: {title}\\n"
                comprehensive_biblio += "\\n---\\n"
        except Exception:
            pass
    return comprehensive_biblio

# =============================================================================
# 2. ARCHITECTURAL ONTOLOGIES (IMA & MA) - EXHAUSTIVE EXPANSION
# =============================================================================

HUMAN_THINKING_METAMODEL = {
    "nodes": {
        "Human mental concentration": {
            "color": "#ADB5BD", "shape": "rectangle", 
            "desc": "The foundational state of cognitive focus required for interdisciplinary synthesis and logical rigor."
        },
        "Identity": {
            "color": "#C6EFCE", "shape": "rectangle", 
            "desc": "The subjective core of the researcher or agent, containing professional ethical parameters and specialized lenses."
        },
        "Autobiographical memory": {
            "color": "#C6EFCE", "shape": "rectangle", 
            "desc": "The historical database of past cycles influencing current logic."
        },
        "Mission": {
            "color": "#92D050", "shape": "rectangle", 
            "desc": "The high-level existential imperative driving the direction of inquiry and synthesis."
        },
        "Vision": {
            "color": "#FFFF00", "shape": "rectangle", 
            "desc": "Mental simulation of a desired future outcome acting as a magnetic pull for goal-setting."
        },
        "Goal": {
            "color": "#00B0F0", "shape": "rectangle", 
            "desc": "Quantifiable milestones materialize the mission within reality."
        },
        "Problem": {
            "color": "#F2DCDB", "shape": "rectangle", 
            "desc": "Obstruction preventing goal realization; gap between current and target state."
        },
        "Ethics/moral": {
            "color": "#FFC000", "shape": "rectangle", 
            "desc": "Value system filtering solution validity."
        },
        "Hierarchy of interests": {
            "color": "#F8CBAD", "shape": "rectangle", 
            "desc": "Ordering of needs dictating resource allocation."
        },
        "Rule": {
            "color": "#F2F2F2", "shape": "rectangle", 
            "desc": "Structural, logical, and legal constraints governing node interactions."
        },
        "Decision-making": {
            "color": "#FFFF99", "shape": "rectangle", 
            "desc": "Choosing efficient selection pathways toward goal achievement."
        },
        "Problem solving": {
            "color": "#D9D9D9", "shape": "rectangle", 
            "desc": "Algorithmic process removing obstructions."
        },
        "Conflict situation": {
            "color": "#00FF00", "shape": "rectangle", 
            "desc": "State where multiple goals or rules clash."
        },
        "Knowledge": {
            "color": "#DDEBF7", "shape": "rectangle", 
            "desc": "Internalized facts and theoretical models."
        },
        "Tool": {
            "color": "#00B050", "shape": "rectangle", 
            "desc": "External instruments leveraged to interact with the domain."
        },
        "Experience": {
            "color": "#00B050", "shape": "rectangle", 
            "desc": " Wisdom gained through direct application of knowledge."
        },
        "Classification": {
            "color": "#CCC0DA", "shape": "rectangle", 
            "desc": "Taxonomic act reducing cognitive load."
        },
        "Psychological aspect": {
            "color": "#F8CBAD", "shape": "rectangle", 
            "desc": "Internal outcomes on individual mental states."
        },
        "Sociological aspect": {
            "color": "#00FFFF", "shape": "rectangle", 
            "desc": "External collective impact and social changes."
        }
    },
    "relations": [
        ("Human mental concentration", "Identity", "has"), ("Identity", "Autobiographical memory", "possesses"),
        ("Mission", "Vision", "defines"), ("Vision", "Goal", "leads to"), ("Problem", "Identity", "challenges"),
        ("Rule", "Decision-making", "constrains"), ("Knowledge", "Classification", "organizes"),
        ("Experience", "Psychological aspect", "forms"), ("Conflict situation", "Sociological aspect", "triggers")
    ]
}

MENTAL_APPROACHES_ONTOLOGY = {
    "nodes": {
        "Perspective shifting": {
            "color": "#00FF00", "shape": "diamond", 
            "desc": "Rotating problem space through disparate stakeholders."
        },
        "Similarity and difference": {
            "color": "#FFFF00", "shape": "diamond", 
            "desc": "Pattern recognition act identifying anomalies."
        },
        "Core": {
            "color": "#FFC000", "shape": "diamond", 
            "desc": "Distillation of a problem into fundamental essence."
        },
        "Attraction": {
            "color": "#F2A6A2", "shape": "diamond", 
            "desc": "Force drawing disparate concepts into synthesis."
        },
        "Repulsion": {
            "color": "#D9D9D9", "shape": "diamond", 
            "desc": "Isolation of incompatible solutions or noise."
        },
        "Condensation": {
            "color": "#CCC0DA", "shape": "diamond", 
            "desc": "Reduction of vast complexity into strategic insight."
        },
        "Framework and foundation": {
            "color": "#F8CBAD", "shape": "diamond", 
            "desc": "Establishing boundaries for innovation logic."
        },
        "Bipolarity and dialectics": {
            "color": "#DDEBF7", "shape": "diamond", 
            "desc": "Synthesis through opposing tension tension."
        },
        "Constant": {
            "color": "#E1C1D1", "shape": "diamond", 
            "desc": "Identifying stable system invariants."
        },
        "Associativity": {
            "color": "#E1C1D1", "shape": "diamond", 
            "desc": "Non-linear, lateral knowledge linking."
        },
        "Induction": {
            "color": "#B4C6E7", "shape": "diamond", 
            "desc": "Building broad theory from field observations."
        },
        "Whole and part": {
            "color": "#00FF00", "shape": "diamond", 
            "desc": "Holistic vs Granular logic navigation."
        },
        "Mini-max": {
            "color": "#00FF00", "shape": "diamond", 
            "desc": "Maximum utility with minimum friction search."
        },
        "Addition and composition": {
            "color": "#FF00FF", "shape": "diamond", 
            "desc": "Building complexity through layering building blocks."
        },
        "Hierarchy": {
            "color": "#C6EFCE", "shape": "diamond", 
            "desc": "Vertical taxonomic ranking by systemic priority."
        },
        "Balance": {
            "color": "#00B0F0", "shape": "diamond", 
            "desc": "Search for dynamic equilibrium between variables."
        },
        "Deduction": {
            "color": "#92D050", "shape": "diamond", 
            "desc": "Applying broad laws to solve specifics."
        },
        "Abstraction and elimination": {
            "color": "#00B0F0", "shape": "diamond", 
            "desc": "Removing noise to reach a generic model."
        },
        "Pleasure and displeasure": {
            "color": "#00FF00", "shape": "diamond", 
            "desc": "Evaluative feedback on solution elegance."
        },
        "Openness and closedness": {
            "color": "#FFC000", "shape": "diamond", 
            "desc": "Systemic boundary state governing external data nodes."
        }
    }
}
# =============================================================================
# 2.1 HIERARCHOLOGY & HIERARCHOGRAPHY ONTOLOGY
# =============================================================================

HIERARCHOLOGY_ONTOLOGY = {
    "core_definitions": {
        "Hierarchology": "Interdisciplinary science studying hierarchical associative systems (Micro, Meso, Macro).",
        "Hierarchography": "Descriptive outlining of systems using workflows, tree maps, and structural diagrams.",
        "Scientific Cage": "Cognitive limitations preventing thought beyond established paradigms."
    },
    "hierarchical_levels": {
        "Micro-hierarchology": "Internal individual thinking and neural inductive communication.",
        "Meso-hierarchology": "Intermediate social groups and organizational associative structures.",
        "Macro-hierarchology": "Fundamental social laws and universal natural hierarchies."
    },
    "operational_logic": {
        "Internal Processes": "Inductive (building from specific neural/local signals to patterns).",
        "External Functioning": "Deductive & Dialectical (applying general laws to specific social behaviors)."
    },
    "hierarchography_tools": [
        "Workflow Mapping", "Tree Maps", "Oligographs", "UML Modeling", "Mind Mapping", "Cognitive Modeling"
    ]
}

# Add Hierarchology-specific nodes to your existing Metamodel
HUMAN_THINKING_METAMODEL["nodes"].update({
    "Hierarchical Associative System": {"color": "#fd7e14", "shape": "ellipse", "desc": "The primary cognitive framework defined by hierarchology."},
    "Scientific Cage": {"color": "#6c757d", "shape": "rectangle", "desc": "The boundary of human mental perspective."},
    "Hierarchography": {"color": "#e63946", "shape": "diamond", "desc": "The visual description of hierarchical structures."}
})
# =============================================================================
# 3. KNOWLEDGE BASE (EXHAUSTIVE 18D SCIENCE FIELDS & ONTOLOGIES)
# =============================================================================

KNOWLEDGE_BASE = {
    "User profiles": {
        "Adventurers": {"description": "Explorers of hidden interdisciplinary patterns and high-risk hypotheses."},
        "Applicators": {"description": "Focused on practical efficiency, rapid deployment, and tangible execution."},
        "Know-it-alls": {"description": "Seekers of systemic absolute clarity, comprehensive taxonomy, and complete data."},
        "Observers": {"description": "Passive monitors of systemic dynamics and trend watchers without intervention."}
    },
    "Scientific paradigms": {
        "Empiricism": "Focus on sensory experience, experimental evidence, and observation-driven data.",
        "Rationalism": "Reliance on deductive logic, a priori reasoning, and mathematical certainty.",
        "Constructivism": "Knowledge as a social and cognitive build, dependent on perception.",
        "Positivism": "Strict adherence to verifiable facts and rejection of speculation.",
        "Pragmatism": "Evaluation based on utility and real-world application.",
        "Reductionism": "Explaining complex phenomena by breaking them down into simpler, fundamental parts.",
        "Holism": "Systems should be viewed as wholes, not just as a collection of parts.",
        "Systems Theory": "Interdisciplinary study of systems where the focus is on relationships and patterns.",
        "Phenomenology": "Study of structures of consciousness as experienced from the first-person point of view.",
        "Falsificationism": "Popper’s principle that scientific theories must be inherently testable and refutable.",
        "Critical Theory": "Social theory oriented toward critiquing and changing society as a whole.",
        "Hermeneutics": "Theory and methodology of interpretation, especially of texts and human actions.",
        "Relativism": "The view that truth and falsity, right and wrong, are products of social and historical contexts.",
        "Structuralism": "Elements of human culture must be understood in terms of their relationship to a broader system.",
        "Post-Structuralism": "Critique of structuralism, emphasizing the instability of meaning and systems."
    },
    "Structural models": {
        "Causal Connections": "Chains of cause and effect mapping systemic causality.",
        "Principles & Relations": "Fundamental laws and the inter-relations between entities.",
        "Episodes & Sequences": "Temporal flow, historical timelines, and event ordering.",
        "Facts & Characteristics": "Raw data properties, attributes, and static descriptions.",
        "Generalizations": "Broad frameworks and high-level theoretical models.",
        "Glossary": "Precise definitions and terminological clarity.",
        "Concepts": "Abstract constructs and conceptual building blocks."
    },
    "Science fields": {
        "Mathematics": {
            "cat": "Formal", 
            "methods": ["Axiomatization", "Formal Proof", "Stochastic Modeling", "Topology"], 
            "tools": ["MATLAB", "LaTeX", "WolframAlpha"], 
            "facets": ["Algebra", "Analysis", "Number Theory", "Calculus"]
        },
        "Physics": {
            "cat": "Natural", 
            "methods": ["Quantum Modeling", "Particle Tracking", "Interferometry", "Simulation"], 
            "tools": ["Accelerator", "Spectrometer", "Oscilloscopes", "Cryostats"], 
            "facets": ["Relativity", "Quantum Mechanics", "Thermodynamics", "Optics"]
        },
        "Chemistry": {
            "cat": "Natural", 
            "methods": ["Organic Synthesis", "Chromatography", "NMR Spectroscopy", "Titration"], 
            "tools": ["NMR", "Mass Spec", "Incubators", "Burettes"], 
            "facets": ["Biochemistry", "Physical Chemistry", "Analytical", "Inorganic"]
        },
        "Biology": {
            "cat": "Natural", 
            "methods": ["Gene Sequencing", "CRISPR", "Cell Culture", "In-vivo observation"], 
            "tools": ["Electron Microscope", "PCR Machine", "Centrifuge", "Incubators"], 
            "facets": ["Genetics", "Microbiology", "Ecology", "Cell Biology"]
        },
        "Neuroscience": {
            "cat": "Natural", 
            "methods": ["Neuroimaging", "Optogenetics", "Behavioral Mapping", "Electrophysiology"], 
            "tools": ["fMRI", "EEG", "Electrodes", "Patch Clamp"], 
            "facets": ["Cognitive Neuroscience", "Neural Plasticity", "Synaptic Physiology"]
        },
        "Psychology": {
            "cat": "Social", 
            "methods": ["Double-Blind Trials", "Psychometrics", "Longitudinal Studies", "CBT"], 
            "tools": ["Standardized Tests", "Surveys", "Biofeedback", "Eye-tracking"], 
            "facets": ["Behavioral", "Clinical", "Developmental", "Cognitive Psychology"]
        },
        "Sociology": {
            "cat": "Social", 
            "methods": ["Ethnography", "Network Analysis", "Survey Design", "Grounded Theory"], 
            "tools": ["NVivo", "SPSS", "Census Data", "Social Graphs"], 
            "facets": ["Demography", "Stratification", "Dynamics", "Urban Sociology"]
        },
        "Political Science": {
            "cat": "Social",
            "methods": ["Comparative Method", "Institutional Analysis", "Quantitative Modeling", "Political Theory Analysis"],
            "tools": ["STATA", "Polling Data", "Legislative Archives"],
            "facets": ["International Relations", "Comparative Politics", "Political Theory", "Public Policy", "Geopolitics"]
        },
        "Anthropology": {
            "cat": "Social/Humanities",
            "methods": ["Participant Observation", "Ethnography", "Cross-Cultural Comparison", "Archaeological Excavation"],
            "tools": ["Field Journals", "GIS", "Radiocarbon Dating"],
            "facets": ["Cultural Anthropology", "Biological Anthropology", "Archaeology", "Linguistic Anthropology"]
        },
        "Cognitive Science": {
            "cat": "Interdisciplinary",
            "methods": ["Computational Modeling", "Experimental Paradigm Design", "Turing Analysis"],
            "tools": ["AI Architectures", "Eye-tracking", "Reaction-time Latency"],
            "facets": ["Artificial Intelligence", "Philosophy of Mind", "Cognitive Psychology", "Linguistics"]
        },
        "Complexity Science": {
            "cat": "Formal/Interdisciplinary",
            "methods": ["Agent-Based Modeling", "Network Topology", "Chaos Theory", "Fractal Analysis"],
            "tools": ["NetLogo", "Graph Theory Software", "Non-linear Simulators"],
            "facets": ["Self-Organization", "Emergence", "System Dynamics", "Complex Adaptive Systems"]
        },
        "Computer Science": {
            "cat": "Formal", 
            "methods": ["Algorithm Design", "Verification", "Complexity Analysis", "Parallelism"], 
            "tools": ["GPU Clusters", "Docker", "Compilers", "IDEs", "Kubernetes"], 
            "facets": ["AI", "Cybersecurity", "Blockchain", "Cloud Computing"]
        },
        "Medicine": {
            "cat": "Applied", 
            "methods": ["Clinical Trials", "Epidemiology", "Radiology", "Pathology"], 
            "tools": ["MRI", "CT Scanner", "Biomarker Assays", "Ultrasound"], 
            "facets": ["Genomics", "Immunology", "Oncology", "Internal Medicine"]
        },
        "Psychiatry": {
            "cat": "Applied/Medical", 
            "methods": ["Clinical Trials", "Diagnostic Interviewing", "Case Formulation", "Psychopharmacological Modeling", "Neuroimaging Analysis"], 
            "tools": ["DSM-5-TR", "ICD-11", "EEG", "fMRI", "Standardized Rating Scales"], 
            "facets": ["Clinical Psychiatry", "Neuropsychiatry", "Forensic Psychiatry", "Geriatric Psychiatry"]
        },
        "Public Health": {
            "cat": "Applied/Social",
            "methods": ["Biostatistics", "Community Health Assessment", "Policy Advocacy", "Epidemiological Surveillance"],
            "tools": ["Vital Statistics", "Health Registries", "GIS"],
            "facets": ["Epidemiology", "Environmental Health", "Global Health", "Health Policy"]
        },
        "Engineering": {
            "cat": "Applied", 
            "methods": ["FEA Analysis", "Prototyping", "Stress Testing", "Systems Integration"], 
            "tools": ["CAD", "3D Printers", "CNC Machines", "Simulation SW"], 
            "facets": ["Robotics", "Nanotechnology", "Civil Eng", "Electrical Eng"]
        },
        "Materials Science": {
            "cat": "Applied/Natural",
            "methods": ["Crystallography", "Metallography", "Polymer Characterization", "Nano-fabrication"],
            "tools": ["SEM (Scanning Electron Microscope)", "X-ray Diffraction", "Spectroscopy"],
            "facets": ["Nanomaterials", "Biomaterials", "Metallurgy", "Semiconductors"]
        },
        "Economics": {
            "cat": "Social", 
            "methods": ["Econometrics", "Game Theory", "Macro Equilibrium Modeling", "Forecasting"], 
            "tools": ["Bloomberg", "Stata", "R", "Python Pandas"], 
            "facets": ["Finance", "Behavioral Econ", "Macroeconomics", "Microeconomics"]
        },
        "Philosophy": {
            "cat": "Humanities", 
            "methods": ["Socratic Method", "Dialectics", "Phenomenology", "Conceptual Analysis"], 
            "tools": ["Logic Mapping", "Primary Texts", "Semantic Analysis"], 
            "facets": ["Epistemology", "Ethics", "Metaphysics", "Aesthetics"]
        },
        "Linguistics": {
            "cat": "Humanities", 
            "methods": ["Corpus Analysis", "Syntactic Parsing", "Historical Phonetics", "Transcription"], 
            "tools": ["Praat", "NLTK", "WordNet", "ELAN"], 
            "facets": ["Semantics", "Phonology", "Sociolinguistics", "CompLing"]
        },
        "Ecology": {
            "cat": "Natural", 
            "methods": ["Remote Sensing", "Trophic Modeling", "Field Sampling", "Biogeochemistry"], 
            "tools": ["GIS", "Biosensors", "Drones", "Satellite Imagery"], 
            "facets": ["Biodiversity", "Conservation Biology", "Restoration Ecology"]
        },
        "History": {
            "cat": "Humanities", 
            "methods": ["Archival Research", "Historiography", "Oral History", "Prosopography"], 
            "tools": ["Radiocarbon Dating", "Microfilm", "Digital Archives"], 
            "facets": ["Military History", "Diplomacy", "Ancient Civilizations", "Social History"]
        },
        "Architecture": {
            "cat": "Applied", 
            "methods": ["Parametric Design", "Environmental Analysis", "BIM", "Urbanism"], 
            "tools": ["Revit", "Rhino 3D", "AutoCAD", "Photogrammetry"], 
            "facets": ["Urban Design", "Sustainability", "Landscape Arch", "Heritage"]
        },
        "Geology": {
            "cat": "Natural", 
            "methods": ["Stratigraphy", "Mineralogy", "Seismology", "Petrology"], 
            "tools": ["Seismograph", "GIS", "Magnetometers", "Thin-sectioning"], 
            "facets": ["Tectonics", "Petrology", "Paleontology", "Geophysics"]
        },
        "Geography": {
            "cat": "Natural/Social", 
            "methods": ["Spatial Analysis", "Geospatial Modeling", "Remote Sensing", "Field Observation", "Regional Synthesis"], 
            "tools": ["ArcGIS/QGIS", "GPS Systems", "Satellite Imagery", "Lidar Scan"], 
            "facets": ["Physical Geography", "Human Geography", "Geomorphology", "Urban Geography"]
        },
        "Climatology": {
            "cat": "Natural", 
            "methods": ["Climate Modeling", "Paleoclimatic Reconstruction", "Statistical Time-Series Analysis"], 
            "tools": ["Supercomputers (HPC)", "Weather Station Arrays", "Satellite Radiometers"], 
            "facets": ["Meteorology", "Paleoclimatology", "Dynamic Climatology", "Applied Climatology"]
        },
        "Library Science": {
            "cat": "Applied", 
            "methods": ["Taxonomy", "Archival Appraisal", "Retrieval Logic", "Metadata"], 
            "tools": ["OPAC", "Metadata Systems", "Thesauri", "Digital Archives"], 
            "facets": ["Knowledge Organization", "Information Retrieval", "Digital Curation"]
        },
        "Criminology": {
            "cat": "Social", 
            "methods": ["Profiling", "Longitudinal Studies", "Victimology Analysis", "Ethnography"], 
            "tools": ["Crime Mapping", "AFIS", "CODIS", "SPSS"], 
            "facets": ["Penology", "Forensic Psychology", "Police Science", "Criminal Justice"]
        },
        "Forensic sciences": {
            "cat": "Applied/Natural", 
            "methods": ["DNA Profiling", "Ballistics", "Toxicology", "Trace Analysis"], 
            "tools": ["Mass Spectrometer", "Luminol", "Comparison Microscope", "AFIS"], 
            "facets": ["Forensic Biology", "Forensic Chemistry", "Forensic Pathology", "Digital Forensics"]
        },
        "Legal science": {
            "cat": "Social", 
            "methods": ["Legal Hermeneutics", "Comparative Law", "Dogmatic Method", "Empirical Legal Research"], 
            "tools": ["Legislative Databases", "Case Law Archives", "Constitutional Records", "Westlaw"], 
            "facets": ["Jurisprudence", "Constitutional Law", "Criminal Law", "Civil Law", "International Law"]
        }
    }
}
# =============================================================================
# 3.1 ADVANCED IDEATION TECHNIQUES LIBRARY
# =============================================================================
IDEATION_TECHNIQUES = {
    "Six Thinking Hats": "Process the problem through 6 perspectives: White (Data), Red (Emotion), Black (Risk), Yellow (Value), Green (Creativity), and Blue (Control/Planning).",
    "SCAMPER": "Apply the following filters: Substitute, Combine, Adapt, Modify, Put to another use, Eliminate, and Reverse.",
    "First Principles": "Deconstruct the problem into fundamental, undeniable truths and rebuild a solution from the ground up (avoiding analogies).",
    "TRIZ (Simplified)": "Identify systemic contradictions and apply inventive principles like Segmentation, Nesting, or Local Quality to resolve them.",
    "Lateral Thinking": "Use 'Provocation' and 'Movement' to jump out of established patterns and find non-obvious entry points to the problem.",
    "Blue Ocean Strategy": "Identify ways to make the competition irrelevant by creating a new value space through 'Eliminate-Reduce-Raise-Create' logic.",
    "Synectics": "Use direct, personal, and symbolic analogies to make the strange familiar and the familiar strange."
}
# =============================================================================
# 3.2 EPIPLEXITY KNOWLEDGE FRAMEWORK
# =============================================================================
EPIPLEXITY_FRAMEWORK = {
    "definition": "The measure of interdisciplinary structural density. It quantifies the 'depth' of fusion between disparate scientific fields to break through 'Scientific Cages'.",
    "logic_levels": {
        "Linear (Low)": "Multidisciplinary: Fields exist side-by-side with minimal interaction (simple borrowing).",
        "Integrated (Medium)": "Interdisciplinary: Fields share methods and terminology, creating a bridge.",
        "Synergetic (High)": "Transdisciplinary: Fields merge to create a new, hybrid 'Scientific Cage' with emergent properties and radical innovation."
    },
    "epiplexic_connectors": [
        "Semantic Overlap", "Methodological Transfer", "Hierarchical Fusion", "Paradigm Collision"
    ]
}
# =============================================================================
# 4. KONČNI POPRAVLJEN SIDEBAR (METODOLOŠKO USKLAJEN)
# =============================================================================
with st.sidebar:
    # 1. Original 3D Relief Logo
    st.markdown(f'<div class="sidebar-logo-container"><img src="data:image/svg+xml;base64,{get_svg_base64(SVG_3D_RELIEF)}" width="220"></div>', unsafe_allow_html=True)
    
    # 2. Date Badge
    st.markdown(f'<div class="date-badge">{SYSTEM_DATE.upper()}</div>', unsafe_allow_html=True)
    
    st.header("⚙️ SYSTEM CONTROL")
    
    # 3. CEREBRAS SYSTEM CONTROL
    cerebras_api_key = st.text_input("Cerebras API Key:", type="password", key="side_cerebras_v2026_final")
    
    st.subheader("🤖 Model Selection")
    p1_model = st.selectbox("Phase 1 (Structure):", ["gpt-oss-120b", "gemma-4-31b"], index=0, key="p1_select")
    p2_model = st.selectbox("Phase 2 (Innovation):", ["gemma-4-31b", "gpt-oss-120b"], index=0, key="p2_select")
    
    st.divider()

    # 4. GRAPH PERSPECTIVE
    st.subheader("🎨 GRAPH PERSPECTIVE")
    graph_perspective = st.selectbox(
        "Select Visual Layout Engine:",
        options=["organic", "hierarchical", "circular", "concentric", "grid"],
        index=0,
        format_func=lambda x: x.capitalize() + " View",
        key="side_graph_layout_v2026_final"
    )
    
    st.divider()
    
    # 5. CONTROL BUTTONS
    col_res, col_gui = st.columns(2)
    with col_res:
        if st.button("♻️ RESET", key="sidebar_reset_final"):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()
    with col_gui:
        if st.button("📖 GUIDE", key="sidebar_guide_final"):
            st.session_state.show_user_guide = not st.session_state.show_user_guide
            st.rerun()
            
    st.divider()

    # 6. KNOWLEDGE EXPLORER (USKLAJEN Z 6 STEBRI)
    st.subheader("📚 KNOWLEDGE EXPLORER")

    with st.expander("📐 Semantic Pillars (ISO & UML)", expanded=False):
        st.markdown("""
        **1. TT (Top Term)**: The absolute root or primary category of a domain (Thick Navy line).
        
        **2. BT (Broader Term)**: A more general concept/category; moves up the hierarchy (Navy line).
        
        **3. NT (Narrower Term)**: A more specific concept/subcategory; moves down the hierarchy (Vee arrow).
        
        **4. RT (Related Term)**: Symmetrical association without hierarchy; horizontal context (Dotted Teal, no arrow).
        
        **5. EQ (Equivalence)**: Identity relationship, synonyms, or "the same as" (Double Gold line, no arrow).
        
        **6. AS (Associative)**: Lateral semantic jumps or non-linear neural connections (Dashed Purple).
        
        **7. IN (Inheritance)**: Object-oriented class hierarchy; A inherits properties from B (Blue line, hollow triangle).
        """)

    with st.expander("🏛️ Metamodel (IMA) Structures", expanded=False):
        for n, d in HUMAN_THINKING_METAMODEL["nodes"].items(): 
            st.markdown(f"• **{n}**: {d['desc']}")

    with st.expander("🧠 Mental Approach (MA) Map", expanded=False):
        for m, d in MENTAL_APPROACHES_ONTOLOGY["nodes"].items(): 
            st.markdown(f"• **{m}**: {d['desc']}")

    with st.expander("🔬 Science Taxonomy", expanded=False):
        st.markdown("**Levels:**")
        for level, desc in HIERARCHOLOGY_ONTOLOGY["hierarchical_levels"].items():
            st.markdown(f"• **{level}**: {desc}")

    st.divider()
    st.subheader("🌐 CONNECTORS")
    st.link_button("🆔 ORCID Registry", "https://orcid.org/", use_container_width=True)
    st.link_button("🎓 Google Scholar", "https://scholar.google.com/", use_container_width=True)

# --- MAIN PAGE CONTENT ---
st.markdown('<h1 class="main-header-gradient">🧱 SIS Universal Knowledge Synthesizer</h1>', unsafe_allow_html=True)
st.markdown(f"**Sequential Multi-Engine Pipeline** | Version: **{VERSION_CODE}**")

if st.session_state.get('show_user_guide'):
    st.info("""
    **Synergy Workflow:**
    1. Enter **Cerebras Key**.
    2. Define **Foundation (Step 1)**: Factual IMA structure.
    3. Define **Innovation (Step 2)**: Generative MA ideas.
    4. **Execute**: Map breakthroughs against scientific cages.
    """)

# ARCHITECTURE BOXES
col_ref1, col_ref2 = st.columns(2)
with col_ref1:
    st.markdown('<div class="metamodel-box"><b>🏛️ Phase 1: Structure</b><br>Fact-based IMA Reasoning foundation.</div>', unsafe_allow_html=True)
with col_ref2:
    st.markdown('<div class="mental-approach-box"><b>🧠 Phase 2: Innovation</b><br>Generative MA Breakthroughs.</div>', unsafe_allow_html=True)

st.markdown("### 🛠️ PIPELINE CONFIGURATION")

# Entry Rows
r1c1, r1c2, r1c3 = st.columns([1.5, 2, 1])
with r1c1:
    target_authors = st.text_input("👤 Target Authors (ORCID):", placeholder="e.g., Karl Petrič", key="auth_in_v2026")
with r1c2:
    sel_sciences = st.multiselect("2. Science Fields:", sorted(list(KNOWLEDGE_BASE["Science fields"].keys())), default=["Physics", "Psychology", "Sociology"], key="sci_in_v2026")
with r1c3:
    expertise = st.select_slider("3. Expertise Level:", ["Novice", "Intermediate", "Expert"], value="Expert", key="exp_in_v2026")

# --- VRSTICA 2: PARADIGME, MODELI IN STRATEŠKI CILJ ---
r2c1, r2c2, r2c3 = st.columns([1, 1, 1])
with r2c1:
    sel_paradigms = st.multiselect(
        "4. Scientific Paradigms:", 
        options=list(KNOWLEDGE_BASE["Scientific paradigms"].keys()), 
        default=["Systems Theory", "Holism"],
        key="paradigms_in_v2026"
    )
with r2c2:
    sel_models = st.multiselect(
        "5. Structural Models:", 
        options=list(KNOWLEDGE_BASE["Structural models"].keys()), 
        default=["Concepts", "Principles & Relations"],
        key="models_in_v2026"
    )
with r2c3:
    goal_context = st.selectbox(
        "6. Strategic Project Goal:", 
        ["Scientific Research", "Problem Solving", "Educational", "Policy Making"], 
        key="goal_ctx_v2026"
    )

st.divider()

# =============================================================================
# 🧬 DYNAMIC ENGINES: EPIPLEXITY & STRATEGY
# =============================================================================
col_eng1, col_eng2 = st.columns(2)

with col_eng1:
    st.markdown("#### 🌀 EPIPLEXITY ENGINE")
    epiplexity_active = st.toggle("Activate Epiplexity Protocol", value=True, key="epi_active_final")
    epiplexity_intensity = st.select_slider("Fusion Depth:", options=["Linear", "Integrated", "Synergetic"], value="Integrated", key="epi_depth_final")

with col_eng2:
    st.markdown("#### 🧬 INNOVATION STRATEGY")
    selected_techniques = st.multiselect("Ideation Frameworks:", options=list(IDEATION_TECHNIQUES.keys()), default=["Six Thinking Hats"], key="strat_in_final")

st.divider()

# =============================================================================
# ❓ DUAL INQUIRY INTERFACE
# =============================================================================
col_inq1, col_inq2 = st.columns(2)

with col_inq1:
    user_query = st.text_area("❓ PHASE 1: Research Inquiry (Structural Foundation):", placeholder="Describe the factual core...", height=200, key="query_p1")

with col_inq2:
    idea_query = st.text_area("💡 PHASE 2: Innovation Prompt (Generative Targets):", placeholder="Describe the desired breakthroughs...", height=200, key="query_p2")

uploaded_file = st.file_uploader("📂 ATTACH DATA (.txt):", type=['txt'], key="file_up_final")
file_content = ""
if uploaded_file:
    file_content = uploaded_file.read().decode("utf-8")
    st.success(f"📎 {uploaded_file.name} Loaded")

# =============================================================================
# 5. SYNERGY EXECUTION ENGINE (PURE CEREBRAS SEQUENTIAL PIPELINE - UNABRIDGED)
# =============================================================================

if st.button("🚀 EXECUTE MULTI-DIMENSIONAL SEQUENTIAL SYNERGY PIPELINE", use_container_width=True, key="exec_pipeline_v2026_final_unabridged"):
    # Preverjamo varnostne ključe in nujne vnose za zagon 18D sistema
    if not cerebras_api_key:
        st.error("❌ Cerebras API key is required to proceed.")
    elif not user_query:
        st.warning("⚠️ Phase 1 Research Inquiry is required.")
    else:
        try:
            # --- 1. IZGRADNJA MANDATORNEGA 18D ANALITIČNEGA KONTEKSTA ---
            # Tukaj AI-ju pošljemo definicije izbranih tehnik in vse parametre vmesnika,
            # kar zagotavlja, da bo sinteza sledila izbranim metodam (npr. TRIZ, SCAMPER).
            strategy_descriptions = "\n".join([f"- {t}: {IDEATION_TECHNIQUES[t]}" for t in selected_techniques])
            
            active_context = f"""
            \n### MANDATORY SYSTEM INSTRUCTION: APPLY 18D ANALYTICAL BACKBONE ###
            The user has explicitly defined the following analytical constraints for this synthesis:
            - TARGET SCIENCE FIELDS: {', '.join(sel_sciences)}
            - APPLIED SCIENTIFIC PARADIGMS: {', '.join(sel_paradigms)}
            - APPLIED STRUCTURAL MODELS: {', '.join(sel_models)}
            - EXPERTISE LEVEL: {expertise}
            - PROJECT STRATEGIC GOAL: {goal_context}
            
            ### MANDATORY IDEATION FRAMEWORKS (USE THESE FOR INNOVATION GENERATION):
            {strategy_descriptions}
            \n###########################################################\n
            """

            with st.spinner('🔍 Accessing ORCID & Scholar databases for author verification...'):
                biblio_data = fetch_author_bibliographies(target_authors) if target_authors else ""
            
            file_context_str = f"\n\n[FILE DATA ATTACHMENT]:\n{file_content}" if file_content else ""
            biblio_context = f"\n\n[AUTHOR RESEARCH BACKGROUND]:\n{biblio_data}" if biblio_data else ""
            
            # Združevanje vseh parametrov, podatkov in poizvedbe za Fazo 1
            full_ai_input = f"{active_context}{user_query}{file_context_str}{biblio_context}"

            # Inicializacija skupnega Cerebras klienta za sekvenčno obdelavo
            cerebras_client = OpenAI(api_key=cerebras_api_key, base_url="https://api.cerebras.ai/v1")
            
            # --- PHASE 1: CEREBRAS (Foundation - IMA Architecture) ---
            # Fokus: Identiteta, Misija, Problem, Dejstva. AI mora zgraditi rigidno ogrodje resnice.
            with st.spinner(f'PHASE 1: Building Structural Foundation with {p1_model}...'):
                p1_response = cerebras_client.chat.completions.create(
                    model=p1_model,
                    messages=[
                        {"role": "system", "content": "You are the SIS Lead Hierarchologist. You MUST build a rigid factual foundation using the provided Scientific Paradigms and Structural Models. Avoid generative creativity; focus on ontological structural truth."}, 
                        {"role": "user", "content": full_ai_input}
                    ],
                    temperature=0.4
                )
                groq_synthesis = p1_response.choices[0].message.content
                st.session_state.groq_synthesis = groq_synthesis

            # --- PHASE 2: CEREBRAS (Innovation & Full Matrix Graph Generation) ---
            # Fokus: Dialektika, Perspektive, Indukcija. Generiranje uporabnih inovativnih idej.
            with st.spinner(f'PHASE 2: Generating 18D Strategic Innovations with {p2_model}...'):
                
                # --- PRIPRAVA POGOJNEGA PROTOKOLA ZA EPIPLEXITY ---
                if epiplexity_active:
                    epiplexity_logic_text = EPIPLEXITY_FRAMEWORK['logic_levels'].get(
                        epiplexity_intensity + ' (Low)' if epiplexity_intensity == 'Linear' else 
                        epiplexity_intensity + ' (Medium)' if epiplexity_intensity == 'Integrated' else 
                        epiplexity_intensity + ' (High)', "Integrated Logic"
                    )
                    
                    protocol_snippet = f"""
### EPIPLEXITY PROTOCOL ACTIVATED ###
Fusion Depth: {epiplexity_intensity}
Logic: {epiplexity_logic_text}
Mandatory Task: Identify 'Epiplexity Peaks'—points where at least three of the selected science fields intersect. 
Use 'EX' (Epiplexity Crossover) relations for these high-energy fusion links.
"""
                else:
                    protocol_snippet = """
### STANDARD SCIENTIFIC PROTOCOL ###
Focus: Standard interdisciplinary mapping. 
Constraint: Maintain clear boundaries between scientific disciplines. 
Do NOT use 'EX' (Epiplexity Crossover) relations. Use standard 'BT', 'NT', or 'AS' relations only.
"""

                # --- IZGRADNJA STROGEGA SISTEMSKEGA NAVODILA ZA STRATEŠKI GRAF ---
                samba_sys_prompt = f"""
You are the SIS Lead Strategic Innovation Architect.

### OPERATIONAL RULES
1. Provide a professional, human-readable STRATEGIC INNOVATION REPORT (Markdown).
2. DO NOT include JSON code or any semantic-graph-data inside the report text.
3. MANDATORY: After your report is completely finished, provide the graph data as a single block starting EXACTLY with the header: ### SEMANTIC_GRAPH_JSON

{protocol_snippet}

### ARCHITECTURAL COUPLING RULES (Strict Connection Logic)
When building the graph edges, you MUST follow these ontological constraints:
- **TT (Top Term)**: Use ONLY to link a 'hexagon' (Science Domain) to the central 'star' (Ultimate Goal).
- **BT/NT (Hierarchy)**: Use to organize 'hexagons' (Domains) or 'rectangles' (Facts).
- **IN (Inheritance)**: Use to link 'rectangles' (Specific Data) to their parent classes or domains.
- **AND/OR/XOR/NOT/IF-THEN (Logic)**: Use ONLY to link 'triangles' (Processes) to 'diamonds' (Innovations).
- **EX (Epiplexity)**: Use ONLY if high-energy fusion is detected between two disparate 'hexagons' (Sciences) to create a new 'diamond'.
- **Conflict**: Use to mark collisions between 'octagons' (Constraints) and 'diamonds' (Innovations).
- **HA (Hierarchical-Associative)**: Use for non-linear jumps between nodes that defy standard hierarchy.

### GEOMETRIC TAXONOMY (Shapes)
Assign shapes based on their ontological role:
- 'star': Ultimate Strategic Goals / Core Result.
- 'hexagon': Science Domains (Fields of Knowledge).
- 'diamond': Innovative Breakthroughs and useful ideas.
- 'triangle': Active Processes, Algorithms, and Methods.
- 'octagon': Risks, Constraints, and Ethical Barriers.
- 'ellipse': Human Factors (Psychology/Sociology).
- 'rectangle': Raw Facts and specific Data points.

### RELATIONSHIP MATRIX (Standardized Codes)
You MUST use these exact codes: TT, BT, NT, RT, EQ, AS, IN, Generalization, Specialization, Realization, Composition, Aggregation, Dependency, Conflict, Containment, HA, AND, OR, XOR, NOT, IF-THEN, EX.
"""

                samba_response = cerebras_client.chat.completions.create(
                    model=p2_model, 
                    messages=[
                        {"role": "system", "content": samba_sys_prompt}, 
                        {"role": "user", "content": f"PHASE 1 FOUNDATION (FACTS):\n{groq_synthesis}\n\nUSER INNOVATION TARGET: {idea_query}\nAPPLY TECHNIQUES: {', '.join(selected_techniques)}"}
                    ],
                    temperature=0.85,
                    top_p=0.9
                )
                cerebras_innovation = samba_response.choices[0].message.content

            # =============================================================================
            # 4. PROCESIRANJE REZULTATOV (ULTRA-RIGID TAXONOMY & AUTO-CORRECTION)
            # =============================================================================
            g_data = {"nodes": [], "edges": []}
            
            # 1. Ločevanje poročila od podatkov (Skrivanje kode pred uporabnikom)
            if "### SEMANTIC_GRAPH_JSON" in cerebras_innovation:
                parts = cerebras_innovation.split("### SEMANTIC_GRAPH_JSON")
                innovation_text = parts[0]
                json_raw = parts[1]
            else:
                innovation_text = cerebras_innovation
                json_raw = ""

            full_report = f"## 📚 Phase 1: Structural Foundation (Cerebras {p1_model})\n\n{groq_synthesis}\n\n---\n## 💡 Phase 2: Strategic Innovations (Cerebras {p2_model})\n\n{innovation_text}"
            
            nodes_to_link = []
            final_elements = []

            # 2. Iskanje JSON bloka z uporabo Regex
            json_match = re.search(r'(\{.*"nodes".*\})', json_raw if json_raw else cerebras_innovation, re.DOTALL | re.IGNORECASE)
            
            if json_match:
                try:
                    raw_json_str = json_match.group(1)
                    clean_json = raw_json_str.replace('\n', ' ').replace('\r', '').replace('\t', ' ')
                    g_data = json.loads(clean_json)
                except Exception:
                    st.warning("Note: Structural data parsing required correction.")

            # 3. PROCESIRANJE VOZLIŠČ (FAIL-SAFE GEOMETRY LOGIC)
            if g_data.get("nodes"):
                for n in g_data.get("nodes", []):
                    lbl = n.get("label", "Node")
                    nid = n.get("id", f"n{lbl}")
                    n_shape = n.get("shape", "rectangle").lower().strip()
                    
                    # --- FAIL-SAFE: Če AI pošlje napačno obliko glede na label, Python to popravi ---
                    l_lower = lbl.lower()
                    if n_shape == "rectangle":
                        if any(x in l_lower for x in ["goal", "metric", "universal", "core"]): n_shape = "star"
                        elif any(x in l_lower for x in list(KNOWLEDGE_BASE["Science fields"].keys())): n_shape = "hexagon"
                        elif any(x in l_lower for x in ["innovation", "idea", "breakthrough", "solution"]): n_shape = "diamond"
                        elif any(x in l_lower for x in ["algorithm", "process", "loop", "engine", "method"]): n_shape = "triangle"
                        elif any(x in l_lower for x in ["risk", "constraint", "conflict", "barrier"]): n_shape = "octagon"

                    # Določitev barvne matrike glede na končno obliko (Metodološka barvna metriki)
                    forced_colors = {
                        "star": "#FFD700", "hexagon": "#DDEBF7", "diamond": "#fd7e14", 
                        "triangle": "#28a745", "octagon": "#dc3545", "ellipse": "#17a2b8", 
                        "rectangle": "#adb5bd"
                    }
                    n_color = n.get("color", forced_colors.get(n_shape, "#DDEBF7"))
                    
                    # STROGA VELIKOSTNA HIERARHIJA
                    if n_shape == 'star': n_size = 145
                    elif n_shape == 'diamond': n_size = 125
                    elif n_shape == 'hexagon': n_size = 115
                    elif n_shape == 'octagon': n_size = 110
                    elif n_shape == 'ellipse': n_size = 100
                    elif n_shape == 'triangle': n_size = 95
                    else: n_size = 85
                    
                    final_elements.append({
                        "data": {
                            "id": nid, "label": lbl, "color": n_color, 
                            "shape": n_shape, "size": n_size, 
                            "description": n.get("description", "18D SIS Analyzed Node.")
                        }
                    })
                    nodes_to_link.append({"id": nid, "label": lbl})

                # 4. PROCESIRANJE POVEZAV (FULL STANDARD MATRIX)
                rel_map = {
                    "top term": "TT", "root": "TT", "broader term": "BT", "narrower term": "NT",
                    "related term": "RT", "equivalence": "EQ", "associative term": "AS", 
                    "instance": "IN", "inheritance": "IN", "example": "IN",
                    "hierarchical-associative": "HA", "epiplexity": "EX", "fusion": "EX",
                    "generalization": "Generalization", "specialization": "Specialization",
                    "composition": "Composition", "aggregation": "Aggregation",
                    "dependency": "Dependency", "conflict": "Conflict", "containment": "Containment",
                    "realization": "Realization", "if-then": "IF-THEN", "and": "AND", "or": "OR", 
                    "xor": "XOR", "not": "NOT"
                }

                if g_data.get("edges"):
                    for e in g_data.get("edges", []):
                        raw_rel = str(e.get("rel_type", "AS")).strip().lower()
                        rel = rel_map.get(raw_rel, raw_rel.upper() if len(raw_rel) < 5 else "AS")

                        # --- VAROVALKA ZA EPIPLEXITY ---
                        if rel == "EX" and not epiplexity_active:
                            rel = "AS"

                        # --- BARVNA MATRICA POVEZAV (Sinhronizirana s Chapter 1) ---
                        if rel in ["TT", "BT", "NT", "Generalization", "Realization", "Containment", "Composition"]:
                            e_color = "#1D3557" # Hierarhija (Navy)
                        elif rel in ["RT", "Dependency", "Aggregation"]:
                            e_color = "#2A9D8F" # Kontekst (Teal)
                        elif rel == "IN":
                            e_color = "#0077B6" # Inheritance (Blue)
                        elif rel in ["AS", "HA"]:
                            e_color = "#7B2CB1" # Asociacija (Purple)
                        elif rel == "EQ":
                            e_color = "#F1C40F" # Ekvivalenca (Gold)
                        elif rel == "Conflict":
                            e_color = "#B91D1D" # Konflikt (Red)
                        elif rel == "EX":
                            e_color = "#FF00FF" # Epiplexity (Magenta)
                        elif rel in ["AND", "OR", "XOR", "NOT", "IF-THEN"]:
                            e_color = "#28a745" # Logika (Green)
                        else:
                            e_color = "#ADB5BD"

                        final_elements.append({
                            "data": { 
                                "source": e.get("source"), 
                                "target": e.get("target"), 
                                "rel_type": rel,
                                "color": e_color 
                            }
                        })

            # --- 5. ANALITIČNI DASHBOARD & PRIKAZ REZULTATOV ---
            if epiplexity_active:
                st.divider()
                ex_edges = [e for e in final_elements if e.get('data', {}).get('rel_type') == 'EX']
                total_edges = [e for e in final_elements if 'source' in e.get('data', {})]
                ex_count = len(ex_edges)
                total_count = len(total_edges)
                epiplexity_score = (ex_count / total_count * 100) if total_count > 0 else 0
                
                st.markdown("### 📊 SYSTEM SYNERGY ANALYTICS")
                m1, m2, m3 = st.columns(3)
                with m1: st.metric("Epiplexity Score", f"{epiplexity_score:.1f}%", help="Degree of transdisciplinary fusion.")
                with m2: st.metric("Cage Breakers (EX)", ex_count, help="Links bypassing traditional scientific silos.")
                with m3: st.metric("Logical Flow Density", total_count, help="Total active connections in the knowledge map.")

                progress_color = "green" if epiplexity_score > 20 else "orange" if epiplexity_score > 10 else "red"
                st.markdown(f"""
                <div style="width: 100%; background-color: #eee; border-radius: 10px; margin-bottom: 20px;">
                    <div style="width: {min(epiplexity_score * 2, 100)}%; background-color: {progress_color}; padding: 5px; border-radius: 10px; text-align: center; color: white; font-weight: bold; font-size: 0.8em;">
                        TRANS-CAGE SYNTHESIS DENSITY: {epiplexity_score:.1f}%
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # B) RENDERING THE INTERACTIVE REPORT (With Regex Semantic Highlighter)
            st.subheader("🧱 INTEGRATED HIERARCHOLOGICAL REPORT")
            if biblio_data:
                with st.expander("📚 EXTRACTED AUTHOR BACKGROUND", expanded=False):
                    st.markdown(biblio_data)
            
            final_interactive_report = full_report
            if nodes_to_link:
                sorted_keywords = sorted(nodes_to_link, key=lambda x: len(x['label']), reverse=True)
                for item in sorted_keywords:
                    lbl = item['label']
                    if len(lbl) > 2:
                        g_url = urllib.parse.quote(lbl)
                        link_html = f'<a href="https://www.google.com/search?q={g_url}" target="_blank" class="semantic-node-highlight">{lbl}<i class="google-icon">↗</i></a>'
                        pattern = re.compile(rf'(?<!\w){re.escape(lbl)}(?!\w)', re.IGNORECASE | re.UNICODE)
                        final_interactive_report = pattern.sub(link_html, final_interactive_report, count=1)
            
            st.markdown(final_interactive_report, unsafe_allow_html=True)

            # C) INNOVATION DEEP-DIVE: DETAILED BREAKTHROUGH CATALOG
            if final_elements:
                innovations = [n['data'] for n in final_elements if n['data'].get('shape') == 'diamond']
                if innovations:
                    st.divider()
                    st.markdown("### 🚀 STRATEGIC INNOVATION DEEP-DIVE")
                    for inv in innovations:
                        st.markdown(f"""
                        <div style="background-color: #ffffff; border-left: 6px solid #fd7e14; padding: 25px; border-radius: 15px; box-shadow: 0 6px 15px rgba(0,0,0,0.1); border: 1px solid #eee; margin-bottom: 25px;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                <span style="background-color: #fff4ed; color: #fd7e14; padding: 5px 12px; border-radius: 20px; font-size: 0.75em; font-weight: 800; text-transform: uppercase; border: 1px solid #fd7e14;">Strategic Breakthrough</span>
                                <a href="https://www.google.com/search?q={urllib.parse.quote(inv['label'])}" target="_blank" style="text-decoration: none; color: #457b9d; font-size: 0.85em; font-weight: 600;">Technical Search ↗</a>
                            </div>
                            <h2 style="margin: 0 0 15px 0; color: #1d3557;">{inv['label']}</h2>
                            <div style="color: #333; font-size: 1.05em; line-height: 1.7; border-top: 1px solid #f0f0f0; padding-top: 15px;">
                                {inv.get('description', 'Detailed analytical breakdown available in the integrated report.')}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                # D) MINIMALIST SYSTEM LEGEND & MAIN GRAPH CALL
                st.markdown("""
                <div style="font-size: 0.78em; color: #444; background: #ffffff; padding: 15px 25px; border-radius: 15px; border: 1px solid #e9ecef; margin-top: 30px; box-shadow: 0 4px 12px rgba(0,0,0,0.03);">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
                        <div>
                            <b style="color: #1d3557; text-transform: uppercase; letter-spacing: 1px;">Nodes:</b> ⭐ Goal | ⬢ Domain | 💠 Innovation | △ Process | ▭ Data | ⬣ Rule
                        </div>
                        <div style="height: 30px; width: 1px; background: #dee2e6;"></div>
                        <div>
                            <b style="color: #1d3557; text-transform: uppercase; letter-spacing: 1px;">Semantic Layers:</b> 
                            <span style="color:#1d3557;">⬤ Hierarchical</span> | 
                            <span style="color:#7b2cb1;">⬤ Associative</span> | 
                            <span style="color:#0077b6;">⬤ Inheritance</span> | 
                            <span style="color:#ff00ff;">⬤ Epiplexity</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.subheader(f"🕸️ HYBRID SEMANTIC SYSTEM MAP ({graph_perspective.upper()} VIEW)")
                render_cytoscape_network(final_elements, layout_type=graph_perspective, container_id=f"cy_{int(time.time())}")
                
                # Shranjevanje elementov za razširjeno galerijo perspektiv
                st.session_state.final_graph_elements = final_elements
                st.session_state.report_ready = True

        except Exception as e:
            st.error(f"❌ Pipeline Failure: {str(e)}")

# =============================================================================
# 6. MULTI-PERSPECTIVE GALLERY (FULL 5 PERSPECTIVES SEQUENTIAL EXPORT)
# =============================================================================

if st.session_state.get('report_ready') and 'final_graph_elements' in st.session_state:
    st.divider()
    st.markdown('<h2 style="color: #1d3557; text-align: center;">🖼️ MULTI-PERSPECTIVE GRAPH GALLERY</h2>', unsafe_allow_html=True)
    st.info("💡 **NAVODILO ZA ZAPOREDNO SHRANJEVANJE:** Spodaj so zavihki z različnimi vizualnimi perspektivami istega znanja. Odprite posamezen zavihek in kliknite gumb **EXPORT PNG**, da shranite vseh 5 verzij.")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🌿 ORGANIC", "🌲 HIERARCHICAL", "⭕ CIRCULAR", "🎯 CONCENTRIC", "🔲 GRID"
    ])

    with tab1:
        st.markdown("**Organic View:** Discovery of natural thematic clusters.")
        render_cytoscape_network(st.session_state.final_graph_elements, layout_type="organic", container_id="gal_organic_final")
    
    with tab2:
        st.markdown("**Hierarchical View:** Strict logical tree from root term to data facts.")
        render_cytoscape_network(st.session_state.final_graph_elements, layout_type="hierarchical", container_id="gal_hierarchical_final")
        
    with tab3:
        st.markdown("**Circular View:** Focus on symmetric relationships (RT/EQ).")
        render_cytoscape_network(st.session_state.final_graph_elements, layout_type="circular", container_id="gal_circular_final")
        
    with tab4:
        st.markdown("**Concentric View:** Structural importance from Core to Periphery.")
        render_cytoscape_network(st.session_state.final_graph_elements, layout_type="concentric", container_id="gal_concentric_final")

    with tab5:
        st.markdown("**Grid View:** Organized alignment of all system elements.")
        render_cytoscape_network(st.session_state.final_graph_elements, layout_type="grid", container_id="gal_grid_final")

# =============================================================================
# 7. FOOTER & VERSIONING
# =============================================================================
st.divider()
st.caption(f"SIS Universal Knowledge Synthesizer | {VERSION_CODE} | System Date: {SYSTEM_DATE} | Operating Date: July 23, 2026")
