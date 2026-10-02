import streamlit as st
import json
import base64
import requests
import urllib.parse
import re
import time
from datetime import datetime
from google import genai
from google.genai import types
import streamlit.components.v1 as components

# =============================================================================
# 0. GLOBAL CONFIGURATION & SESSION DATE (FEBRUARY 24, 2026)
# =============================================================================
SYSTEM_DATE = datetime.now().strftime("%B %d, %Y")
VERSION_CODE = "v23.0.0-ULTRA-SYNERGY-GOOGLE-GEMINI-ONLY-LEAN-MODULAR"

# =============================================================================
# INITIALIZATION FIX: Preprečuje AttributeError pri zagonu in resetiranju
# =============================================================================
if 'show_user_guide' not in st.session_state:
    st.session_state.show_user_guide = False

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

def render_cytoscape_network(elements, layout_type="organic", container_id="cy_canvas", modular=False):
    """
    ULTRA-SYNERGY Multi-Perspective Hierarhografski motor.
    Vključuje: ISO 25964 Thesaurus, UML 2.5 Standard, Petrič HA Logiko, Logic Gates in EX fuzijo.
    GEOMETRIJSKA TAKSONOMIJA: Zvezde, Heksagoni, Diamanti, Oktogoni, Trikotniki, Elipse, Pravokotniki.
    NOVO (v23): Modularni prikaz (compound/module škatle po barvah vozlišč).
    """

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

    # --- NOVO (v23): Stili za modularne (compound) vozlišče-škatle ---
    module_style_block = """
                    {
                        selector: 'node[module_box = "true"]',
                        style: {
                            'shape': 'roundrectangle',
                            'background-color': 'data(color)',
                            'background-opacity': 0.12,
                            'border-width': 3,
                            'border-style': 'dashed',
                            'border-color': 'data(color)',
                            'label': 'data(label)',
                            'color': '#1d3557',
                            'font-size': '15px',
                            'font-weight': '900',
                            'text-valign': 'top',
                            'text-halign': 'center',
                            'text-transform': 'uppercase',
                            'padding': '28px',
                            'font-family': 'sans-serif'
                        }
                    },""" if modular else ""

    cyto_html = f"""
    <div style="position: relative; width: 100%;">
        <div style="position: absolute; top: 15px; right: 15px; z-index: 1000; display: flex; gap: 6px;">
            <button id="zoomin_btn_{container_id}" style="padding: 10px 15px; background: #1d3557; color: white; border: none; border-radius: 8px; cursor: pointer; font-family: sans-serif; font-size: 12px; font-weight: 800; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">➕ ZOOM IN</button>
            <button id="zoomout_btn_{container_id}" style="padding: 10px 15px; background: #1d3557; color: white; border: none; border-radius: 8px; cursor: pointer; font-family: sans-serif; font-size: 12px; font-weight: 800; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">➖ ZOOM OUT</button>
            <button id="fit_btn_{container_id}" style="padding: 10px 15px; background: #457b9d; color: white; border: none; border-radius: 8px; cursor: pointer; font-family: sans-serif; font-size: 12px; font-weight: 800; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">🎯 FIT</button>
            <button id="save_btn_{container_id}" style="padding: 10px 15px; background: #2a9d8f; color: white; border: none; border-radius: 8px; cursor: pointer; font-family: sans-serif; font-size: 12px; font-weight: 800; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">💾 PNG</button>
        </div>
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
                    {module_style_block}
                    
                    /* --- 1. ISO 25964 THESAURUS LOGIC --- */
                    {{ selector: 'edge[rel_type="TT"]', style: {{ 'width': 8, 'line-color': '#1d3557', 'target-arrow-shape': 'triangle', 'target-arrow-scale': 1.6 }} }},
                    {{ selector: 'edge[rel_type="BT"]', style: {{ 'width': 5, 'line-color': '#1d3557', 'target-arrow-shape': 'triangle' }} }},
                    {{ selector: 'edge[rel_type="NT"]', style: {{ 'width': 4, 'line-color': '#1d3557', 'target-arrow-shape': 'vee' }} }},
                    {{ selector: 'edge[rel_type="IN"]', style: {{ 'width': 3, 'line-color': '#0077b6', 'line-style': 'dotted', 'target-arrow-shape': 'triangle', 'target-arrow-fill': 'filled' }} }},
                    {{ selector: 'edge[rel_type="RT"]', style: {{ 'width': 2, 'line-color': '#2a9d8f', 'line-style': 'dotted', 'target-arrow-shape': 'none' }} }},
                    {{ selector: 'edge[rel_type="AS"]', style: {{ 'width': 3, 'line-color': '#7b2cb1', 'line-style': 'dashed', 'target-arrow-shape': 'vee' }} }},
                    {{ selector: 'edge[rel_type="EQ"]', style: {{ 'width': 6, 'line-color': '#f1c40f', 'line-style': 'double', 'target-arrow-shape': 'none' }} }},

                    /* --- 2. UML 2.5 STRUCTURAL LOGIC --- */
                    {{ selector: 'edge[rel_type="Generalization"]', style: {{ 'width': 4, 'line-color': '#1d3557', 'target-arrow-shape': 'triangle', 'target-arrow-fill': 'hollow' }} }},
                    {{ selector: 'edge[rel_type="Specialization"]', style: {{ 'width': 4, 'line-style': 'dashed', 'line-color': '#000', 'target-arrow-shape': 'triangle', 'target-arrow-fill': 'filled' }} }},
                    {{ selector: 'edge[rel_type="Realization"]', style: {{ 'width': 2, 'line-style': 'dashed', 'line-color': '#1d3557', 'target-arrow-shape': 'triangle', 'target-arrow-fill': 'hollow' }} }},
                    {{ selector: 'edge[rel_type="Composition"]', style: {{ 'width': 6, 'source-arrow-shape': 'diamond', 'source-arrow-fill': 'filled', 'source-arrow-color': '#1d3557', 'target-arrow-shape': 'none' }} }},
                    {{ selector: 'edge[rel_type="Aggregation"]', style: {{ 'width': 4, 'source-arrow-shape': 'diamond', 'source-arrow-fill': 'hollow', 'source-arrow-color': '#1d3557', 'target-arrow-shape': 'none' }} }},
                    {{ selector: 'edge[rel_type="Dependency"]', style: {{ 'width': 3, 'line-style': 'dashed', 'line-color': '#457b9d', 'target-arrow-shape': 'vee' }} }},
                    {{ selector: 'edge[rel_type="Conflict"]', style: {{ 'width': 8, 'line-color': '#b91d1d', 'line-style': 'solid', 'target-arrow-shape': 'triangle-cross', 'source-arrow-shape': 'triangle-cross', 'target-arrow-color': '#b91d1d', 'source-arrow-color': '#b91d1d' }} }},
                    {{ selector: 'edge[rel_type="Containment"]', style: {{ 'width': 6, 'line-color': '#1d3557', 'target-arrow-shape': 'circle', 'target-arrow-fill': 'hollow', 'target-arrow-color': '#1d3557' }} }},

                    /* --- 3. PETRIČ HIERARCHICAL-ASSOCIATIVE (HA) --- */
                    {{ selector: 'edge[rel_type="HA"]', style: {{ 'width': 6, 'line-color': '#7b2cb1', 'line-style': 'dashed', 'target-arrow-shape': 'triangle-tee', 'source-arrow-shape': 'circle', 'source-arrow-fill': 'hollow', 'arrow-scale': 1.2 }} }},
                    
                    /* --- 4. LOGIC GATES (DECISION LOGIC) --- */
                    {{ selector: 'edge[rel_type="AND"]', style: {{ 'width': 6, 'line-color': '#00FF00', 'target-arrow-color': '#00FF00', 'target-arrow-shape': 'triangle' }} }},
                    {{ selector: 'edge[rel_type="OR"]', style: {{ 'width': 4, 'line-color': '#00BFFF', 'line-style': 'dashed', 'target-arrow-color': '#00BFFF', 'target-arrow-shape': 'vee' }} }},
                    {{ selector: 'edge[rel_type="XOR"]', style: {{ 'width': 5, 'line-color': '#FF8C00', 'line-style': 'double', 'target-arrow-color': '#FF8C00', 'target-arrow-shape': 'diamond' }} }},
                    {{ selector: 'edge[rel_type="NOT"]', style: {{ 'width': 5, 'line-color': '#FF0000', 'line-style': 'dashed', 'target-arrow-color': '#FF0000', 'target-arrow-shape': 'tee' }} }},
                    {{ selector: 'edge[rel_type="IF-THEN"]', style: {{ 'width': 5, 'line-color': '#FFD700', 'target-arrow-color': '#FFD700', 'target-arrow-shape': 'triangle', 'arrow-scale': 1.5 }} }},

                    /* --- 5. MATHEMATICAL & DYNAMICAL CAUSALITY (9.9+ RATING) --- */
                    {{
                        selector: 'edge[rel_type="Causes(+)"]',
                        style: {{
                            'width': 5,
                            'line-color': '#02c39a',
                            'target-arrow-shape': 'triangle',
                            'target-arrow-color': '#02c39a',
                            'line-style': 'solid'
                        }}
                    }},
                    {{
                        selector: 'edge[rel_type="Inhibits(-)"]',
                        style: {{
                            'width': 5,
                            'line-color': '#e63946',
                            'target-arrow-shape': 'tee',
                            'target-arrow-color': '#e63946',
                            'line-style': 'solid'
                        }}
                    }},
                    {{
                        selector: 'edge[rel_type^="Triggers"]',
                        style: {{
                            'width': 6,
                            'line-color': '#ffb703',
                            'line-style': 'dashed',
                            'target-arrow-shape': 'triangle-tee',
                            'target-arrow-color': '#ffb703'
                        }}
                    }},

                    /* --- GEOMETRIC TAXONOMY (Shapes & Specialized Sizes) --- */
                    {{ selector: 'node[shape="star"]', style: {{ 'width': 140, 'height': 140, 'border-width': 6, 'border-color': '#FFD700', 'font-size': '16px' }} }},
                    {{ selector: 'node[shape="hexagon"]', style: {{ 'width': 100, 'height': 100, 'border-width': 4, 'border-color': '#1d3557' }} }},
                    {{ selector: 'node[shape="diamond"]', style: {{ 'width': 115, 'height': 115, 'border-width': 5, 'border-color': '#fd7e14' }} }},
                    {{ selector: 'node[shape="octagon"]', style: {{ 'width': 105, 'height': 105, 'border-width': 4, 'border-color': '#dc3545' }} }},
                    {{ selector: 'node[shape="triangle"]', style: {{ 'width': 90, 'height': 90, 'border-width': 3, 'border-color': '#28a745' }} }},
                    {{ selector: 'node[shape="ellipse"]', style: {{ 'width': 95, 'height': 95, 'border-width': 3, 'border-color': '#17a2b8' }} }},
                    {{ selector: 'node[shape="rectangle"]', style: {{ 'width': 85, 'height': 85, 'border-width': 2, 'border-color': '#6c757d' }} }}
                ],
                layout: {selected_layout}
            }});

            document.getElementById('zoomin_btn_{container_id}').addEventListener('click', function() {{
                cy.zoom({{level: cy.zoom() * 1.3, renderedPosition: {{ x: cy.width() / 2, y: cy.height() / 2 }}}});
            }});
            document.getElementById('zoomout_btn_{container_id}').addEventListener('click', function() {{
                cy.zoom({{level: cy.zoom() / 1.3, renderedPosition: {{ x: cy.width() / 2, y: cy.height() / 2 }}}});
            }});
            document.getElementById('fit_btn_{container_id}').addEventListener('click', function() {{
                cy.fit(undefined, 40);
            }});
            document.getElementById('save_btn_{container_id}').addEventListener('click', function() {{
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
    """Pridobi bibliografijo preko ORCID API-ja."""
    if not author_input: return ""
    author_list = [a.strip() for a in author_input.split(",")]
    comprehensive_biblio = ""
    headers = {"Accept": "application/json"}
    for auth in author_list:
        try:
            # FIX: URL-encode the author name so non-ASCII characters (č, š, ž, ...)
            # don't break the request ('ascii' codec can't encode character error).
            s_res = requests.get(f"https://pub.orcid.org/v3.0/search/?q={urllib.parse.quote(auth)}", headers=headers, timeout=6).json()
            if s_res.get('result'):
                orcid_id = s_res['result'][0]['orcid-identifier']['path']
                r_res = requests.get(f"https://pub.orcid.org/v3.0/{orcid_id}/record", headers=headers, timeout=6).json()
                works = r_res.get('activities-summary', {}).get('works', {}).get('group', [])
                comprehensive_biblio += f"#### 🆔 ORCID: {auth.upper()} ({orcid_id})\n"
                for work in works[:12]:
                    summary = work.get('work-summary', [{}])[0]
                    title = summary.get('title', {}).get('title', {}).get('value', 'Unknown Title')
                    pub_date = summary.get('publication-date')
                    year = pub_date.get('year', {}).get('value', 'n.d.') if pub_date else 'n.d.'
                    comprehensive_biblio += f"- **{year}**: {title}\n"
                comprehensive_biblio += "\n---\n"
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
        "Post-Structuralism": "Critique of structuralism, emphasizing the instability of meaning and systems.",
        # --- NOVO (v23): dodatne pomembne znanstvene paradigme ---
        "Instrumentalism": "Scientific theories are tools for prediction and control, not literal descriptions of reality.",
        "Operationalism": "Scientific concepts are defined by the concrete operations used to measure them.",
        "Bayesianism": "Rational belief updating through probability revision in the light of new evidence.",
        "Materialism": "Everything that exists is ultimately grounded in physical matter and its interactions.",
        "Idealism": "Reality is fundamentally mental or conceptually constructed.",
        "Emergentism": "Higher-level phenomena arise with genuinely novel properties not reducible to their parts.",
        "Determinism": "All events are fully determined by prior states of the system.",
        "Probabilism": "Indeterminacy and stochastic processes are intrinsic features of nature, not artifacts of ignorance.",
        "Functionalism": "Mental and social states are defined by their functional roles, not by their substrate.",
        "Structural Realism": "Science captures the relational structure of the world, not its intrinsic nature.",
        "Conventionalism": "Scientific principles are partly founded on agreed conventions chosen for convenience.",
        "Naturalism": "Inquiry should be grounded in the methods of natural science, without supernatural explanations.",
        "Anti-Foundationalism": "There is no certain, self-justifying basis of knowledge; justification is holistic and fallible.",
        "Postmodernism": "Skepticism toward grand narratives and universal claims of objective truth.",
        "Complexity Paradigm": "Reality is best modeled as complex adaptive systems with non-linear dynamics and emergence.",
        "Interdisciplinarity": "Knowledge production through the integration and fusion of multiple disciplinary perspectives."
    },
    "Structural models": {
        "Concepts": "Abstract constructs and conceptual building blocks.",
        "Causal Connections": "Chains of cause and effect mapping systemic causality.",
        "Principles & Relations": "Fundamental laws and the inter-relations between entities.",
        "Episodes & Sequences": "Temporal flow, historical timelines, and event ordering.",
        "Facts & Characteristics": "Raw data properties, attributes, and static descriptions.",
        "Generalizations": "Broad frameworks and high-level theoretical models.",
        "Glossary": "Precise definitions and terminological clarity."
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
        },
        # --- NOVO (v23): dodatna pomembna znanstvena področja ---
        "Astronomy": {
            "cat": "Natural",
            "methods": ["Photometry", "Spectroscopy", "Astrometry", "Radio Interferometry"],
            "tools": ["Telescopes (Optical/Radio)", "Space Probes", "CCD Imaging", "Planetarium SW"],
            "facets": ["Astrophysics", "Cosmology", "Planetary Science", "Stellar Evolution"]
        },
        "Statistics": {
            "cat": "Formal",
            "methods": ["Hypothesis Testing", "Bayesian Inference", "Regression Modeling", "Design of Experiments"],
            "tools": ["R", "SPSS", "JASP", "SAS"],
            "facets": ["Biostatistics", "Multivariate Analysis", "Time-Series Analysis", "Non-parametric Methods"]
        },
        "Data Science": {
            "cat": "Formal/Interdisciplinary",
            "methods": ["Machine Learning", "Data Mining", "Feature Engineering", "Predictive Modeling"],
            "tools": ["Python (scikit-learn)", "TensorFlow", "Jupyter", "Spark"],
            "facets": ["Big Data Analytics", "Natural Language Processing", "Computer Vision", "Data Engineering"]
        },
        "Environmental Science": {
            "cat": "Natural/Interdisciplinary",
            "methods": ["Environmental Impact Assessment", "Life-Cycle Analysis", "Pollution Monitoring", "Ecosystem Modeling"],
            "tools": ["GIS", "Environmental Sensors", "Satellite Imagery", "LIDAR"],
            "facets": ["Sustainability Science", "Pollution Control", "Resource Management", "Climate Adaptation"]
        },
        "Pharmacy": {
            "cat": "Applied/Natural",
            "methods": ["Pharmacokinetics", "Drug Design", "Formulation Science", "Clinical Pharmacology"],
            "tools": ["HPLC", "Dissolution Testers", "Molecular Docking SW", "Tablet Presses"],
            "facets": ["Pharmacology", "Pharmaceutical Chemistry", "Toxicology", "Pharmacogenomics"]
        },
        "Veterinary Medicine": {
            "cat": "Applied/Natural",
            "methods": ["Clinical Examination", "Herd Health Management", "Diagnostic Imaging", "Epidemiological Surveillance"],
            "tools": ["Veterinary Ultrasound", "Hematology Analyzers", "Digital Radiography"],
            "facets": ["Companion Animal Medicine", "Food Safety", "Zoonotic Disease Control", "Veterinary Pathology"]
        },
        "Agricultural Science": {
            "cat": "Applied/Natural",
            "methods": ["Field Trials", "Crop Modeling", "Soil Analysis", "Selective Breeding"],
            "tools": ["Greenhouse Facilities", "Soil Sensors", "Precision Agriculture Drones"],
            "facets": ["Agronomy", "Horticulture", "Animal Science", "Agroecology"]
        },
        "Education Sciences": {
            "cat": "Social/Applied",
            "methods": ["Pedagogical Experiment", "Didactic Analysis", "Action Research", "Assessment Design"],
            "tools": ["Learning Management Systems", "Assessment Rubrics", "Educational Analytics"],
            "facets": ["Curriculum Theory", "Educational Psychology", "Instructional Design", "Adult Education"]
        },
        "Management Science": {
            "cat": "Applied/Social",
            "methods": ["Operations Research", "Scenario Planning", "Balanced Scorecard", "Case Study Analysis"],
            "tools": ["ERP Systems", "Project Management SW", "BI Dashboards"],
            "facets": ["Strategic Management", "Organizational Behavior", "Operations Management", "Innovation Management"]
        },
        "Logic": {
            "cat": "Formal",
            "methods": ["Formal Deduction", "Model Theory", "Proof Theory", "Modal Analysis"],
            "tools": ["Proof Assistants (Coq/Lean)", "Truth Tables", "Theorem Provers"],
            "facets": ["Classical Logic", "Modal Logic", "Non-classical Logic", "Computability Theory"]
        },
        "Communication Science": {
            "cat": "Social",
            "methods": ["Content Analysis", "Discourse Analysis", "Media Effects Research", "Audience Studies"],
            "tools": ["Media Monitoring Tools", "Survey Platforms", "Social Network Analysis SW"],
            "facets": ["Media Studies", "Rhetoric", "Digital Communication", "Journalism Studies"]
        },
        "Demography": {
            "cat": "Social",
            "methods": ["Census Analysis", "Cohort Analysis", "Migration Modeling", "Fertility Analysis"],
            "tools": ["Population Registries", "Statistical Projections", "GIS"],
            "facets": ["Fertility & Mortality", "Migration Studies", "Population Aging", "Population Projections"]
        },
        "Kinesiology": {
            "cat": "Applied/Natural",
            "methods": ["Motion Capture Analysis", "Exercise Testing", "Biomechanical Modeling", "Training Intervention Studies"],
            "tools": ["Force Plates", "EMG", "Ergospirometry", "Motion Capture Systems"],
            "facets": ["Sports Medicine", "Exercise Physiology", "Motor Control", "Sports Psychology"]
        },
        "Information Science": {
            "cat": "Formal/Applied",
            "methods": ["Information Retrieval Modeling", "Knowledge Graph Construction", "Ontology Engineering", "Bibliometrics"],
            "tools": ["Search Engines", "Knowledge Graph DBs", "Citation Indexes", "RDF/OWL Tooling"],
            "facets": ["Knowledge Organization", "Human-Information Interaction", "Informetrics", "Semantic Web"]
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

# --- NOVO (v23): celoten spekter povezav za izbiro uporabnika ---
EDGE_REL_TYPES = [
    "TT", "BT", "NT", "IN", "RT", "AS", "EQ", "HA",
    "AND", "OR", "XOR", "NOT", "IF-THEN",
    "Generalization", "Specialization", "Realization",
    "Composition", "Aggregation", "Dependency", "Conflict", "Containment",
    "Causes(+)", "Inhibits(-)", "Triggers(θ)"
]
# =============================================================================
# 4. KONČNI POPRAVLJEN SIDEBAR (Z UNIKATNIMI KLJUČI) — GOOGLE GEMINI ONLY
# =============================================================================
with st.sidebar:
    # 1. Original 3D Relief Logo
    st.markdown(f'<div class="sidebar-logo-container"><img src="data:image/svg+xml;base64,{get_svg_base64(SVG_3D_RELIEF)}" width="220"></div>', unsafe_allow_html=True)

    # 2. Date Badge
    st.markdown(f'<div class="date-badge">{SYSTEM_DATE.upper()}</div>', unsafe_allow_html=True)

    st.header("⚙️ SYSTEM CONTROL")

    # 3. GOOGLE GEMINI SYSTEM CONTROL (nadomestil Cerebras)
    st.header("⚙️ GOOGLE GEMINI SYSTEM CONTROL")
    google_api_key = st.text_input(
        "Google Gemini API Key:",
        type="password",
        key="side_google_gemini_v2026",
        help="Google AI Studio / Gemini API key."
    )

    # Google-only language-model catalog (enaki modeli kot v prejšnji različici).
    GOOGLE_MODELS = {
        # Current Gemini 3.x
        "Gemini 3.8 Flash — latest": "gemini-3.8-flash",
        "Gemini 3.7 Flash — advanced": "gemini-3.7-flash",
        "Gemini 3.6 Flash": "gemini-3.6-flash",
        "Gemini 3.5 Flash": "gemini-3.5-flash",
        "Gemini 3.5 Flash-Lite — free/cost-efficient": "gemini-3.5-flash-lite",
        "Gemini 3.1 Flash-Lite — free/cost-efficient": "gemini-3.1-flash-lite",
        "Gemini 3.1 Pro Preview": "gemini-3.1-pro-preview",
        "Gemini 3 Flash Preview": "gemini-3-flash-preview",
        # Gemini 2.5 family
        "Gemini 2.5 Pro": "gemini-2.5-pro",
        "Gemini 2.5 Flash": "gemini-2.5-flash",
        "Gemini 2.5 Flash-Lite": "gemini-2.5-flash-lite",
        # Gemma 4
        "Gemma 4 31B IT — free": "gemma-4-31b-it",
        "Gemma 4 26B A4B IT — free": "gemma-4-26b-a4b-it",
    }

    st.subheader("🤖 Sequential Google Model Selection")

    # Thinking level (kakovost > stroški; "low" znižuje kakovost grafov)
    thinking_level = st.selectbox(
        "🧠 Gemini 3.x Thinking Level:",
        ["High", "Medium", "Low", "Default (API)"],
        index=0,
        help="Stopnja notranjega razmišljanja za Gemini 3.x modele. 'High' daje "
             "najboljše poročila in grafe (9,6+).",
        key="side_thinking_level_v2026"
    )

    # Izbira za Phase 1 (Foundation)
    p1_model_label = st.selectbox(
        "Phase 1 Model (Structure):", 
        list(GOOGLE_MODELS.keys()), 
        index=3, 
        help="Priporočeno: Gemini 3.5 Flash za kompleksno IMA sintezo."
    )
    p1_model = GOOGLE_MODELS[p1_model_label]

    # Izbira za Phase 2 (Innovation)
    p2_model_label = st.selectbox(
        "Phase 2 Model (Innovation):", 
        list(GOOGLE_MODELS.keys()), 
        index=1, 
        help="Priporočeno: Gemini 3.7/3.8 Flash za MA inovativne preboje."
    )
    p2_model = GOOGLE_MODELS[p2_model_label]

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

    # --- NOVO (v23): DRSLNIK ZA ŠTEVILO VOZLIŠČ GRAFA ---
    st.subheader("🎚️ GRAPH SIZE CONTROL")
    target_node_count = st.slider(
        "Target Number of Nodes:",
        min_value=12,
        max_value=150,
        value=40,
        step=2,
        help="Ciljno število vozlišč, ki jih mora graf vsebovati (določimo ga PRED poizvedbama).",
        key="side_node_count_slider_v23"
    )
    target_edge_factor = st.slider(
        "Edge Density (edges per node):",
        min_value=1.0,
        max_value=4.0,
        value=1.5,
        step=0.1,
        help="Kakovost povezanosti: več = gostejše, bolj povezano omrežje.",
        key="side_edge_density_slider_v23"
    )

    # --- NOVO (v23): IZBIRA TIPOV POVEZAV ---
    st.subheader("🔗 EDGE TYPE CONTROL")
    selected_edge_types = st.multiselect(
        "Included Relation Types (empty = all):",
        options=EDGE_REL_TYPES,
        default=[],
        help="Izberite, katere semantične povezave naj graf vključuje. Prazno = vse.",
        key="side_edge_types_multiselect_v23"
    )

    # --- NOVO (v23): MODULARNI PRIKAZ GRAFA ---
    st.subheader("🧩 MODULAR VIEW")
    modular_view = st.checkbox(
        "Enable Modular Graph Display (module boxes)",
        value=False,
        help="Vozlišča se združijo v barvne modularne škatle (gl. simbolično shemo Ga2): "
             "Environmental Foundation, Biochemical Hierarchy, ATE, Systemic Core, Vision ipd.",
        key="side_modular_view_v23"
    )
    module_grouping = st.selectbox(
        "Group Modules By:",
        options=["Node Color (semantic domains)", "Node Shape (logical level)", "Color + Shape (fine-grained)"],
        index=0,
        help="Barva = semantična domena (kot škatle v shemi) | Oblika = logična raven | Oboje = najfinejša delitev.",
        key="side_module_grouping_v23"
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
    1. **Key Input**: Enter your Google Gemini API key and select Google models for Phase 1 and Phase 2.
    2. **Research Foundation (Step 1)**: Google Gemini performs structural synthesis foundation using Integrated Metamodel Architecture (IMA).
    3. **Innovation Prompt (Step 2)**: Google Gemini takes the Phase 1 foundation and generates radical 'Useful Innovative Ideas' using Mental Approaches (MA) logic.
    4. **Visualization**: The interactive 18D graph maps structural facts against generative ideas. Node count, edge types and modular view are set in the sidebar BEFORE running the two inquiries.
    """)

# REFERENCE ARCHITECTURE BOXES
col_ref1, col_ref2 = st.columns(2)
with col_ref1:
    st.markdown("""<div class="metamodel-box"><b>🏛️ Phase 1: Google Gemini (IMA Architecture)</b><br>Structural reasoning building the factual foundation. Focus: Identity, Mission, Problem. </div>""", unsafe_allow_html=True)
with col_ref2:
    st.markdown("""<div class="mental-approach-box"><b>🧠 Phase 2: Google Gemini (MA Architecture)</b><br>Cognitive transformation generating innovative solutions. Focus: Dialectics, Perspective, Induction.</div>""", unsafe_allow_html=True)

st.markdown("### 🛠️ CONFIGURE SYNERGY PIPELINE")

# Entry Rows
r1c1, r1c2, r1c3 = st.columns([1.5, 2, 1])
with r1c1: target_authors = st.text_input("👤 Authors for ORCID Analysis:", placeholder="Karl Petrič, Samo Kralj, Teodor Petrič")
with r1c2: sel_sciences = st.multiselect("2. Select Science Fields:", sorted(list(KNOWLEDGE_BASE["Science fields"].keys())), default=["Physics", "Psychology", "Sociology"])
with r1c3: expertise = st.select_slider("3. Expertise Level:", ["Novice", "Intermediate", "Expert"], value="Expert")

r2c1, r2c2, r2c3 = st.columns(3)
with r2c1: sel_paradigms = st.multiselect("4. Scientific Paradigms:", list(KNOWLEDGE_BASE["Scientific paradigms"].keys()), default=["Rationalism", "Holism", "Systems Theory", "Critical Theory"])
with r2c2: sel_models = st.multiselect("5. Structural Models:", list(KNOWLEDGE_BASE["Structural models"].keys()), default=["Concepts"])
with r2c3: goal_context = st.selectbox("6. Strategic Project Goal:", ["Scientific Research", "Problem Solving", "Educational", "Policy Making"])

# --- NOVO (v23): 7. METHODOLOGIES IN 8. TOOLS (se gradita iz izbranih znanstvenih polj) ---
r3c1, r3c2 = st.columns(2)
available_methods = sorted({m for s in sel_sciences for m in KNOWLEDGE_BASE["Science fields"].get(s, {}).get("methods", [])})
available_tools = sorted({t for s in sel_sciences for t in KNOWLEDGE_BASE["Science fields"].get(s, {}).get("tools", [])})
with r3c1:
    sel_methodologies = st.multiselect(
        "7. Methodologies:",
        options=available_methods,
        default=[],
        help="Metodologije, pridobljene iz izbranih znanstvenih polj (točka 2).",
        key="unique_methodologies_multiselect_v23"
    )
with r3c2:
    sel_tools = st.multiselect(
        "8. Tools:",
        options=available_tools,
        default=[],
        help="Orodja in instrumenti, pridobljeni iz izbranih znanstvenih polj (točka 2).",
        key="unique_tools_multiselect_v23"
    )

# ============================================================================= 
# 🧬 INTEGRIRAN NADZOR: INOVACIJSKA STRATEGIJA (OČIŠČENA VERZIJA)
# ============================================================================= 
st.divider()

# --- INNOVATION STRATEGY (Kreativni miselni okvirji) --- 
st.markdown("### 🧬 INNOVATION STRATEGY")
selected_techniques = st.multiselect(
    "Select Strategic Ideation Frameworks (Pick one or more):", 
    options=list(IDEATION_TECHNIQUES.keys()), 
    default=["Six Thinking Hats"],
    help="Izbrani okvirji bodo usmerjali generiranje idej v Phase 2.",
    key="unique_strategy_multiselect_final"
)

if not selected_techniques:
    st.warning("⚠️ Please select at least one technique for Phase 2.")
else:
    # Prikaz opisa aktivnih tehnik
    combined_desc = " | ".join([f"**{t}**: {IDEATION_TECHNIQUES[t]}" for t in selected_techniques])
    st.info(f"**Active Hybrid Strategy:** {combined_desc}")

st.divider()

# ============================================================================= 
# ❓ DUAL INQUIRY INTERFACE (Vnosna polja in podatki)
# ============================================================================= 
col_inq1, col_inq2, col_inq3 = st.columns([2, 2, 1])

with col_inq1:
    user_query = st.text_area(
        "❓ STEP 1: Research Inquiry (for GOOGLE GEMINI):", 
        placeholder="Fact-based Foundational Inquiry...", 
        height=200
    )

with col_inq2:
    idea_query = st.text_area(
        "💡 STEP 2: Innovation Prompt (for GOOGLE GEMINI):", 
        placeholder="Targets for innovative idea production...", 
        height=200
    )

with col_inq3:
    uploaded_file = st.file_uploader("📂 ATTACH DATA (.txt only):", type=['txt'], key="final_file_uploader_v2")
    file_content = "" 
    if uploaded_file is not None:
        try:
            file_content = uploaded_file.read().decode("utf-8")
            st.success(f"📎 {uploaded_file.name} uploaded!")
            with st.expander("File Preview"):
                st.text(file_content[:300] + "...")
        except Exception as e:
            st.error(f"Error reading file: {e}")

# ============================================================================= 
# 4.9 NOVO (v23): GRADNJA MODULARNIH ELEMENTOV (compound škatle po shemi Ga2)
# ============================================================================= 

def build_modular_elements(elements, grouping="color"):
    """
    Združi vozlišča v modularne škatle (Cytoscape compound/parent vozlišča),
    simbolično po shemi Ga2: vsak modul je barvna škatla z oznako in vozlišči znotraj.
    grouping: 'color' (semantične domene), 'shape' (logične ravni) ali 'both'.
    """
    nodes = [el for el in elements if "label" in el.get("data", {}) and el["data"].get("shape") not in (None, "", "roundrectangle", "module")]
    edges = [el for el in elements if "source" in el.get("data", {})]

    def group_key(d):
        if grouping == "shape":
            return f"shape:{d.get('shape', 'rectangle')}"
        elif grouping == "both":
            return f"{d.get('color', '#ADB5BD')}|{d.get('shape', 'rectangle')}"
        return f"color:{d.get('color', '#ADB5BD')}"

    # Imena modulom glede na prevladujočo obliko (kot v shemi: cilji, domene, inovacije ...)
    SHAPE_MODULE_NAMES = {
        "star": "Strategic Goals Module",
        "hexagon": "Science Domain Module",
        "diamond": "Innovation Module",
        "triangle": "Process Module",
        "octagon": "Ethical Constraints Module",
        "ellipse": "Human Factors Module",
        "rectangle": "Facts & Data Module"
    }

    groups = {}
    for el in nodes:
        k = group_key(el["data"])
        groups.setdefault(k, []).append(el)

    new_elements = []
    group_color = {}
    for gi, (k, members) in enumerate(sorted(groups.items()), start=1):
        g_color = members[0]["data"].get("color", "#ADB5BD")
        shapes = {m["data"].get("shape") for m in members}
        if len(shapes) == 1:
            g_label = SHAPE_MODULE_NAMES.get(next(iter(shapes)), f"Module {gi}")
        else:
            # Mešana skupina: ime po barvni domeni (npr. 'Environmental Foundation')
            g_label = f"Module {gi}"
        if grouping == "shape":
            g_color = "#1d3557"
        mid = f"module_{gi}"
        group_color[k] = mid
        new_elements.append({
            "data": {
                "id": mid,
                "label": g_label,
                "color": g_color,
                "shape": "roundrectangle",
                "module_box": "true"
            }
        })
        for m in members:
            md = dict(m["data"])
            md["parent"] = mid
            new_elements.append({"data": md})

    for e in edges:
        new_elements.append(e)
    return new_elements

# ============================================================================= 
# 5. SYNERGY EXECUTION ENGINE (PURE GOOGLE GEMINI SEQUENTIAL PIPELINE)
# ============================================================================= 

def google_generate(client, model_id, system_prompt, user_content, temperature, max_retries=4, thinking_level="High"):
    """Single Google GenAI gateway. No third-party LLM providers.

    Includes automatic retry with exponential backoff for transient server-side
    errors (e.g. 503 UNAVAILABLE / high demand), which are temporary on Google's
    side and usually succeed on the next attempt.
    """
    if client is None:
        raise RuntimeError("Google Gemini client is not initialized.")

    config_kwargs = {
        "system_instruction": system_prompt,
        "temperature": temperature,
    }
    # Thinking level ni vsiljen na "low" — kakovost ima prednost.
    if model_id.startswith("gemini-3") and thinking_level and thinking_level.startswith(("High", "Medium", "Low")):
        try:
            config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_level=thinking_level.lower())
        except Exception:
            pass

    config = types.GenerateContentConfig(**config_kwargs)

    last_exc = None
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=model_id,
                contents=user_content,
                config=config,
            )
            text_out = getattr(response, "text", None)
            if text_out:
                return text_out
            try:
                return response.candidates[0].content.parts[0].text
            except Exception as exc:
                raise RuntimeError(f"Google returned no usable text response: {exc}") from exc
        except Exception as exc:
            last_exc = exc
            error_str = str(exc)
            is_transient = any(code in error_str for code in ["503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED", "500", "INTERNAL"])
            if is_transient and attempt < max_retries - 1:
                wait_time = (2 ** attempt) + 1  # 2s, 3s, 5s, 9s...
                st.toast(f"⏳ Google API trenutno preobremenjen (poskus {attempt + 1}/{max_retries}). Ponovni poskus čez {wait_time}s...")
                time.sleep(wait_time)
                continue
            raise

    raise RuntimeError(f"Google Gemini API ni na voljo po {max_retries} poskusih: {last_exc}")


if st.button("🚀 EXECUTE MULTI-DIMENSIONAL SEQUENTIAL SYNERGY PIPELINE", use_container_width=True, key="exec_pipeline_v2026"):
    # Preverjamo le Google Gemini ključ (Cerebras je odstranjen)
    if not google_api_key:
        st.error("❌ Google Gemini API key is required to proceed.")
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
                - Applied Methodologies (7): {', '.join(sel_methodologies) if sel_methodologies else 'auto-select from fields'}
                - Applied Tools (8): {', '.join(sel_tools) if sel_tools else 'auto-select from fields'}
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

            # Inicializacija Google Gemini klienta
            google_client = genai.Client(api_key=google_api_key)

            # --- PHASE 1: GOOGLE GEMINI (Foundation - npr. Gemini 3.5 Flash) ---
            with st.spinner(f'PHASE 1: Building Architecture with {p1_model_label}...'):
                groq_synthesis = google_generate(
                    google_client,
                    p1_model,
                    "You are the SIS Lead Hierarchologist. If the user provides specific Paradigms or Models in the 'MANDATORY SYSTEM INSTRUCTION', you MUST prioritize them in your structural analysis.",
                    full_ai_input,
                    temperature=0.4,
                    thinking_level=thinking_level
                )
                st.session_state.groq_synthesis = groq_synthesis

            # --- NOVO (v23): dinamične omejitve velikosti grafa ---
            node_min = max(12, int(target_node_count * 0.9))
            node_max = int(target_node_count * 1.1)
            edge_min = max(18, int(target_node_count * target_edge_factor))
            allowed_rels_str = ", ".join(selected_edge_types) if selected_edge_types else "full spectrum (all codes listed above)"
            edge_restriction_block = f"""
### GRAPH SIZE MANDATE (USER-SET)
- Generate between {node_min} and {node_max} nodes (target: {target_node_count}).
- Generate at least {edge_min} edges (target density: {target_edge_factor} edges per node).
""" + (f"""
### RESTRICTED RELATION TYPES (USER-SET)
- Use ONLY these relation codes: {allowed_rels_str}
- Do NOT emit edges with any other relation type.
""" if selected_edge_types else "")

            # --- 3. PHASE 2: GOOGLE GEMINI (Innovation - npr. Gemini 3.7/3.8 Flash) ---
            with st.spinner(f'PHASE 2: Generating innovations with {p2_model_label}...'):

                # --- STANDARDNI INTERDISCIPLINARNI PROTOKOL (Epiplexity odstranjen) --- 
                protocol_snippet = """
### INTERDISCIPLINARY MAPPING PROTOCOL ###
Focus: High-density interdisciplinary mapping.
Constraint: Maintain clear boundaries between scientific disciplines.
Use 'BT', 'NT', 'RT', or 'AS' relations for cross-domain links.
"""

                # --- IZGRADNJA SISTEMSKEGA NAVODILA ---
                samba_sys_prompt = f"""
You are the SIS Lead Strategic Innovation Architect.

### OPERATIONAL RULES
1. Provide a professional, human-readable STRATEGIC INNOVATION REPORT.
2. DO NOT include JSON code or any semantic-graph-data inside the report text.
3. MANDATORY: After your report is completely finished, provide the graph data as a single block starting EXACTLY with the header: ### SEMANTIC_GRAPH_JSON

{protocol_snippet}

{edge_restriction_block}

### MODULAR STRUCTURE MANDATE
Organize the graph into SEMANTIC MODULES (thematic clusters like 'Environmental Foundation', 
'Systemic Core', 'Vision', thematic domain blocks). Assign each node a 'color' that reflects 
its module (nodes of the same module share the same color) so the visualization can group 
them into module boxes.

### ANTI-REDUNDANCY RULES (STRICT)
- Every innovation in the report must be UNIQUE: no repeated, rephrased, overlapping, or near-duplicate ideas.
- Each innovation must add a genuinely NEW insight, method, or mechanism — never a restatement of a previous point.
- Each node in the graph must appear exactly once (no duplicate labels).

### GEOMETRIC TAXONOMY (Strict Shapes — Use ALL of them)
Assign shapes based on logical level and MAXIMIZE geometric diversity — every shape must be used at least once:
- 'star': Ultimate Goals
- 'hexagon': Science Domains
- 'diamond': Innovations
- 'triangle': Active Processes
- 'octagon': Ethical Constraints
- 'ellipse': Human Factors
- 'rectangle': Specific Facts

### RELATIONSHIP MATRIX (Maximum Semantic Diversity)
Use the FULL semantic spectrum and DIVERSIFY actively — never let one relation type dominate:

A) THESAURUS LOGIC (ISO 25964) — use ALL where semantically valid:
- 'TT' (Top Term), 'BT' (Broader Term), 'NT' (Narrower Term): hierarchical taxonomic chains
- 'RT' (Related Term): lateral associative links between concepts and innovations
- 'AS' (Associative): cooperating innovations / cross-domain partnerships
- 'EQ' (Equivalence): synonyms and concept alignments across fields
- 'IN' (Instance): concrete examples of abstract categories

B) UML 2.5 STRUCTURAL LOGIC — use ALL where semantically valid:
- 'Composition': whole-part links where parts cannot exist without the whole
- 'Aggregation': whole-part links where parts remain independent
- 'Containment': structural nesting (e.g. elements inside the Scientific Cage)
- 'Dependency': innovation grounded in a science field or method
- 'Realization': implementation of a goal or abstract concept
- 'Generalization': abstraction from specific to general
- 'Specialization': derivation from general to specific
- 'Conflict': tension or incompatibility between paradigms/goals

C) ADDITIONAL LOGIC: HA, AND, OR, XOR, NOT, IF-THEN — for hybrid and decision edges.

D) DYNAMICAL CAUSAL & MATHEMATICAL OPERATORS (MANDATORY FOR 9.9+ RATINGS):
If state-space variables, thresholds, or ODEs are discussed:
- 'Causes(+)': Reinforcing causal edge (e.g. Stressors -> Allostatic Load)
- 'Inhibits(-)': Inhibitory or dampening edge (e.g. Executive Reserve -> Impulsive Breach)
- 'Triggers(θ1)': Nonlinear threshold activation edge (Heaviside step trigger)
- 'Flow': Stock-to-Flow dynamic transfer (dX/dt)

### CONNECTIVITY MANDATE (Connectionist Richness — Critical)
The graph must be a DENSELY WOVEN NETWORK, not a collection of loose chains:
- EVERY node MUST have at least 2 edges (in + out combined); ideally 3–5.
- Use AT LEAST 10 DIFFERENT relation types across the graph (thesaurus + UML families combined); do not fall back on one dominant type.
- Actively create LATERAL (RT/AS) edges between innovations, and cross-domain edges (Dependency, HA) between different science fields.
- Close semantic loops: goals (stars) must receive NEG-FEEDBACK style IF-THEN edges back into the system core.
- No isolated islands: every sub-network must connect to the main structure.
- Target edge density: at least {target_edge_factor} edges per node.

### STRICT JSON FORMAT (MANDATORY)
Output EXACTLY this structure (use these field names, nothing else):
{{
  "nodes": [
    {{"id": "n1", "label": "Human-readable Name", "shape": "hexagon", "color": "#1d3557", "description": "One-sentence role of the node."}}
  ],
  "edges": [
    {{"id": "e1", "source": "n1", "target": "n2", "rel_type": "BT"}}
  ]
}}
Rules: 'id' must be unique and referenced by 'source'/'target'; 'label' must be unique; between {node_min} and {node_max} nodes and at least {edge_min} edges; use only the relation codes listed above{'; restrict relations to: ' + allowed_rels_str if selected_edge_types else ''}.
"""
                # IZVEDBA KLICA NA GOOGLE GEMINI API
                innovation_raw = google_generate(
                    google_client,
                    p2_model,
                    samba_sys_prompt,
                    f"PHASE 1 FOUNDATION:\n{groq_synthesis}\n\nUSER GOAL: {idea_query}{file_context_str}",
                    temperature=0.85,
                    thinking_level=thinking_level
                )

            # ============================================================================= 
            # 4. PROCESIRANJE REZULTATOV (ULTRA-RIGID TAXONOMY & AUTO-CORRECTION)
            # ============================================================================= 
            g_data = {"nodes": [], "edges": []}

            # Ločevanje človeškega poročila od JSON podatkov (da koda ne smeti poročila)
            if "### SEMANTIC_GRAPH_JSON" in innovation_raw:
                parts = innovation_raw.split("### SEMANTIC_GRAPH_JSON")
                innovation_text = parts[0]
                json_raw = parts[1]
            else:
                innovation_text = innovation_raw
                json_raw = ""

            # Sestavljanje končnega poročila (P1 + P2) brez JSON kode
            full_report = f"## 📚 Phase 1: Structural Foundation (Google {p1_model_label})\n\n{groq_synthesis}\n\n---\n## 💡 Phase 2: Strategic Innovations (Google {p2_model_label})\n\n{innovation_text}"

            nodes_to_link = []
            final_elements = []

            # --- ROBUSTNO LOČEVANJE JSON OD BESEDILA (več strategij) ---
            def parse_graph_json(raw_text):
                """Modeli JSON včasih ovijejo v fence-e ali doda prozo okrog njega;
                zato poskusimo več strategij ločevanja."""
                candidates = []
                raw_text = (raw_text or "").strip()
                # 1. Odstranimo code-fence ovojnice
                cleaned = re.sub(r'^```(?:json)?\s*', '', raw_text, flags=re.I)
                cleaned = re.sub(r'\s*```\s*$', '', cleaned.strip())
                # 2. Zgrabimo blok od prve '{' do zadnje '}'
                start = cleaned.find('{')
                end = cleaned.rfind('}')
                if start != -1 and end > start:
                    candidates.append(cleaned[start:end + 1])
                # 3. Regex kot zasilna varianta (prvi blok, ki vsebuje 'nodes')
                m = re.search(r'\{[\s\S]*?"nodes"[\s\S]*?\}', cleaned, re.IGNORECASE)
                if m:
                    candidates.append(m.group(0))
                for cand in candidates:
                    try:
                        c = cand.replace('\r', '').replace('\t', ' ')
                        c = re.sub(r',\s*([}\]])', r'\1', c)  # trailing vejice
                        data = json.loads(c)
                        if isinstance(data, dict) and "nodes" in data:
                            return data
                    except Exception:
                        continue
                return None

            g_data = parse_graph_json(json_raw) or parse_graph_json(innovation_raw) or {"nodes": [], "edges": []}
            if not g_data.get("nodes"):
                st.warning("Note: Graph structure could not be parsed — check the SEMANTIC_GRAPH_JSON block.")

            # --- PROCESIRANJE VOZLIŠČ Z IZRAZITO GEOMETRIJSKO TAKSONOMIJO ---
            if g_data.get("nodes"):
                # --- ROBUSTNO BRANJE POLJ: AI uporablja različna imena (label/name, id/node_id, shape/type) ---
                def first_val(d, keys, default=None):
                    for k in keys:
                        if isinstance(d, dict) and d.get(k) not in (None, ""):
                            return d[k]
                    return default

                # Vsi možni zapisi (id-ji in labeli) preslikani v končne ID-je vozlišč
                node_id_alias = {}
                seen_labels = {}  # label_key -> nid (deduplikacija vozlišč)
                for idx, n in enumerate(g_data.get("nodes", [])):
                    if not isinstance(n, dict):
                        continue
                    # Label: podpira 'label', 'name', 'title', 'node'
                    lbl = str(first_val(n, ["label", "name", "title", "node"], f"Node {idx + 1}")).strip()
                    # ID: podpira 'id', 'node_id', 'nodeId'; sicer unikaten nadomestni ID
                    raw_id = first_val(n, ["id", "node_id", "nodeId"])
                    nid = str(raw_id).strip() if raw_id not in (None, "") else f"n{idx}"

                    # ANTI-REDUNDANCA: podvojena vozlišča (isti label) preskočimo,
                    # a njihov ID preslikamo na obstoječe vozlišče, da povezave ostanejo veljavne.
                    label_key = lbl.lower()
                    if label_key in seen_labels:
                        node_id_alias[nid.lower()] = seen_labels[label_key]
                        node_id_alias[label_key] = seen_labels[label_key]
                        continue
                    seen_labels[label_key] = nid
                    node_id_alias[nid.lower()] = nid
                    node_id_alias[label_key] = nid

                    n_color = first_val(n, ["color", "colour"], "#DDEBF7")
                    # Oblika: podpira 'shape', 'node_type', 'type', 'kind', 'geometry'
                    n_shape = str(first_val(n, ["shape", "node_type", "type", "kind", "geometry"], "rectangle")).strip().lower()

                    # STROGA VELIKOSTNA HIERARHIJA (Preprečuje redukcijo na kroge)
                    if n_shape == 'star': 
                        n_size = 145 # Makro-vizija (Cilji)
                    elif n_shape == 'diamond': 
                        n_size = 125 # Inovacije (Innovation Cores)
                    elif n_shape == 'hexagon': 
                        n_size = 115 # Znanstvene domene
                    elif n_shape == 'octagon': 
                        n_size = 110 # Etične meje in pravila
                    elif n_shape == 'ellipse': 
                        n_size = 100 # Človeški faktorji
                    elif n_shape == 'triangle': 
                        n_size = 95  # Procesi in metode
                    elif n_shape == 'rectangle': 
                        n_size = 90  # Dejstva in podatki
                    else: 
                        n_size = 85  # Privzeta velikost

                    nodes_to_link.append({"id": nid, "label": lbl})
                    final_elements.append({
                        "data": {
                            "id": nid,
                            "label": lbl,
                            "color": n_color,
                            "shape": n_shape,
                            "size": n_size,
                            "description": first_val(n, ["description", "desc", "details"], "Podroben razčlen v poročilu.")
                        }
                    })

                # --- PROCESIRANJE POVEZAV (CELOTEN SPEKTER LOGIKE) ---
                # Ta del popravi AI napake: npr. "Association" -> "AS"
                rel_map = {
                    "association": "AS", "associative": "AS",
                    "broader term": "BT", "broader": "BT",
                    "narrower term": "NT", "narrower": "NT",
                    "top term": "TT", "root": "TT",
                    "related term": "RT", "related": "RT",
                    "equivalence": "EQ", "synonym": "EQ",
                    "instance": "IN", "example": "IN",
                    "hierarchical-associative": "HA", "hybrid": "HA",
                    "is a type of": "Specialization", "subtype": "Specialization",
                    "generalization": "Generalization", "superclass": "Generalization",
                    "composition": "Composition", "aggregation": "Aggregation",
                    "dependency": "Dependency", "conflict": "Conflict",
                    "containment": "Containment", "realization": "Realization",
                    "if-then": "IF-THEN", "if then": "IF-THEN",
                }

                seen_edges = set()  # Deduplikacija povezav (isti par + relacija)
                valid_node_ids = set(node_id_alias.values())
                for e in g_data.get("edges", []):
                    if not isinstance(e, dict):
                        continue
                    # Relacija: podpira 'rel_type', 'relation', 'rel', 'relationship', 'type', 'edge_type'
                    orig_rel = first_val(e, ["rel_type", "relation", "rel", "relationship", "type", "edge_type"], "AS")
                    raw_rel = str(orig_rel).strip().lower()
                    # Če je AI uporabil polno besedo, jo skrajšamo v kodo
                    rel = rel_map.get(raw_rel, orig_rel)
                    # Normalizacija: 'tt' -> 'TT' ipd., da se povezava poveže s pravim stilom
                    KNOWN_RELS = {"TT","BT","NT","IN","RT","AS","EQ","HA","AND","OR","XOR","NOT","IF-THEN",
                                  "Generalization","Specialization","Realization","Composition","Aggregation",
                                  "Dependency","Conflict","Containment"}
                    rel_u = str(rel).strip().upper()
                    if rel_u in KNOWN_RELS:
                        rel = rel_u
                    elif str(rel).strip() in KNOWN_RELS:
                        rel = str(rel).strip()

                    # --- NOVO (v23): FILTRIRANJE PO IZBRANIH TIPIH POVEZAV ---
                    if selected_edge_types:
                        rel_str = str(rel)
                        is_allowed = rel_str in selected_edge_types or any(
                            t.startswith("Triggers") and rel_str.startswith("Triggers")
                            for t in selected_edge_types
                        )
                        if not is_allowed:
                            continue

                    # --- POVEZLJIVOSTNA OKREPITEV: preslikava vseh zapisov v veljavne ID-je ---
                    # Source/target: podpira 'source'/'from'/'src', 'target'/'to'/'tgt' (ID ali label)
                    src_raw = str(first_val(e, ["source", "from", "src", "source_id", "sourceId"], "")).strip()
                    tgt_raw = str(first_val(e, ["target", "to", "tgt", "target_id", "targetId"], "")).strip()
                    src = node_id_alias.get(src_raw.lower(), src_raw if src_raw in valid_node_ids else None)
                    tgt = node_id_alias.get(tgt_raw.lower(), tgt_raw if tgt_raw in valid_node_ids else None)
                    # Odstranimo povezave na neobstoječa vozlišča ali zankice
                    if not src or not tgt or src == tgt:
                        continue
                    # Odstranimo podvojene povezave (isti par v isti smeri z isto relacijo)
                    edge_key = (src, tgt, str(rel))
                    if edge_key in seen_edges:
                        continue
                    seen_edges.add(edge_key)

                    # BARVNA MATRICA (Povezana z render_cytoscape_network stili)
                    # 1. RIGIDNA HIERARHIJA IN DEDNOST (Temno modra)
                    if rel in ["TT", "BT", "NT", "Generalization", "Specialization", "Containment", "Realization"]:
                        e_color = "#1D3557"
                    # 2. STRUKTURNA INTEGRACIJA (Srednje modra)
                    elif rel in ["IN", "Composition"]:
                        e_color = "#0077B6"
                    # 3. ASOCIATIVNA IN LATERALNA MREŽA (Zelena)
                    elif rel in ["RT", "AS", "Dependency", "Aggregation"]:
                        e_color = "#2A9D8F"
                    # 4. HIBRIDNA LOGIKA (Petrič HA - Vijolična)
                    elif rel == "HA":
                        e_color = "#7B2CB1"
                    # 5. SEMANTIČNA EKVIVALENCA (Rumena)
                    elif rel == "EQ":
                        e_color = "#F1C40F"
                    # 6. SISTEMSKA NAPETOST IN KONFLIKT (Rdeča)
                    elif rel == "Conflict":
                        e_color = "#B91D1D"
                    # 7. LOGIČNA VRATA (Neon barve)
                    elif rel == "AND":
                        e_color = "#00FF00"
                    elif rel == "IF-THEN":
                        e_color = "#FFD700"
                    elif rel in ["OR", "XOR"]:
                        e_color = "#00BFFF"
                    elif rel == "NOT":
                        e_color = "#FF4500"
                    else:
                        e_color = "#ADB5BD"  # Nevtralna siva za neznane tipe

                    final_elements.append({
                        "data": { 
                            "id": str(e.get("id", f"e{len(final_elements)}")),
                            "source": src, 
                            "target": tgt, 
                            "rel_type": rel,  # TUKAJ JE ZDAJ KRATICA (npr. AS)
                            "color": e_color 
                        }
                    })

                # --- POVEZLJIVOSTNA OKREPITEV: samodejni mostovi za izolirana vozlišča ---
                connected = set()
                for el in final_elements:
                    d = el.get("data", {})
                    if "source" in d:
                        connected.add(d["source"]); connected.add(d["target"])
                all_node_ids = [el["data"]["id"] for el in final_elements if "label" in el.get("data", {})]
                hexagon_ids = [el["data"]["id"] for el in final_elements if el.get("data", {}).get("shape") == "hexagon"]
                bridge_anchor = hexagon_ids[0] if hexagon_ids else (all_node_ids[0] if all_node_ids else None)
                bridged_count = 0
                for nid in all_node_ids:
                    if nid not in connected and bridge_anchor and nid != bridge_anchor:
                        # Izolirano vozlišče povežemo z asociativno RT povezavo z najbližjo domeno
                        final_elements.append({
                            "data": {
                                "id": f"e_bridge_{nid}",
                                "source": nid,
                                "target": bridge_anchor,
                                "rel_type": "RT",
                                "color": "#2A9D8F"
                            }
                        })
                        bridged_count += 1
                if bridged_count:
                    st.caption(f"🔗 Connectivity reinforcement: {bridged_count} isolated node(s) auto-bridged into the network (RT).")

            # --- 5. FINAL DISPLAY: SEQUENTIAL INTERACTIVE SYNERGY REPORT ---

            # 5a. GLOBAL SEMANTIC HIGHLIGHTER (Regex Highlighter)
            final_interactive_report = full_report
            if nodes_to_link:
                # Razvrstimo ključne besede po dolžini (daljše prej), da se krajše ne vmešavajo
                sorted_keywords = sorted(nodes_to_link, key=lambda x: len(x['label']), reverse=True)
                for item in sorted_keywords:
                    lbl = item['label']
                    if len(lbl) > 2:
                        g_url = urllib.parse.quote(lbl)
                        # The link style ensures high visibility
                        link_html = f'<a href="https://www.google.com/search?q={g_url}" target="_blank" class="semantic-node-highlight">{lbl}<i class="google-icon">↗</i></a>'

                        # Unicode-safe regex to catch terms in report
                        pattern = re.compile(rf'(?<!\w){re.escape(lbl)}(?!\w)', re.IGNORECASE | re.UNICODE)

                        # Linkamo le PRVO pojavitev besede za čistočo
                        final_interactive_report = pattern.sub(link_html, final_interactive_report, count=1)

            # 5b. RENDERING THE INTERACTIVE REPORT
            st.subheader("🧱 INTEGRATED HIERARCHOLOGICAL REPORT")
            if biblio_data:
                with st.expander("📚 EXTRACTED AUTHOR BACKGROUND", expanded=False):
                    st.markdown(biblio_data)

            # Display the full linked report (P1 + P2)
            st.markdown(final_interactive_report, unsafe_allow_html=True)

            # 5c. (ODSTRANJENO: STRATEGIC INNOVATION DEEP-DIVE — podvojene inovativne ideje
            #      so bile odstranjene; vsaka inovacija je opisana izključno v poročilu ali na grafu.)

            # 5d. MINIMALIST SYSTEM LEGEND (FINAL ARCHITECTURE)
            if final_elements:
                st.markdown("""
                <div style="font-size: 0.78em; color: #444; background: #ffffff; padding: 15px 25px; border-radius: 15px; border: 1px solid #e9ecef; margin-top: 30px; box-shadow: 0 4px 12px rgba(0,0,0,0.03);">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
                        <div>
                            <b style="color: #1d3557; text-transform: uppercase; letter-spacing: 1px;">Nodes (Geometry):</b><br>
                            ⭐ Goal | ⬢ Domain | 💠 Innovation | △ Process | ▭ Data | ⬣ Rule | ⭔ Bio
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

                # --- IZ RAZLIČNIH OMREŽIJ ENO OMREŽJE: fuzija čez več zagonov ---
                # Vsak nov zagon se zlije s prejšnjimi grafi v eno akumulativno omrežje
                # (deduplikacija po labelu vozlišč in po paru povezav).
                def merge_networks(base_elements, new_elements):
                    merged = []
                    seen_n, seen_e = {}, set()
                    # Najprej obstoječe (starejši pogoji imajo prednost pred prekrivnimi)
                    for el in (base_elements or []):
                        d = el.get("data", {})
                        if "label" in d:
                            seen_n[d["label"].strip().lower()] = d["id"]
                            merged.append(el)
                        elif "source" in d:
                            key = (d["source"], d["target"], d.get("rel_type"))
                            if key not in seen_e:
                                seen_e.add(key)
                                merged.append(el)
                    # Nato nove elemente dodamo brez podvajanja
                    for el in (new_elements or []):
                        d = el.get("data", {})
                        if "label" in d:
                            lkey = d["label"].strip().lower()
                            if lkey in seen_n:
                                continue  # vozlišče že obstaja
                            seen_n[lkey] = d["id"]
                            merged.append(el)
                        elif "source" in d:
                            key = (d["source"], d["target"], d.get("rel_type"))
                            if key in seen_e:
                                continue
                            seen_e.add(key)
                            merged.append(el)
                    return merged

                prev_network = st.session_state.get('accumulated_network', [])
                st.session_state.accumulated_network = merge_networks(prev_network, final_elements)
                # Za prikaz uporabimo ZDRUŽENO omrežje (iz različnih omrežij eno omrežje)
                final_elements = st.session_state.accumulated_network
                if len(prev_network) > 0:
                    st.success(f"🌐 Network Fusion: merged with previous run(s) — one unified network ({len(final_elements)} elements total). Use ♻️ RESET to start a fresh network.")

                # --- NOVO (v23): priprava elementov za prikaz (modularno ali navadno) ---
                grouping_mode = {"Node Color (semantic domains)": "color", "Node Shape (logical level)": "shape", "Color + Shape (fine-grained)": "both"}.get(module_grouping, "color")
                if modular_view:
                    display_elements = build_modular_elements(final_elements, grouping=grouping_mode)
                    st.caption(f"🧩 Modular view enabled: nodes grouped into module boxes by {module_grouping.lower()}.")
                else:
                    display_elements = final_elements

                # 5e. FINAL GRAPH RENDERING (Z DINAMIČNO PERSPEKTIVO)
                view_title = f"🕸️ HYBRID SEMANTIC SYSTEM MAP ({graph_perspective.upper()} VIEW" + (" — MODULAR" if modular_view else "") + ")"
                st.subheader(view_title)
                render_cytoscape_network(
                    display_elements, 
                    layout_type=graph_perspective, 
                    container_id=f"cy_{int(time.time())}",
                    modular=modular_view
                )

                # 5f. IZVOZ POROČILA IN GRAFA V SAMOSTOJNI HTML
                def build_html_export(elements, report_md, modular=False):
                    """Skuha samostojno HTML datoteko: poročilo + interaktivni graf (Cytoscape)."""
                    # Poročilo varno prek base64 (prepreči lomljenje zaradi narekovajev/znakov)
                    report_b64 = base64.b64encode((report_md or "").encode("utf-8")).decode("ascii")
                    elements_json = json.dumps(elements or [])
                    layout_js = "cose"
                    module_style_js = """
        { selector: 'node[module_box = "true"]', style: {
            'shape': 'roundrectangle', 'background-color': 'data(color)', 'background-opacity': 0.12,
            'border-width': 3, 'border-style': 'dashed', 'border-color': 'data(color)',
            'label': 'data(label)', 'color': '#1d3557', 'font-size': '15px', 'font-weight': '900',
            'text-valign': 'top', 'text-halign': 'center', 'text-transform': 'uppercase', 'padding': '28px'
        }},""" if modular else ""
                    html = """<!DOCTYPE html>
<html lang="sl">
<head>
<meta charset="utf-8">
<title>SIS Universal Knowledge Synthesizer — Export __SYSDATE__</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.26.0/cytoscape.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<style>
body { font-family: 'Segoe UI', Roboto, sans-serif; margin: 0; background: #f8f9fa; color: #1d3557; }
header { background: linear-gradient(90deg, #1d3557, #457b9d); color: white; padding: 30px 40px; }
header h1 { margin: 0; font-size: 1.8em; }
#report { max-width: 1100px; margin: 30px auto; background: white; padding: 40px 50px; border-radius: 15px; box-shadow: 0 10px 40px rgba(0,0,0,0.08); line-height: 1.8; }
#cy { width: 100%; height: 800px; background: white; border-radius: 15px; border: 1px solid #e0e0e0; max-width: 1200px; margin: 0 auto 40px; }
.toolbar { max-width: 1200px; margin: 0 auto 10px; display: flex; gap: 8px; }
.toolbar button { padding: 10px 18px; background: #1d3557; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: 800; font-size: 12px; }
h2 { margin-top: 40px; text-align: center; }
</style>
</head>
<body>
<header><h1>🧱 SIS Universal Knowledge Synthesizer</h1><p>__SYSDATE__ | __VERSION__</p></header>
<h2>📋 INTEGRATED HIERARCHOLOGICAL REPORT</h2>
<div id="report"></div>
<h2>🕸️ HYBRID SEMANTIC SYSTEM MAP</h2>
<div class="toolbar">
    <button onclick="zoomIn()">➕ ZOOM IN</button>
    <button onclick="zoomOut()">➖ ZOOM OUT</button>
    <button onclick="cy1.fit(undefined, 40)">🎯 FIT</button>
    <button onclick="downloadPng()">💾 PNG</button>
</div>
<div id="cy"></div>
<script>
var cy1;
function b64ToUtf8(b64) {
    var bin = atob(b64);
    var bytes = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    return new TextDecoder('utf-8').decode(bytes);
}
document.getElementById('report').innerHTML = marked.parse(b64ToUtf8("__REPORT_B64__"));
cy1 = cytoscape({
    container: document.getElementById('cy'),
    elements: __ELEMENTS__,
    style: [
        { selector: 'node', style: {
            'label': 'data(label)', 'text-valign': 'center', 'text-halign': 'center',
            'color': '#1d3557', 'background-color': 'data(color)',
            'width': 'data(size)', 'height': 'data(size)', 'shape': 'data(shape)',
            'font-size': '12px', 'font-weight': 'bold', 'text-wrap': 'wrap', 'text-max-width': '80px',
            'border-width': 3, 'border-color': '#ffffff', 'text-outline-color': '#ffffff', 'text-outline-width': 2
        }},
__MODULE_STYLE__
        { selector: 'edge', style: {
            'width': 2, 'line-color': 'data(color)', 'label': 'data(rel_type)', 'font-size': '9px',
            'color': '#2a9d8f', 'curve-style': 'unbundled-bezier', 'control-point-step-size': 40,
            'target-arrow-color': 'data(color)', 'target-arrow-shape': 'vee',
            'text-background-opacity': 1, 'text-background-color': '#ffffff',
            'text-background-padding': '3px', 'text-background-shape': 'roundrectangle', 'opacity': 0.8
        }}
    ],
    layout: { name: '__LAYOUT__', idealEdgeLength: 120, nodeOverlap: 50, fit: true, padding: 50, nodeRepulsion: 1000000, animate: false }
});
function zoomIn() { cy1.zoom({ level: cy1.zoom() * 1.3, renderedPosition: { x: cy1.width() / 2, y: cy1.height() / 2 } }); }
function zoomOut() { cy1.zoom({ level: cy1.zoom() / 1.3, renderedPosition: { x: cy1.width() / 2, y: cy1.height() / 2 } }); }
function downloadPng() {
    var link = document.createElement('a');
    link.href = cy1.png({ full: true, bg: 'white', scale: 3 });
    link.download = 'sis_universal_graph_export.png';
    link.click();
}
</script>
</body>
</html>"""
                    html = html.replace("__SYSDATE__", SYSTEM_DATE).replace("__VERSION__", VERSION_CODE)
                    html = html.replace("__REPORT_B64__", report_b64)
                    html = html.replace("__ELEMENTS__", elements_json)
                    html = html.replace("__LAYOUT__", layout_js)
                    html = html.replace("__MODULE_STYLE__", module_style_js)
                    return html

                # Gumb za prenos samostojnega HTML (poročilo + graf v eni datoteki)
                st.download_button(
                    "🌐 EXPORT REPORT + GRAPH (HTML)",
                    data=build_html_export(display_elements, full_report, modular=modular_view),
                    file_name=f"sis_report_graph_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                    mime="text/html",
                    use_container_width=True,
                    key=f"html_export_btn_{int(time.time())}"
                )

                st.session_state.final_graph_elements = final_elements

        except Exception as e:
            st.error(f"❌ Pipeline Failure: {str(e)}")

# ============================================================================= 
# 6. FOOTER
# ============================================================================= 
st.divider()
st.caption(f"SIS Universal Knowledge Synthesizer | {VERSION_CODE} | {SYSTEM_DATE}")
