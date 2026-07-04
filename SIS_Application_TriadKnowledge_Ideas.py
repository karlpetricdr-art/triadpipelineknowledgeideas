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
    Posodobljen motor z več perspektivami (Multi-Perspective Layout Engine).
    Vključuje UML, ISO Thesaurus in Logične konektorje (AND, OR, XOR, NOT, IF-THEN).
    """
    
    # Mapiranje Python izbire v Cytoscape JS konfiguracije
    layout_configs = {
        "organic": """{ 
            name: 'cose', 
            idealEdgeLength: 120, 
            nodeOverlap: 50, 
            refresh: 20, 
            fit: true, 
            padding: 50, 
            nodeRepulsion: 1000000,
            edgeElasticity: 100,
            nestingFactor: 1.2,
            numIter: 1500
        }""",
        "hierarchical": """{ 
            name: 'breadthfirst', 
            directed: true, 
            padding: 50, 
            circle: false, 
            spacingFactor: 1.75,
            maximal: true
        }""",
        "circular": """{ 
            name: 'circle', 
            padding: 50, 
            radius: 400,
            spacingFactor: 0.8
        }""",
        "concentric": """{ 
            name: 'concentric', 
            minNodeSpacing: 60, 
            concentric: function(node){ return node.data('size'); },
            levelWidth: function(nodes){ return 10; },
            padding: 50
        }""",
        "grid": """{ 
            name: 'grid', 
            rows: 5, 
            padding: 50, 
            spacingFactor: 1.2 
        }"""
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
                            'border-opacity': 0.8,
                            'text-outline-color': '#ffffff',
                            'text-outline-width': 2,
                            'box-shadow': '0 4px 10px rgba(0,0,0,0.2)'
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
                            'color': '#2a9d8f',
                            'curve-style': 'unbundled-bezier',
                            'control-point-step-size': 40,
                            'target-arrow-color': 'data(color)',
                            'target-arrow-shape': 'vee',
                            'text-background-opacity': 1,
                            'text-background-color': '#ffffff',
                            'text-background-padding': '3px',
                            'text-background-shape': 'roundrectangle',
                            'edge-distances': 'node-position',
                            'opacity': 0.8
                        }}
                    }},
                    /* --- UML NOTACIJA --- */
                    {{ selector: 'edge[rel_type="Generalization"]', style: {{ 'target-arrow-shape': 'triangle', 'target-arrow-fill': 'hollow', 'width': 3 }} }},
                    {{ selector: 'edge[rel_type="Realization"]', style: {{ 'line-style': 'dashed', 'target-arrow-shape': 'triangle', 'target-arrow-fill': 'hollow' }} }},
                    {{ selector: 'edge[rel_type="Composition"]', style: {{ 'source-arrow-shape': 'diamond', 'source-arrow-fill': 'filled', 'width': 4 }} }},
                    {{ selector: 'edge[rel_type="Aggregation"]', style: {{ 'source-arrow-shape': 'diamond', 'source-arrow-fill': 'hollow', 'width': 3 }} }},
                    {{ selector: 'edge[rel_type="Dependency"]', style: {{ 'line-style': 'dashed', 'target-arrow-shape': 'vee' }} }},
                    {{ selector: 'edge[rel_type="Conflict"]', style: {{ 'width': 6, 'line-color': '#b91d1d', 'line-style': 'solid', 'target-arrow-color': '#b91d1d', 'target-arrow-shape': 'triangle-cross', 'source-arrow-shape': 'triangle-cross', 'source-arrow-color': '#b91d1d' }} }},
                    {{ selector: 'edge[rel_type="Specialization"]', style: {{ 'line-style': 'dashed', 'line-color': '#000000', 'target-arrow-shape': 'triangle', 'target-arrow-fill': 'filled', 'target-arrow-color': '#000000', 'width': 2 }} }},
                    {{ selector: 'edge[rel_type="Containment"]', style: {{ 'line-color': '#1d3557', 'target-arrow-shape': 'circle', 'target-arrow-color': '#1d3557', 'target-arrow-fill': 'hollow', 'width': 4 }} }},
                    
                    /* --- ISO THESAURUS --- */
                    {{ selector: 'edge[rel_type="TT"]', style: {{ 'width': 6, 'line-color': '#1d3557' }} }},
                    {{ selector: 'edge[rel_type="BT"]', style: {{ 'width': 4, 'line-color': '#1d3557' }} }},
                    {{ selector: 'edge[rel_type="NT"]', style: {{ 'width': 4, 'line-color': '#1d3557' }} }},
                    {{ selector: 'edge[rel_type="EQ"]', style: {{ 'line-style': 'double', 'width': 5, 'line-color': '#f1c40f' }} }},
                    {{ selector: 'edge[rel_type="RT"]', style: {{ 'line-style': 'dotted', 'width': 2, 'line-color': '#2a9d8f', 'target-arrow-shape': 'none' }} }},
                    {{ selector: 'edge[rel_type="AS"]', style: {{ 'line-style': 'dashed', 'width': 2, 'line-color': '#7b2cb1' }} }},
                    {{ selector: 'edge[rel_type="IN"]', style: {{ 'line-style': 'dotted', 'width': 3, 'line-color': '#0077b6', 'target-arrow-shape': 'triangle' }} }},
                    
                    /* --- LOGIČNI KONEKTORJI (Decision Logic) --- */
                    {{ selector: 'edge[rel_type="AND"]', style: {{ 'width': 5, 'line-color': '#00FF00', 'target-arrow-color': '#00FF00', 'target-arrow-shape': 'triangle' }} }},
                    {{ selector: 'edge[rel_type="OR"]', style: {{ 'width': 3, 'line-color': '#00BFFF', 'line-style': 'dashed', 'target-arrow-color': '#00BFFF', 'target-arrow-shape': 'vee' }} }},
                    {{ selector: 'edge[rel_type="XOR"]', style: {{ 'width': 4, 'line-color': '#FF8C00', 'line-style': 'double', 'target-arrow-color': '#FF8C00', 'target-arrow-shape': 'diamond' }} }},
                    {{ selector: 'edge[rel_type="NOT"]', style: {{ 'width': 4, 'line-color': '#FF0000', 'line-style': 'dashed', 'target-arrow-color': '#FF0000', 'target-arrow-shape': 'tee' }} }},
                    {{ selector: 'edge[rel_type="IF-THEN"]', style: {{ 'width': 4, 'line-color': '#FFD700', 'target-arrow-color': '#FFD700', 'target-arrow-shape': 'triangle', 'arrow-scale': 1.3 }} }},

                    /* Poudarek na zvezdah (Macro cilji) */
                    {{ selector: 'node[shape="star"]', style: {{ 'font-size': '16px', 'width': 130, 'height': 130, 'border-width': 5, 'border-color': '#FFD700' }} }}
                ],
                layout: {selected_layout}
            }});

            document.getElementById('save_btn').addEventListener('click', function() {{
                var png64 = cy.png({{full: true, bg: 'white', scale: 2}});
                var link = document.createElement('a');
                var timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
                link.href = png64; 
                link.download = 'hierarchograph_{layout_type}_' + timestamp + '.png';
                link.click();
            }});
        }});
    </script>
    """
    components.html(cyto_html, height=900)

def fetch_author_bibliographies(author_input):
    if not author_input: return ""
    author_list = [a.strip() for a in author_input.split(",")]
    comprehensive_biblio = ""
    headers = {"Accept": "application/json"}
    for auth in author_list:
        try:
            s_res = requests.get(f"https://pub.orcid.org/v3.0/search/?q={auth}", headers=headers, timeout=6).json()
            if s_res.get('result'):
                orcid_id = s_res['result'][0]['orcid-identifier']['path']
                r_res = requests.get(f"https://pub.orcid.org/v3.0/{orcid_id}/record", headers=headers, timeout=6).json()
                works = r_res.get('activities-summary', {}).get('works', {}).get('group', [])
                comprehensive_biblio += f"#### 🆔 ORCID: {auth.upper()} ({orcid_id})\n"
                for work in works[:12]:
                    summary = work.get('work-summary', [{}])[0]
                    title = summary.get('title', {}).get('title', {}).get('value', 'Unknown Title')
                    # Boljše iskanje letnice
                    pub_date = summary.get('publication-date')
                    year = pub_date.get('year', {}).get('value', 'n.d.') if pub_date else 'n.d.'
                    comprehensive_biblio += f"- **{year}**: {title}\n"
                comprehensive_biblio += "\n---\n"
        except: pass
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
# 4. KONČNI POPRAVLJEN SIDEBAR (Z SAMBANOVO IN UNIKATNIMI KLJUČI)
# =============================================================================
with st.sidebar:
    # 1. Original 3D Relief Logo
    st.markdown(f'<div class="sidebar-logo-container"><img src="data:image/svg+xml;base64,{get_svg_base64(SVG_3D_RELIEF)}" width="220"></div>', unsafe_allow_html=True)
    
    # 2. Date Badge
    st.markdown(f'<div class="date-badge">{SYSTEM_DATE.upper()}</div>', unsafe_allow_html=True)
    
    st.header("⚙️ SYSTEM CONTROL")
    
    # 3. Dual API Keys Access
    st.subheader("🔑 Dual-Engine API Access")
    cerebras_api_key = st.text_input("Cerebras Key (Phase 1):", type="password", key="side_cerebras_v2026")
    gemini_api_key = st.text_input("Google Gemini Key (Phase 2):", type="password", key="side_gemini_v2026")
    
    # Izbira modelov za Cerebras po tvoji želji
    cerebras_model_id = st.selectbox(
        "Cerebras Model (Phase 1):", 
        ["gpt-oss-120b", "gemma-4-31b"], 
        index=0, 
        key="side_cerebras_model_v2026"
    )

    # 4. Google Gemini (Phase 2) - Razširjen nabor za leto 2026
    gemini_model_id = st.selectbox(
        "Gemini Model (Phase 2):", 
        [
            "gemini-1.5-flash-latest", # Najbolj verjetno, da deluje v EU
            "gemini-1.5-pro-latest",
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-1.5-flash-8b",     # Lažji model, pogosto dostopnejši
            "gemini-2.0-flash-exp"     # Eksperimentalni model nove generacije
        ], 
        index=0, 
        key="side_gemini_model_select"
    )
    
    st.divider()

    # --- NOVO: IZBIRA PERSPEKTIVE GRAFA ---
    st.subheader("🎨 GRAPH PERSPECTIVE")
    graph_perspective = st.selectbox(
        "Select Visual Layout Engine:",
        options=["organic", "hierarchical", "circular", "concentric", "grid"],
        index=0,
        format_func=lambda x: x.capitalize() + " View",
        help="Organic: Naravno grupiranje | Hierarchical: Drevesna struktura | Circular: Relacije | Concentric: Centralnost",
        key="side_graph_layout_v2026"
    )
    
    st.divider()
    
    # 5. Reset in Guide Gumbi (Dodani unikatni ključi)
    col_res, col_gui = st.columns(2)
    with col_res:
        if st.button("♻️ RESET", key="sidebar_reset_btn_unique"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    with col_gui:
        if st.button("📖 GUIDE", key="sidebar_guide_btn_unique"):
            st.session_state.show_user_guide = not st.session_state.show_user_guide
            st.rerun()
            
    st.divider()
    st.subheader("🌐 EXTERNAL CONNECTORS")
    st.link_button("📂 GitHub Repository", "https://github.com/", use_container_width=True, key="side_git_link")
    st.link_button("🆔 ORCID Registry", "https://orcid.org/", use_container_width=True, key="side_orcid_link")
    st.link_button("🎓 Google Scholar", "https://scholar.google.com/", use_container_width=True, key="side_scholar_link")
    
    # 6. KNOWLEDGE EXPLORER (POSODOBLJENA RAZŠIRJENA RAZLIČICA)
    st.divider()
    st.subheader("📚 KNOWLEDGE EXPLORER")

    with st.expander("👤 User Profile Ontologies", expanded=False):
        for p, d in KNOWLEDGE_BASE["User profiles"].items(): 
            st.markdown(f"**{p}**: {d['description']}")

    with st.expander("🧠 Mental Approach (MA) Map", expanded=False):
        for m, d in MENTAL_APPROACHES_ONTOLOGY["nodes"].items(): 
            st.markdown(f"• **{m}**: {d['desc']}")

    with st.expander("🏛️ Metamodel (IMA) Structures", expanded=False):
        for n, d in HUMAN_THINKING_METAMODEL["nodes"].items(): 
            st.markdown(f"• **{n}**: {d['desc']}")

    with st.expander("📐 Hierarchology & Hierarchography", expanded=False):
        st.markdown("**Core Concepts:**")
        for key, val in HIERARCHOLOGY_ONTOLOGY["core_definitions"].items():
            st.markdown(f"• **{key}**: {val}")
        
        st.markdown("---")
        st.markdown("**Advanced Mapping Connectors:**")
        st.markdown("• ⬛ ┄ ➤ **Specialization**: Deduktivna izpeljava iz splošnega zakona v specifičen primer (nasprotje generalizacije).")
        st.markdown("• 🟦 — ◯ **Containment**: Močna strukturna vsebovanost; označuje elemente, ujetne znotraj 'znanstvene kletke'.")

    with st.expander("🔬 Science Taxonomy & Levels", expanded=False):
        st.markdown("**Field Domains:**")
        for s in sorted(KNOWLEDGE_BASE["Science fields"].keys()): 
            st.markdown(f"• **{s}**")
        
        st.markdown("---")
        st.markdown("**Hierarchical Levels:**")
        for level, desc in HIERARCHOLOGY_ONTOLOGY["hierarchical_levels"].items():
            st.markdown(f"• **{level}**: {desc}")
            
        st.markdown("---")
        st.markdown("**Logic Flows:**")
        st.markdown(f"• *Internal (Inductive):* {HIERARCHOLOGY_ONTOLOGY['operational_logic']['Internal Processes']}")
        st.markdown(f"• *External (Deductive):* {HIERARCHOLOGY_ONTOLOGY['operational_logic']['External Functioning']}")
        
        st.markdown("---")
        st.markdown("**Hierarchography Methods:**")
        st.write(", ".join(HIERARCHOLOGY_ONTOLOGY["hierarchography_tools"]))

    with st.expander("🏗️ Structural Model Context", expanded=False):
        for m, d in KNOWLEDGE_BASE["Structural models"].items(): 
            st.markdown(f"**{m}**: {d}")

# --- MAIN PAGE CONTENT ---
st.markdown('<h1 class="main-header-gradient">🧱 SIS Universal Knowledge Synthesizer</h1>', unsafe_allow_html=True)
st.markdown(f"**Sequential Multi-Engine Pipeline** | Current Operating Date: **{SYSTEM_DATE}**")

if st.session_state.show_user_guide:
    st.info(f"""
    **Sequential Synergy Pipeline Workflow (Updated Feb 24, 2026):**
    1. **Key Input**: Enter your Cerebras (Phase 1) and Google Gemini (Phase 2) API keys in the sidebar.
    2. **Research Foundation (Step 1)**: Cerebras performs structural synthesis foundation using Integrated Metamodel Architecture (IMA).
    3. **Innovation Prompt (Step 2)**: Google Gemini takes Cerebras's work and generates radical 'Useful Innovative Ideas' using Mental Approaches (MA) logic.
    4. **Visualization**: The interactive 18D graph maps structural facts against generative ideas.
    """)

# REFERENCE ARCHITECTURE BOXES
col_ref1, col_ref2 = st.columns(2)
with col_ref1:
    st.markdown("""<div class="metamodel-box"><b>🏛️ Phase 1: Cerebras (IMA Architecture)</b><br>Structural reasoning building the factual foundation. Focus: Identity, Mission, Problem. </div>""", unsafe_allow_html=True)
with col_ref2:
    st.markdown("""<div class="mental-approach-box"><b>🧠 Phase 2: Google Gemini (MA Architecture)</b><br>Cognitive transformation generating innovative solutions. Focus: Dialectics, Perspective, Induction.</div>""", unsafe_allow_html=True)

st.markdown("### 🛠️ CONFIGURE SYNERGY PIPELINE")

# Entry Rows
r1c1, r1c2, r1c3 = st.columns([1.5, 2, 1])
with r1c1: target_authors = st.text_input("👤 Authors for ORCID Analysis:", placeholder="Karl Petrič, Samo Kralj, Teodor Petrič")
with r1c2: sel_sciences = st.multiselect("2. Select Science Fields:", sorted(list(KNOWLEDGE_BASE["Science fields"].keys())), default=["Physics", "Psychology", "Sociology"])
with r1c3: expertise = st.select_slider("3. Expertise Level:", ["Novice", "Intermediate", "Expert"], value="Expert")

r2c1, r2c2, r2c3 = st.columns(3)
with r2c1: sel_paradigms = st.multiselect("4. Scientific Paradigms:", list(KNOWLEDGE_BASE["Scientific paradigms"].keys()), default=["Rationalism"])
with r2c2: sel_models = st.multiselect("5. Structural Models:", list(KNOWLEDGE_BASE["Structural models"].keys()), default=["Concepts"])
with r2c3: goal_context = st.selectbox("6. Strategic Project Goal:", ["Scientific Research", "Problem Solving", "Educational", "Policy Making"])

st.divider()
# --- ADVANCED MULTI-IDEATION UI ---
st.markdown("### 🧬 INNOVATION STRATEGY")
selected_techniques = st.multiselect(
    "Select Strategic Ideation Frameworks (Pick one or more):", 
    options=list(IDEATION_TECHNIQUES.keys()), 
    default=["Six Thinking Hats"],
    help="If you select multiple, the AI will synthesize them into a hybrid innovation strategy."
)

if not selected_techniques:
    st.warning("⚠️ Please select at least one technique for Phase 2.")
else:
    # Build a combined description for the info box
    combined_desc = " | ".join([f"**{t}**: {IDEATION_TECHNIQUES[t]}" for t in selected_techniques])
    st.info(f"**Active Hybrid Strategy:** {combined_desc}")
st.divider()

# DUAL INQUIRY INTERFACE
col_inq1, col_inq2, col_inq3 = st.columns([2, 2, 1])
with col_inq1:
    user_query = st.text_area("❓ STEP 1: Research Inquiry (for CEREBRAS):", placeholder="Fact-based Foundational Inquiry...", height=200)
with col_inq2:
    idea_query = st.text_area("💡 STEP 2: Innovation Prompt (for GEMINI):", placeholder="Targets for innovative idea production...", height=200)
# --- POPRAVEK KORAK 1: Branje vsebine datoteke ---
# --- KORAK 1: File Upload with English Translation ---
with col_inq3:
    uploaded_file = st.file_uploader("📂 ATTACH DATA (.txt only):", type=['txt'], key="final_file_uploader_v2")
    file_content = "" 
    if uploaded_file is not None:
        try:
            file_content = uploaded_file.read().decode("utf-8")
            st.success(f"📎 {uploaded_file.name} uploaded!")
            # Prevedeno v angleščino:
            with st.expander("File Preview"):
                st.text(file_content[:300] + "...")
        except Exception as e:
            st.error(f"Error reading file: {e}")

# =============================================================================
# 5. SYNERGY EXECUTION ENGINE (WITH CONDITIONAL ACTIVATION)
# =============================================================================

if st.button("🚀 EXECUTE MULTI-DIMENSIONAL SEQUENTIAL SYNERGY PIPELINE", use_container_width=True, key="exec_pipeline_v2026"):
    # POPRAVEK: Preverjamo gemini_api_key namesto sambanova
    if not cerebras_api_key or not gemini_api_key:
        st.error("❌ Dual-Model synergy requires both Cerebras and Google Gemini keys.")
    elif not user_query:
        st.warning("⚠️ Phase 1 Research Inquiry is required.")
    else:
        try:
            # --- CONDITIONAL DIMENSION ACTIVATION ---
            # The system only injects sidebar selections if [ACTIVATE] is present in the prompt.
            trigger_keyword = "[ACTIVATE]"
            active_context = ""
            
            if trigger_keyword in user_query or (idea_query and trigger_keyword in idea_query):
                active_context = f"""
                \n### MANDATORY SYSTEM INSTRUCTION: APPLY INTERFACE PARAMETERS ###
                The user has explicitly activated the following constraints for this specific run:
                - Target Science Fields: {', '.join(sel_sciences)}
                - Applied Scientific Paradigms: {', '.join(sel_paradigms)}
                - Structural Model Focus: {', '.join(sel_models)}
                - Innovation Frameworks: {', '.join(selected_techniques)}
                - Expertise Level: {expertise}
                - Project Strategic Goal: {goal_context}
                \n###########################################################\n
                """

            with st.spinner('🔍 Accessing ORCID & Scholar databases...'):
                biblio_data = fetch_author_bibliographies(target_authors) if target_authors else ""
            
            file_context_str = f"\n\n[FILE CONTEXT]:\n{file_content}" if file_content else ""
            biblio_context = f"\n\n[AUTHOR RESEARCH BACKGROUND]:\n{biblio_data}" if biblio_data else ""
            
            # Combine the trigger context with the user query
            full_ai_input = f"{active_context}{user_query}{file_context_str}{biblio_context}"

            # Inicializacija povezav (Cerebras ostaja za Phase 1)
            cerebras_client = OpenAI(api_key=cerebras_api_key, base_url="https://api.cerebras.ai/v1")
            
            # --- PHASE 1: CEREBRAS (Logična sinteza namesto Groq) ---
            with st.spinner('PHASE 1: Building Architecture (Cerebras Logic)...'):
                p1_response = cerebras_client.chat.completions.create(
                    model=cerebras_model_id,
                    messages=[
                        {"role": "system", "content": "You are the SIS Lead Hierarchologist. If the user provides specific Paradigms or Models in the 'MANDATORY SYSTEM INSTRUCTION', you MUST prioritize them in your structural analysis."}, 
                        {"role": "user", "content": full_ai_input}
                    ],
                    temperature=0.4
                )
                # Rezultat shranimo v isto spremenljivko, da ostala koda deluje brez sprememb
                groq_synthesis = p1_response.choices[0].message.content
                st.session_state.groq_synthesis = groq_synthesis

            # --- 3. PHASE 2: GOOGLE GEMINI (ZAMENJAVA ZA SAMBANOVO - PREKO NEPOSREDNEGA REST ADAPTERJA) ---
            with st.spinner(f'PHASE 2: Gemini ({gemini_model_id}) generating radical innovations...'):
                samba_sys_prompt = f"""
You are the SIS Lead Strategic Innovation Architect and Hierarchographist. 
Your task is to transform the structural analysis from Phase 1 into a visionary Innovation Report and a perfectly mapped Hierarchographic Network.

### 1. REPORT REQUIREMENTS
Write a "STRATEGIC INNOVATION REPORT". 
- For each innovation, provide a technical title, a detailed 3-4 sentence strategic explanation, and its cross-disciplinary impact.
- Use professional terminology.
- IMPORTANT: Inside the JSON section, do NOT use double quotes (") within descriptions. Use single quotes (') instead to ensure the JSON structure remains valid.

### 2. RELATIONSHIP LOGIC MATRIX (MANDATORY FOR JSON)
You must interconnect nodes using the following two standards:

A) THESAURUS LOGIC (ISO 25964 / Conceptual Taxonomy):
- 'TT' (Top Term): Absolute root of a knowledge domain.
- 'BT' (Broader Term): Higher-level class/concept (Genus).
- 'NT' (Narrower Term): Lower-level sub-concept (Species).
- 'RT' (Related Term): Symmetrical lateral association between concepts.
- 'EQ' (Equivalence): Synonyms or identical concepts in different fields.
- 'AS' (Associative): Functional connection (e.g., Process AS Result, Tool AS Action).
- 'IN' (Instance): Category to a specific unique entity/example (e.g., Physics IN Theory of Relativity).

B) UML LOGIC (OMG Standard / Structural Architecture):
- 'Generalization': 'Is-a' Inheritance (e.g., Quantum Physics is a Generalization of Physics).
- 'Specialization': The deductive opposite of Generalization. A downward move from a general law to a specific refined case.
- 'Containment': A strong structural inclusion where a node is trapped or housed inside another. Mandatory for mapping concepts within a 'Scientific Cage'.
- 'Realization': An Innovation/Tool implementing a Goal/Vision.
- 'Composition': Strong 'Part-of' (Life-cycle dependent).
- 'Aggregation': Weak 'Part-of' (Independent existence).
- 'Dependency': Node A requires Node B to function.
- 'Conflict': A Systemic tension, incompatibility, or direct conflict between two elements.

C) LOGICAL CONNECTORS (Decision Logic):
- 'AND': Močna sinteza, kjer morata oba pogoja obstajati hkrati (Veznik IN).
- 'OR': Alternativna pot ali izbira med koncepti (Veznik ALI).
- 'XOR': Izključujoči ALI (Koncepta sta nezdružljiva ali paradoksalna).
- 'NOT': Negacija ali prepovedana povezava (Meja znanstvene kletke).
- 'IF-THEN': Vzročna posledica ali pogojni prehod.

### 3. MANDATORY GEOMETRY (SHAPES)
- 'star': Ultimate Goals / Macro-Vision.
- 'hexagon': Science Fields / Academic Domains.
- 'diamond': Strategic Innovations / New Breakthroughs.
- 'triangle': Active Processes / Methods / Vectors.
- 'octagon': Constraints / Ethical Boundaries / Rules.
- 'ellipse': Human Factors / Identities / Biological Entities.
- 'rectangle': Facts / Data Points / Micro-components.

### 4. OUTPUT FORMAT
MANDATORY JSON STRUCTURE:
### SEMANTIC_GRAPH_JSON
{{
  "nodes": [
    {{"id": "n1", "label": "LABEL", "shape": "diamond", "color": "#fd7e14", "description": "Full detailed description for the deep-dive."}}
  ],
  "edges": [
    {{"source": "n1", "target": "n2", "rel_type": "AS"}},
    {{"source": "n3", "target": "n1", "rel_type": "Composition"}}
  ]
}}
"""
                # VARNO ČIŠČENJE ID-JA MODELA
                clean_model_id = gemini_model_id.replace("models/", "")
                
                # NEPOSREDEN REST KLIC (Uporaba v1beta za najboljšo kompatibilnost v EU)
                gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{clean_model_id}:generateContent?key={gemini_api_key}"
                
                headers = {'Content-Type': 'application/json'}
                
                # Priprava telesa prošnje po Googlovih specifikacijah
                payload = {
                    "contents": [{
                        "parts": [{
                            "text": f"{samba_sys_prompt}\n\nPHASE 1 FOUNDATION:\n{groq_synthesis}\n\nUSER GOAL: {idea_query}{file_context_str}"
                        }]
                    }],
                    "generationConfig": {
                        "temperature": 0.7,
                        "topP": 0.9,
                        "maxOutputTokens": 8192
                    },
                    "safetySettings": [
                        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
                    ]
                }

                # Izvedba mrežne prošnje s knjižnico requests
                response_rest = requests.post(gemini_url, headers=headers, json=payload)
                
                if response_rest.status_code == 200:
                    res_json = response_rest.json()
                    # Izvlečemo tekst iz Googlovega specifičnega JSON formata
                    if 'candidates' in res_json and len(res_json['candidates']) > 0:
                        cerebras_innovation = res_json['candidates'][0]['content']['parts'][0]['text']
                    else:
                        cerebras_innovation = "❌ Error: Gemini returned no content candidates."
                else:
                    st.error(f"Gemini API Error {response_rest.status_code}: {response_rest.text}")
                    cerebras_innovation = "❌ Error: Could not connect to Gemini."

            # --- 4. PROCESIRANJE REZULTATOV (Z GEOMETRIJSKO LOGIKO) ---
            # Inicializacija g_data, da preprečimo napako 'name not defined'
            g_data = {"nodes": [], "edges": []}
            
            if "### SEMANTIC_GRAPH_JSON" in cerebras_innovation:
                parts = cerebras_innovation.split("### SEMANTIC_GRAPH_JSON")
                innovation_text = parts[0]
                json_raw = parts[1]
            else:
                innovation_text = cerebras_innovation
                json_raw = ""

            full_report = f"## 📚 Phase 1: Foundation (Cerebras)\n\n{groq_synthesis}\n\n---\n## 💡 Phase 2: Strategic Innovations (Google Gemini)\n\n{innovation_text}"
            
            nodes_to_link = []
            final_elements = []

            # Izboljšano iskanje in varnostno čiščenje JSON-a
            json_match = re.search(r'(\{.*"nodes".*\})', json_raw if json_raw else cerebras_innovation, re.DOTALL | re.IGNORECASE)
            
            if json_match:
                try:
                    # 1. Izvlečemo surovi JSON tekst
                    raw_json_str = json_match.group(1)
                    # 2. Očistimo nove vrstice in nevarne znake, ki lomijo format
                    clean_json = raw_json_str.replace('\n', ' ').replace('\r', '')
                    # 3. Poskusimo prebrati JSON podatke
                    g_data = json.loads(clean_json)
                except Exception as json_err:
                    st.warning(f"Note: Graph structure issue: {json_err}")

            # --- PROCESIRANJE VOZLIŠČ Z DINAMIČNO VELIKOSTJO ---
            if g_data.get("nodes"):
                for n in g_data.get("nodes", []):
                    lbl = n.get("label", "Node")
                    nid = n.get("id", f"n{lbl}")
                    n_color = n.get("color", "#DDEBF7")
                    n_shape = n.get("shape", "rectangle")
                    
                    # Velikostna hierarhija glede na obliko
                    if n_shape == 'star': n_size = 125
                    elif n_shape == 'diamond': n_size = 110
                    elif n_shape == 'octagon': n_size = 105
                    elif n_shape == 'hexagon': n_size = 100
                    elif n_shape == 'triangle': n_size = 95
                    elif n_shape == 'ellipse': n_size = 90
                    else: n_size = 85
                    
                    nodes_to_link.append({"id": nid, "label": lbl})
                    final_elements.append({
                        "data": {"id": nid, "label": lbl, "color": n_color, "shape": n_shape, "size": n_size, "description": n.get("description", "Detail breakdown in report.")}
                    })

                # --- PROCESIRANJE POVEZAV (UML + THESAURUS + LOGIC) ---
                for e in g_data.get("edges", []):
                    rel = e.get("rel_type", "Association")
                    
                    # A) UML IN STRUKTURNA LOGIKA (Rdeča/Črna/Modra skala)
                    if rel in ["Generalization", "Realization", "Composition", "Aggregation", "Dependency", "Specialization", "Containment", "Conflict"]:
                        if rel == "Conflict":
                            e_color = "#b91d1d"  # Temno rdeča za trčenje/spor
                        elif rel == "Specialization":
                            e_color = "#000000"  # Črna za dedukcijo
                        elif rel == "Containment":
                            e_color = "#1D3557"  # Temno modra za "Scientific Cage"
                        elif rel == "Generalization":
                            e_color = "#E63946"  # UML rdeča
                        elif rel == "Realization":
                            e_color = "#E63946"  # UML rdeča
                        else:
                            e_color = "#E63946"  # Privzeta UML rdeča (Dependency, Aggregation...)
                            
                    # B) ISO THESAURUS (Hierarhologija - Modra/Vijolična skala)
                    elif rel in ["BT", "NT", "TT"]:
                        e_color = "#1D3557"  # Temno modra (Nivoji)
                    elif rel == "IN":
                        e_color = "#0077B6"  # Svetlo modra (Instanca)
                    elif rel == "AS":
                        e_color = "#7B2CB1"  # Vijolična (Asociativna)
                    elif rel == "EQ":
                        e_color = "#F1C40F"  # Rumena (Ekvivalenca)
                    elif rel == "RT":
                        e_color = "#2A9D8F"  # Zelena (Povezano)

                    # C) LOGIČNI KONEKTORJI (Decision Logic - Neon skala)
                    elif rel == "AND":
                        e_color = "#00FF00"  # Neon zelena
                    elif rel == "OR":
                        e_color = "#00BFFF"  # Svetlo modra
                    elif rel == "XOR":
                        e_color = "#FF8C00"  # Oranžna
                    elif rel == "NOT":
                        e_color = "#FF0000"  # Rdeča
                    elif rel == "IF-THEN":
                        e_color = "#FFD700"  # Zlata
                        
                    else:
                        e_color = "#ADB5BD"  # Če tipa ne pozna = Siva

                    final_elements.append({
                        "data": {
                            "source": e.get("source"), 
                            "target": e.get("target"), 
                            "rel_type": rel, 
                            "color": e_color
                        }
                    })

            # Avtomatsko povezovanje besedila z grafom (Highlighting)
            final_markdown = full_report
            if nodes_to_link:
                # Razvrstimo ključne besede po dolžini (daljše prej), da se krajše ne vmešavajo
                sorted_keywords = sorted(nodes_to_link, key=lambda x: len(x['label']), reverse=True)
                for item in sorted_keywords:
                    lbl = item['label']
                    if len(lbl) > 2:
                        g_url = urllib.parse.quote(lbl)
                        link_html = f'<a href="https://www.google.com/search?q={g_url}" target="_blank" class="semantic-node-highlight">{lbl}<i class="google-icon">↗</i></a>'
                        
                        # Unicode-safe regex
                        pattern = re.compile(rf'(?<!\w){re.escape(lbl)}(?!\w)', re.IGNORECASE | re.UNICODE)
                        
                        # Linkamo le prvo pojavitev za preglednost
                        final_markdown = pattern.sub(link_html, final_markdown, count=1)

            # 5b. RENDERING THE INTERACTIVE REPORT
            st.subheader("🧱 INTEGRATED HIERARCHOLOGICAL REPORT")
            if biblio_data:
                with st.expander("📚 EXTRACTED AUTHOR BACKGROUND", expanded=False):
                    st.markdown(biblio_data)
            
            # Display the full linked report (P1 + P2)
            st.markdown(final_markdown, unsafe_allow_html=True)

            # 5c. INNOVATION DEEP-DIVE: DETAILED BREAKTHROUGH CATALOG
            if final_elements:
                st.divider()
                st.markdown("### 🚀 STRATEGIC INNOVATION DEEP-DIVE")
                st.info("The following strategic breakthroughs have been synthesized from the multi-dimensional analysis above.")
                
                # Extract innovations (diamonds) for detailed report-style display
                innovations = [n['data'] for n in final_elements if n['data'].get('shape') == 'diamond']
                
                if innovations:
                    for inv in innovations:
                        g_url = urllib.parse.quote(inv['label'])
                        detailed_desc = inv.get('description', "Detailed strategic analysis is available in the integrated report above.")
                        
                        # High-End Report Style Card
                        st.markdown(f"""
                        <div style="background-color: #ffffff; border-left: 6px solid #fd7e14; padding: 25px; border-radius: 15px; box-shadow: 0 6px 15px rgba(0,0,0,0.1); border: 1px solid #eee; margin-bottom: 25px;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                <span style="background-color: #fff4ed; color: #fd7e14; padding: 5px 12px; border-radius: 20px; font-size: 0.75em; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; border: 1px solid #fd7e14;">Strategic Breakthrough</span>
                                <a href="https://www.google.com/search?q={g_url}" target="_blank" style="text-decoration: none; color: #457b9d; font-size: 0.85em; font-weight: 600;">Technical Search ↗</a>
                            </div>
                            <h2 style="margin: 0 0 15px 0; color: #1d3557; font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">{inv['label']}</h2>
                            <div style="color: #333; font-size: 1.05em; line-height: 1.7; border-top: 1px solid #f0f0f0; padding-top: 15px;">
                                {detailed_desc}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.warning("No specific 'Diamond' innovations were found. Review the structural graph for implicit breakthroughs.")

                # 5d. MINIMALIST SYSTEM LEGEND (FINAL ARCHITECTURE)
                st.markdown("""
                <div style="font-size: 0.78em; color: #444; background: #ffffff; padding: 15px 25px; border-radius: 15px; border: 1px solid #e9ecef; margin-top: 30px; box-shadow: 0 4px 12px rgba(0,0,0,0.03);">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
                        <div>
                            <b style="color: #1d3557; text-transform: uppercase; letter-spacing: 1px;">Nodes (Geometry):</b><br>
                            ⭐ Goal | ⬢ Domain | 💠 Innovation | △ Process | ▭ Data | ⬣ Rule | ⭔ Bio
                        </div>
                        <div style="height: 30px; width: 1px; background: #dee2e6; display: block;"></div>
                        <div>
                            <b style="color: #1d3557; text-transform: uppercase; letter-spacing: 1px;">UML & Logic Connectors:</b><br>
                            <span style="color:#e63946;">⬤ Structural (UML)</span> | 
                            <span style="color:#000000;">⬤ Specialization (Deduction)</span> | 
                            <span style="color:#1d3557;">⬤ Containment (Cage)</span>
                        </div>
                        <div style="height: 30px; width: 1px; background: #dee2e6; display: block;"></div>
                        <div>
                            <b style="color: #1d3557; text-transform: uppercase; letter-spacing: 1px;">Semantic Layers:</b><br>
                            <span style="color:#1d3557;">⬤ Hierarchical (ISO)</span> | 
                            <span style="color:#7b2cb1;">⬤ Associative</span> | 
                            <span style="color:#2a9d8f;">⬤ Related</span> | 
                            <span style="color:#f1c40f;">⬤ Equivalence</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # 5e. FINAL GRAPH RENDERING (Z DINAMIČNO PERSPEKTIVO)
                st.subheader(f"🕸️ HYBRID SEMANTIC SYSTEM MAP ({graph_perspective.upper()} VIEW)")
                render_cytoscape_network(
                    final_elements, 
                    layout_type=graph_perspective, 
                    container_id=f"cy_{int(time.time())}"
                )

                # --- NOVO: SHRANJEVANJE ZA GALERIJO (DODANO NA KONEC POROČILA) ---
                st.session_state.final_graph_elements = final_elements
                st.session_state.report_ready = True

        except Exception as e:
            st.error(f"❌ Pipeline Failure: {str(e)}")
			
# =============================================================================
# 6. MULTI-PERSPECTIVE GALLERY (SEQUENTIAL EXPORT)
# =============================================================================

if st.session_state.get('report_ready') and 'final_graph_elements' in st.session_state:
    st.divider()
    st.markdown('<h2 style="color: #1d3557; text-align: center;">🖼️ MULTI-PERSPECTIVE GRAPH GALLERY</h2>', unsafe_allow_html=True)
    st.info("💡 **NAVODILO ZA ZAPOREDNO SHRANJEVANJE:** Spodaj so zavihki z različnimi vizualnimi perspektivami istega znanja. Odprite posamezen zavihek in kliknite gumb **EXPORT PNG**, da shranite vseh 5 verzij na svoj disk.")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🌿 ORGANIC", "🌲 HIERARCHICAL", "⭕ CIRCULAR", "🎯 CONCENTRIC", "🔲 GRID"
    ])

    with tab1:
        st.markdown("**Organic View:** Najboljše za odkrivanje naravnih tematskih sklopov.")
        render_cytoscape_network(st.session_state.final_graph_elements, layout_type="organic", container_id="gal_organic")
    
    with tab2:
        st.markdown("**Hierarchical View:** Logično drevo od splošnega k specifičnemu.")
        render_cytoscape_network(st.session_state.final_graph_elements, layout_type="hierarchical", container_id="gal_hierarchical")
        
    with tab3:
        st.markdown("**Circular View:** Fokus na relacijah in krožni soodvisnosti.")
        render_cytoscape_network(st.session_state.final_graph_elements, layout_type="circular", container_id="gal_circular")
        
    with tab4:
        st.markdown("**Concentric View:** Razporeditev po sistemski pomembnosti (Jedro).")
        render_cytoscape_network(st.session_state.final_graph_elements, layout_type="concentric", container_id="gal_concentric")

    with tab5:
        st.markdown("**Grid View:** Pregledna poravnava vseh prvin.")
        render_cytoscape_network(st.session_state.final_graph_elements, layout_type="grid", container_id="gal_grid")

# =============================================================================
# 7. FOOTER
# =============================================================================
st.divider()
st.caption(f"SIS Universal Knowledge Synthesizer | {VERSION_CODE} | {SYSTEM_DATE}")
