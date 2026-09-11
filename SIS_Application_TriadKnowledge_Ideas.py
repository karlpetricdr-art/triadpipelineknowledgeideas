import streamlit as st
import json
import base64
import requests
import urllib.parse
import re
import time
import io
import html
import ast
import operator as _operator
import statistics
from collections import Counter, defaultdict
from itertools import combinations
from typing import Any, Dict, List, Tuple, Optional
from datetime import datetime
from google import genai
from google.genai import types
import streamlit.components.v1 as components

# =============================================================================
# 0. GLOBAL CONFIGURATION & SESSION DATE (FEBRUARY 24, 2026)
# =============================================================================
SYSTEM_DATE = datetime.now().strftime("%B %d, %Y")
VERSION_CODE = "v25.0.0-ADAPTIVE-SYNTHESIS-ARCHITECTURE"

# =============================================================================
# INITIALIZATION FIX: Preprečuje AttributeError pri zagonu in resetiranju
# =============================================================================
if 'show_user_guide' not in st.session_state:
    st.session_state.show_user_guide = False

# Zagotovimo, da so vsi ključi prisotni v session_state pred prvo uporabo
if 'phase1_synthesis' not in st.session_state:
    st.session_state.phase1_synthesis = ""

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
        color: #1d3557 !important; /* Maximum Contrast */
        font-size: 0.98em !important;
        font-weight: 500 !important;
        line-height: 1.6 !important;
        opacity: 1 !important;
    }

    /* 3. RE-STYLE EXPANDERS FOR PROFESSIONAL DENSITY */
    .stExpander {
        background-color: #f5f7fa !important;
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

def fetch_author_bibliographies(author_input):
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
            pass # Ignore API errors to keep the app running
    return comprehensive_biblio

import math

def calculate_systemic_stress(f_pf, f_sf, f_pr):
    """
    Implements Dr. Petrič's Stress Intensity formula (Page 60).
    σ0SF = arcsin(sqrt((FSF * FPR) / FPF))
    """
    try:
        # Convert to float and ensure f_pf (Positive Factors) isn't zero to avoid crash
        pf = float(f_pf)
        sf = float(f_sf)
        pr = float(f_pr)
        
        if pf <= 0: pf = 0.001 
        
        # Calculate the ratio
        ratio = (sf * pr) / pf
        
        # MATH SAFETY: sqrt() needs positive, arcsin() needs value between -1 and 1
        clamped_ratio = max(0.0, min(ratio, 1.0))
        
        stress_rad = math.asin(math.sqrt(clamped_ratio))
        
        # Returns the result in "Stress Degrees" (°S) as defined in the book
        return math.degrees(stress_rad)
    except Exception:
        return 0.0

def calculate_effective_energy(stress_intensity, initial_potential=2500):
    """
    Implements the Energy Loss Index (W_EP) from Page 61 of the book.
    W_EP = Initial_Energy - (Initial_Energy * (Stress_Intensity / 90))
    2500 Kcal is the default baseline used in Dr. Petrič's example.
    """
    try:
        # The book defines 90°S as the theoretical maximum stress
        max_stress = 90.0
        
        # Calculate the proportion of energy lost
        loss_ratio = stress_intensity / max_stress
        
        # Ensure ratio stays within logical bounds [0, 1]
        loss_ratio = max(0.0, min(loss_ratio, 1.0))
        
        # Calculate remaining (effective) energy
        effective_energy = initial_potential - (initial_potential * loss_ratio)
        
        # Efficiency percentage
        efficiency_pct = (effective_energy / initial_potential) * 100
        
        return round(effective_energy, 2), round(efficiency_pct, 1)
    except Exception:
        return 0.0, 0.0

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
        "Scientific Realism": "The view that scientific theories can provide approximately true descriptions of a mind-independent reality, including entities not directly observable.",
        "Critical Realism": "A stratified view of reality distinguishing observable events, underlying mechanisms, and generative structures while recognizing limits of observation.",
        "Postpositivism": "A fallibilist approach to science recognizing that observations and theories are theory-laden, while retaining systematic empirical testing and critical evaluation.",
        "Bayesianism": "An inferential framework in which hypotheses are updated by evidence through probabilistic reasoning and explicit prior assumptions.",
        "Mechanistic Explanation": "Explaining phenomena by identifying entities, activities, organization, and interactions that generate observable outcomes.",
        "Evolutionary Paradigm": "Understanding change through variation, selection, inheritance, adaptation, and historical processes across biological and social systems.",
        "Complexity and Emergence": "Explaining system-level patterns as emergent outcomes of nonlinear interactions among interconnected components.",
        "Cybernetics": "The study of feedback, regulation, communication, control, and adaptive behavior in complex systems.",
        "Computational Paradigm": "Treating computation, algorithms, information processing, and simulation as fundamental means for representing and investigating phenomena.",
        "Process Philosophy": "Understanding reality primarily in terms of processes, relations, transformation, and becoming rather than static entities alone."
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
        "Astronomy": {
            "cat": "Natural", 
            "methods": ["Observational Astronomy", "Astrophysical Modeling", "Spectroscopy", "Astrometry"], 
            "tools": ["Telescopes", "Spectrographs", "Radio Interferometers", "Space Observatories"], 
            "facets": ["Planetary Science", "Stellar Astronomy", "Galactic Astronomy", "Cosmology"]
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

# v25 architecture expansion: the original IMA/MA vocabulary remains compatible,
# but the reasoning kernel is strengthened with explicit system-design constructs.
HUMAN_THINKING_METAMODEL["nodes"].update({
    "System boundary": {"color": "#495057", "shape": "rectangle",
                        "desc": "Explicit boundary separating the modeled system from its environment."},
    "Causal mechanism": {"color": "#e8590c", "shape": "rectangle",
                         "desc": "Mechanism that explains how a condition produces a change or outcome."},
    "Feedback loop": {"color": "#0ca678", "shape": "rectangle",
                      "desc": "Circular influence in which an output modifies a later system state."},
    "Invariant": {"color": "#7048e8", "shape": "rectangle",
                  "desc": "Property or relation intended to remain stable under transformation."},
    "Scenario": {"color": "#1971c2", "shape": "rectangle",
                 "desc": "Explicit future or counterfactual configuration used for testing an idea."},
    "Evidence": {"color": "#2b8a3e", "shape": "rectangle",
                 "desc": "Source-supported observation, measurement, document or reproducible result."},
    "Hypothesis": {"color": "#ae3ec9", "shape": "octagon",
                   "desc": "Provisional explanatory proposition that can be tested or challenged."},
    "Constraint": {"color": "#c92a2a", "shape": "octagon",
                   "desc": "Condition limiting feasible states, actions or transformations."},
    "Intervention": {"color": "#d9480f", "shape": "triangle",
                     "desc": "Deliberate change introduced into a system to alter its trajectory."},
    "Evaluation criterion": {"color": "#364fc7", "shape": "octagon",
                             "desc": "Explicit criterion used to compare solution quality."},
    "Architecture pattern": {"color": "#087f5b", "shape": "diamond",
                             "desc": "Reusable structural arrangement connecting components and behavior."},
    "Emergence": {"color": "#5f3dc4", "shape": "ellipse",
                  "desc": "System-level property arising from interactions among components."},
    "Outcome": {"color": "#2f9e44", "shape": "star",
                "desc": "Observable or intended result used to assess a transformation."},
})
HUMAN_THINKING_METAMODEL["relations"].extend([
    ("Problem", "System boundary", "Dependency"),
    ("System boundary", "Constraint", "Containment"),
    ("Evidence", "Hypothesis", "supports"),
    ("Hypothesis", "Causal mechanism", "explains"),
    ("Causal mechanism", "Outcome", "causes"),
    ("Intervention", "Causal mechanism", "modifies"),
    ("Causal mechanism", "Feedback loop", "forms"),
    ("Feedback loop", "Emergence", "produces"),
    ("Scenario", "Hypothesis", "tests"),
    ("Evaluation criterion", "Goal", "measures"),
    ("Architecture pattern", "Intervention", "realizes"),
])

MENTAL_APPROACHES_ONTOLOGY["nodes"].update({
    "Recombination": {"color": "#ff922b", "shape": "diamond",
                      "desc": "Recombine useful components from different domains into a new configuration."},
    "Inversion": {"color": "#e03131", "shape": "diamond",
                  "desc": "Reverse an assumed direction, role, dependency or objective to expose alternatives."},
    "Scale shifting": {"color": "#1c7ed6", "shape": "diamond",
                       "desc": "Move deliberately between Micro, Meso and Macro levels to reveal hidden structure."},
    "Boundary crossing": {"color": "#0ca678", "shape": "diamond",
                          "desc": "Transfer a mechanism across a system, disciplinary or organizational boundary."},
    "Counterfactual reasoning": {"color": "#7048e8", "shape": "diamond",
                                 "desc": "Test an idea by changing a critical assumption and examining consequences."},
    "Abstraction ladder": {"color": "#4263eb", "shape": "diamond",
                           "desc": "Move between concrete instances and abstract principles without losing traceability."},
    "Constraint relaxation": {"color": "#f08c00", "shape": "diamond",
                              "desc": "Temporarily relax a constraint to discover otherwise hidden configurations."},
    "Feedback reframing": {"color": "#12b886", "shape": "diamond",
                           "desc": "Reinterpret a feedback loop as a design resource rather than only a problem."},
    "Mechanism transfer": {"color": "#7950f2", "shape": "diamond",
                          "desc": "Transfer a causal mechanism, not merely an analogy, between domains."},
    "Modularization": {"color": "#087f5b", "shape": "diamond",
                       "desc": "Partition a system into coherent modules with explicit interfaces and dependencies."},
})


# =============================================================================
# SIS v25.0 — ADAPTIVE SYNTHESIS / INNOVATION / EQUATION ARCHITECTURE
# =============================================================================

# The original ontologies and science taxonomy are intentionally preserved above.
# v25 adds an adaptive quality loop, a unified graph model, modular organic views,
# and an opt-in equation engine. Calculation is NEVER performed unless explicitly
# requested by the user through the UI.

TARGET_SCORE = 9.90
QUALITY_DIMENSIONS = [
    "conceptual_novelty",
    "systemic_architecture",
    "interdisciplinary_integration",
    "practicality",
    "clarity",
]

RELATION_TYPES = [
    "TT", "BT", "NT", "RT", "EQ", "AS", "IN",
    "Generalization", "Specialization", "Containment", "Realization",
    "Composition", "Aggregation", "Dependency", "Conflict",
    "AND", "OR", "XOR", "NOT", "IF-THEN"
]

GRAPH_LAYER_COLORS = {
    "Lexical": "#6f42c1",
    "Category": "#0d6efd",
    "Hierarchy": "#20c997",
    "Semantic": "#198754",
    "Network": "#fd7e14",
    "Analytical": "#dc3545",
    "Energetic": "#7b2cbf",
    "Metamodel": "#495057",
    "Mental Approach": "#6366f1",
    "Science": "#00838f",
    "Innovation": "#e8590c",
    "Logic": "#d63384",
    "Equation": "#f08c00",
}

# -------------------------------------------------------------------------
# Connected equation system — inspired by the seven-layer globe model.
# -------------------------------------------------------------------------
EQUATION_SYSTEM = {
    "Observed Frequency": {
        "symbol": "f",
        "formula": "f",
        "requires": ["f"],
        "layer": "Lexical",
        "description": "Observed frequency of a term/event.",
    },
    "Distinct Frequency": {
        "symbol": "v",
        "formula": "v",
        "requires": ["v"],
        "layer": "Lexical",
        "description": "Number of distinct observed terms/events.",
    },
    "Total Observations": {
        "symbol": "N",
        "formula": "N",
        "requires": ["N"],
        "layer": "Lexical",
        "description": "Total number of observations/tokens.",
    },
    "Type-Token Ratio": {
        "symbol": "TTR",
        "formula": "v / N",
        "requires": ["v", "N"],
        "layer": "Lexical",
        "description": "Lexical diversity.",
    },
    "Category Frequency": {
        "symbol": "CF",
        "formula": "fc / N",
        "requires": ["fc", "N"],
        "layer": "Category",
        "description": "Relative frequency of a category.",
    },
    "Category Concentration": {
        "symbol": "CC",
        "formula": "sum_f2 / N",
        "requires": ["sum_f2", "N"],
        "layer": "Category",
        "description": "Concentration of observations across categories.",
    },
    "Category Factor": {
        "symbol": "Kc",
        "formula": "CF * CC / N",
        "requires": ["CF", "CC", "N"],
        "layer": "Category",
        "description": "Combined category-frequency/concentration factor.",
    },
    "Hierarchical Depth": {
        "symbol": "d",
        "formula": "log(N, base)",
        "requires": ["N", "base"],
        "layer": "Hierarchy",
        "description": "Logarithmic hierarchy depth.",
    },
    "Hierarchical Linguistic Power": {
        "symbol": "HLP",
        "formula": "I * A * C * w * (1 + alpha * d)",
        "requires": ["I", "A", "C", "w", "alpha", "d"],
        "layer": "Hierarchy",
        "description": "Composite hierarchical-linguistic power.",
    },
    "PMI": {
        "symbol": "PMI",
        "formula": "log2(Pxy / (Px * Py))",
        "requires": ["Pxy", "Px", "Py"],
        "layer": "Semantic",
        "description": "Pointwise mutual information.",
    },
    "Associative Strength": {
        "symbol": "AS",
        "formula": "PMI",
        "requires": ["PMI"],
        "layer": "Semantic",
        "description": "Associative strength derived from PMI.",
    },
    "Semantic Centrality": {
        "symbol": "SC",
        "formula": "sum_AS / n",
        "requires": ["sum_AS", "n"],
        "layer": "Semantic",
        "description": "Mean associative strength across a semantic neighborhood.",
    },
    "Degree": {
        "symbol": "D",
        "formula": "k / (n - 1)",
        "requires": ["k", "n"],
        "layer": "Network",
        "description": "Normalized node degree.",
    },
    "Network Density": {
        "symbol": "ND",
        "formula": "2 * E / (n * (n - 1))",
        "requires": ["E", "n"],
        "layer": "Network",
        "description": "Density of an undirected simple graph.",
    },
    "Co-occurrence": {
        "symbol": "CCo",
        "formula": "sum_cij / N",
        "requires": ["sum_cij", "N"],
        "layer": "Network",
        "description": "Normalized co-occurrence.",
    },
    "Network Criticality": {
        "symbol": "Ck",
        "formula": "(BC + EC + D) / 3",
        "requires": ["BC", "EC", "D"],
        "layer": "Analytical",
        "description": "Composite network criticality.",
    },
    "Stress Argument": {
        "symbol": "Ag",
        "formula": "(FSF * FPR) / FPF",
        "requires": ["FSF", "FPR", "FPF"],
        "layer": "Analytical",
        "description": "Argument of the stress-intensity relation.",
    },
    "Stress Intensity": {
        "symbol": "sigma",
        "formula": "degrees(asin(sqrt(clamp(Ag, 0, 1))))",
        "requires": ["Ag"],
        "layer": "Analytical",
        "description": "Stress intensity in degrees (°S).",
    },
    "Useful Energy": {
        "symbol": "WEU",
        "formula": "WI * (1 - sigma / 90)",
        "requires": ["WI", "sigma"],
        "layer": "Energetic",
        "description": "Useful energy remaining after stress loss.",
    },
    "Energy Loss": {
        "symbol": "WL",
        "formula": "WI - WEU",
        "requires": ["WI", "WEU"],
        "layer": "Energetic",
        "description": "Energy lost to the modeled stress load.",
    },
    "Efficiency": {
        "symbol": "eta",
        "formula": "100 * WEU / WI",
        "requires": ["WEU", "WI"],
        "layer": "Energetic",
        "description": "Useful-energy efficiency percentage.",
    },
}

SAFE_FUNCS = {
    "log": math.log,
    "log2": math.log2,
    "sqrt": math.sqrt,
    "asin": math.asin,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "degrees": math.degrees,
    "radians": math.radians,
    "abs": abs,
    "min": min,
    "max": max,
    "clamp": lambda x, lo, hi: max(lo, min(x, hi)),
}

def _safe_eval(expr: str, variables: Dict[str, float]) -> float:
    """Evaluate only arithmetic expressions and whitelisted math functions."""
    tree = ast.parse(expr, mode="eval")
    allowed_nodes = (
        ast.Expression, ast.BinOp, ast.UnaryOp, ast.Add, ast.Sub, ast.Mult,
        ast.Div, ast.Pow, ast.Mod, ast.USub, ast.UAdd, ast.Constant,
        ast.Name, ast.Call, ast.Load, ast.Tuple,
    )
    for node in ast.walk(tree):
        if not isinstance(node, allowed_nodes):
            raise ValueError(f"Unsupported expression element: {type(node).__name__}")
        if isinstance(node, ast.Name) and node.id not in variables and node.id not in SAFE_FUNCS:
            raise ValueError(f"Unknown variable: {node.id}")
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in SAFE_FUNCS:
                raise ValueError("Function is not allowed")
    env = dict(SAFE_FUNCS)
    env.update({k: float(v) for k, v in variables.items()})
    return float(eval(compile(tree, "<equation>", "eval"), {"__builtins__": {}}, env))

def calculate_equation_chain(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate only equations whose dependencies are explicitly available."""
    values = {}
    for key, value in (inputs or {}).items():
        try:
            values[key] = float(value)
        except (TypeError, ValueError):
            pass

    results = {}
    symbol_values = {}
    pending = dict(EQUATION_SYSTEM)

    # Fixed-point evaluation. Dependencies are expressed with equation symbols,
    # while results remain keyed by human-readable equation names.
    for _ in range(len(EQUATION_SYSTEM) + 2):
        progress = False
        for name, spec in pending.items():
            if name in results:
                continue
            if all(dep in values or dep in symbol_values for dep in spec["requires"]):
                local = dict(values)
                local.update(symbol_values)
                try:
                    value = _safe_eval(spec["formula"], local)
                    results[name] = value
                    symbol_values[spec["symbol"]] = value
                    progress = True
                except Exception:
                    continue
        if not progress:
            break

    return {
        "inputs": values,
        "results": results,
        "symbol_values": symbol_values,
        "equations": EQUATION_SYSTEM,
    }

def calculation_requested(user_query: str, idea_query: str, explicit_toggle: bool) -> bool:
    if explicit_toggle:
        return True
    textq = f"{user_query or ''} {idea_query or ''}".lower()
    triggers = [
        "[calculate]", "[calculation]", "[calculate equations]", "[izračunaj]",
        "izračun", "kalkul", "calculate", "calculation", "compute", "equation",
        "formula", "mathematical calculation", "numeric result",
    ]
    return any(t in textq for t in triggers)

# -------------------------------------------------------------------------
# Adaptive scoring / refinement
# -------------------------------------------------------------------------
def extract_json_object(raw: str) -> Optional[Dict[str, Any]]:
    """Extract the first balanced JSON object from an LLM response."""
    if not raw:
        return None
    text0 = re.sub(r"```(?:json)?", "", raw, flags=re.I).replace("```", "").strip()
    start = text0.find("{")
    if start < 0:
        return None
    depth = 0
    in_string = False
    escaped = False
    for i in range(start, len(text0)):
        ch = text0[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    obj = json.loads(text0[start:i + 1])
                    return obj if isinstance(obj, dict) else None
                except Exception:
                    return None
    return None

def parse_graph_payload(raw: str) -> Tuple[str, Dict[str, Any]]:
    marker = "### SEMANTIC_GRAPH_JSON"
    if marker not in raw:
        return raw, {"system_metrics": {}, "nodes": [], "edges": []}
    report, json_part = raw.split(marker, 1)
    graph = extract_json_object(json_part) or {"system_metrics": {}, "nodes": [], "edges": []}
    return report.strip(), graph

def normalize_graph(g_data: Dict[str, Any], max_nodes: int = 50, max_edges: int = 80) -> Dict[str, Any]:
    """Normalize, deduplicate and rank graph content; never allow orphan edges."""
    nodes_raw = g_data.get("nodes", []) if isinstance(g_data, dict) else []
    edges_raw = g_data.get("edges", []) if isinstance(g_data, dict) else []

    clean_nodes = []
    seen_ids = set()
    for idx, n in enumerate(nodes_raw):
        if not isinstance(n, dict):
            continue
        nid = str(n.get("id") or f"n{idx+1}")
        if nid in seen_ids:
            continue
        seen_ids.add(nid)
        label = str(n.get("label") or f"Node {idx+1}").strip()
        shape = str(n.get("shape") or "rectangle").strip()
        layer = str(n.get("layer") or "Semantic").strip()
        importance = float(n.get("importance", 0.5) or 0.5)
        clean_nodes.append({
            "id": nid,
            "label": label[:120],
            "shape": shape,
            "color": n.get("color") or GRAPH_LAYER_COLORS.get(layer, "#6c757d"),
            "description": str(n.get("description") or "")[:700],
            "layer": layer,
            "importance": max(0.0, min(1.0, importance)),
            "module": str(n.get("module") or layer),
        })

    clean_nodes.sort(key=lambda x: (-x["importance"], x["label"].lower()))
    clean_nodes = clean_nodes[:max_nodes]
    valid_ids = {n["id"] for n in clean_nodes}

    clean_edges = []
    seen_edges = set()
    for idx, e in enumerate(edges_raw):
        if not isinstance(e, dict):
            continue
        s = str(e.get("source", ""))
        t = str(e.get("target", ""))
        rel = str(e.get("rel_type") or "RT")
        if s not in valid_ids or t not in valid_ids or s == t or rel not in RELATION_TYPES:
            continue
        key = (s, t, rel)
        if key in seen_edges:
            continue
        seen_edges.add(key)
        weight = float(e.get("weight", e.get("importance", 0.5)) or 0.5)
        clean_edges.append({
            "id": str(e.get("id") or f"e{idx+1}"),
            "source": s,
            "target": t,
            "rel_type": rel,
            "weight": max(0.0, min(1.0, weight)),
            "label": str(e.get("label") or rel)[:60],
            "evidence": str(e.get("evidence") or "")[:300],
        })
    clean_edges.sort(key=lambda x: (-x["weight"], x["rel_type"]))
    clean_edges = clean_edges[:max_edges]

    return {
        "system_metrics": g_data.get("system_metrics", {}) if isinstance(g_data, dict) else {},
        "nodes": clean_nodes,
        "edges": clean_edges,
    }

def graph_to_cytoscape(g_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    elements = []
    for n in g_data.get("nodes", []):
        shape = n.get("shape", "rectangle")
        sizes = {
            "star": 135, "diamond": 118, "octagon": 110, "hexagon": 105,
            "triangle": 100, "ellipse": 92, "rectangle": 86,
        }
        elements.append({"data": {
            **n,
            "size": sizes.get(shape, 86),
        }})
    for e in g_data.get("edges", []):
        elements.append({"data": e})
    return elements

def render_cytoscape_network(elements, layout_type="organic", container_id="cy_canvas",
                             title="Unified Semantic Network"):
    """High-clarity Cytoscape renderer with unified layers and modular organic mode."""
    layout_configs = {
        "organic": """{name:'cose', idealEdgeLength:150, nodeRepulsion:180000,
            edgeElasticity:90, nestingFactor:1.0, numIter:1800, fit:true, padding:70}""",
        "hierarchical": """{name:'breadthfirst', directed:true, padding:70,
            spacingFactor:1.45, maximal:true, fit:true}""",
        "concentric": """{name:'concentric', minNodeSpacing:65, padding:70,
            concentric:function(node){return node.data('importance')*10;},
            levelWidth:function(){return 2;}, fit:true}""",
        "circular": """{name:'circle', padding:70, spacingFactor:1.1, fit:true}""",
        "grid": """{name:'grid', padding:70, spacingFactor:1.25, fit:true}""",
    }
    selected_layout = layout_configs.get(layout_type, layout_configs["organic"])
    graph_json = json.dumps(elements, ensure_ascii=False)

    style_edges = "\n".join(
        f"""{{selector:'edge[rel_type="{rel}"]',style:{{'width':{max(2, int(2+5*0.7))},
        'line-style':'{("dashed" if rel in ["Dependency","Realization","OR","NOT","Specialization"] else "solid")}',
        'target-arrow-shape':'{("triangle" if rel in ["Generalization","Realization","Specialization","AND","IF-THEN"] else "vee")}',
        'source-arrow-shape':'{("diamond" if rel in ["Composition","Aggregation"] else "none")}',
        'line-color':'{("#d63384" if rel in ["AND","OR","XOR","NOT","IF-THEN"] else "#6c757d")}'}}}}"""
        for rel in RELATION_TYPES
    )

    html_block = f"""
    <div style="position:relative;width:100%;">
      <div style="font:700 18px Arial;color:#1d3557;margin:4px 0 10px 4px;">{html.escape(title)}</div>
      <div style="position:absolute;right:10px;top:0;z-index:20;display:flex;gap:6px;flex-wrap:wrap;">
        <button id="zin_{container_id}">＋</button>
        <button id="zout_{container_id}">−</button>
        <button id="zfit_{container_id}">⛶ Fit</button>
      </div>
      <div id="{container_id}" style="width:100%;height:820px;background:#fbfcfe;
        border:1px solid #dfe5ec;border-radius:18px;box-shadow:0 8px 28px rgba(0,0,0,.07);"></div>
      <div style="font:12px Arial;color:#495057;margin:7px 4px;">
        Unified network: lexical → category → hierarchy → semantic → network → analytical → energetic,
        connected with IMA, MA, science and logic relations. Click a node to emphasize its neighborhood.
      </div>
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.26.0/cytoscape.min.js"></script>
    <script>
    (function(){{
      const cy=cytoscape({{
        container:document.getElementById('{container_id}'),
        elements:{graph_json},
        style:[
          {{selector:'node',style:{{
            'label':'data(label)','text-valign':'center','text-halign':'center',
            'background-color':'data(color)','width':'data(size)','height':'data(size)',
            'shape':'data(shape)','font-size':'11px','font-weight':'bold',
            'text-wrap':'wrap','text-max-width':'95px','color':'#17202a',
            'border-width':function(n){{return 2+3*n.data('importance');}},
            'border-color':'#ffffff','text-outline-color':'#ffffff','text-outline-width':2
          }}}},
          {{selector:'edge',style:{{
            'width':2,'line-color':'#adb5bd','target-arrow-color':'#adb5bd',
            'target-arrow-shape':'vee','curve-style':'bezier','opacity':0.55,
            'label':'data(rel_type)','font-size':'8px','color':'#495057',
            'text-background-color':'#ffffff','text-background-opacity':0.9,
            'text-background-padding':'2px'
          }}}},
          {style_edges},
          {{selector:'node:selected',style:{{'border-width':6,'border-color':'#111827','z-index':999}}}},
          {{selector:'edge:selected',style:{{'width':5,'opacity':1,'z-index':998}}}}
        ],
        layout:{selected_layout}
      }});
      cy.on('tap','node',function(evt){{
        const n=evt.target;
        cy.elements().removeClass('focus');
        n.closedNeighborhood().addClass('focus');
      }});
      cy.style().selector('.focus').style({{'opacity':1}}).update();
      document.getElementById('zin_{container_id}').onclick=()=>cy.zoom({{level:Math.min(cy.zoom()*1.25,4),renderedPosition:{{x:cy.width()/2,y:cy.height()/2}}}});
      document.getElementById('zout_{container_id}').onclick=()=>cy.zoom({{level:Math.max(cy.zoom()/1.25,.15),renderedPosition:{{x:cy.width()/2,y:cy.height()/2}}}});
      document.getElementById('zfit_{container_id}').onclick=()=>cy.fit(undefined,70);
    }})();
    </script>
    """
    components.html(html_block, height=875)

def build_html_report(report_text, graph_elements, perspective, evaluation=None, equations=None):
    graph_json = json.dumps(graph_elements, ensure_ascii=False)
    score_html = ""
    if evaluation:
        score = evaluation.get("overall_score")
        score_html = f"<h2>Quality optimization</h2><p><b>Overall:</b> {score if score is not None else 'not returned'} / 10.00; target {TARGET_SCORE:.2f}+.</p>"
    eq_html = ""
    if equations and equations.get("results"):
        rows = "".join(
            f"<tr><td>{html.escape(k)}</td><td>{v:.6g}</td><td>{html.escape(EQUATION_SYSTEM[k]['symbol'])}</td></tr>"
            for k,v in equations["results"].items()
        )
        eq_html = f"<h2>Equation chain</h2><table><tr><th>Equation</th><th>Value</th><th>Symbol</th></tr>{rows}</table>"
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
    <title>SIS Universal Knowledge Synthesizer v25</title>
    <style>
    body{{font-family:Arial,Helvetica,sans-serif;background:#f6f8fb;color:#17202a;margin:0}}
    .wrap{{max-width:1400px;margin:auto;padding:32px}} h1,h2{{color:#1d3557}}
    .report{{background:#fff;padding:30px;border-radius:18px;box-shadow:0 6px 24px rgba(0,0,0,.06)}}
    .graph{{height:820px;background:#fff;border:1px solid #ddd;border-radius:18px}}
    table{{border-collapse:collapse;width:100%;margin-top:12px}} th,td{{border:1px solid #ddd;padding:8px;text-align:left}}
    </style></head><body><div class="wrap">
    <h1>SIS Universal Knowledge Synthesizer v25.0</h1>
    <div class="report">{report_text}</div>
    {score_html}{eq_html}
    <h2>Unified semantic system map — {html.escape(perspective.upper())}</h2>
    <div id="cy" class="graph"></div>
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.26.0/cytoscape.min.js"></script>
    <script>
    const elements={graph_json};
    cytoscape({{container:document.getElementById('cy'),elements:elements,
      style:[
        {{selector:'node',style:{{'label':'data(label)','background-color':'data(color)',
        'width':'data(size)','height':'data(size)','shape':'data(shape)','text-wrap':'wrap',
        'text-max-width':'90px','font-size':'11px','font-weight':'bold','text-valign':'center',
        'text-halign':'center','color':'#17202a','border-width':3,'border-color':'#fff'}}}},
        {{selector:'edge',style:{{'width':2,'line-color':'#adb5bd','target-arrow-color':'#adb5bd',
        'target-arrow-shape':'vee','curve-style':'bezier','label':'data(rel_type)','font-size':'8px'}}}}
      ],
      layout:{{name:'cose',fit:true,padding:70}}}});
    </script></body></html>"""

# -------------------------------------------------------------------------
# Sidebar
# -------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        f'<div class="sidebar-logo-container"><img src="data:image/svg+xml;base64,{get_svg_base64(SVG_3D_RELIEF)}" width="220"></div>',
        unsafe_allow_html=True
    )
    st.markdown(f'<div class="date-badge">{SYSTEM_DATE.upper()}</div>', unsafe_allow_html=True)
    st.header("⚙️ SYSTEM CONTROL")

    google_api_key = st.text_input(
        "Google Gemini API Key:", type="password",
        key="side_google_gemini_v250"
    )

    GOOGLE_MODELS = {
        "Gemini 3.8 Flash — latest": "gemini-3.8-flash",
        "Gemini 3.7 Flash — advanced": "gemini-3.7-flash",
        "Gemini 3.6 Flash": "gemini-3.6-flash",
        "Gemini 3.5 Flash": "gemini-3.5-flash",
        "Gemini 3.5 Flash-Lite": "gemini-3.5-flash-lite",
        "Gemini 3.1 Flash-Lite": "gemini-3.1-flash-lite",
        "Gemini 3.1 Pro Preview": "gemini-3.1-pro-preview",
        "Gemini 3 Flash Preview": "gemini-3-flash-preview",
        "Gemini 2.5 Pro": "gemini-2.5-pro",
        "Gemini 2.5 Flash": "gemini-2.5-flash",
        "Gemini 2.5 Flash-Lite": "gemini-2.5-flash-lite",
        "Gemma 4 31B IT": "gemma-4-31b-it",
        "Gemma 4 26B A4B IT": "gemma-4-26b-a4b-it",
    }

    p1_model_label = st.selectbox(
        "Phase 1 — IMA Foundation:", list(GOOGLE_MODELS.keys()),
        index=min(5, len(GOOGLE_MODELS)-1)
    )
    p2_model_label = st.selectbox(
        "Phase 2 — MA Innovation:", list(GOOGLE_MODELS.keys()),
        index=min(1, len(GOOGLE_MODELS)-1)
    )
    critic_model_label = st.selectbox(
        "Quality Critic / Refiner:", list(GOOGLE_MODELS.keys()),
        index=min(1, len(GOOGLE_MODELS)-1)
    )
    p1_model, p2_model, critic_model = (
        GOOGLE_MODELS[p1_model_label],
        GOOGLE_MODELS[p2_model_label],
        GOOGLE_MODELS[critic_model_label],
    )

    st.divider()
    st.subheader("🧠 ADAPTIVE QUALITY ENGINE")
    optimization_rounds = st.slider(
        "Refinement rounds:", 0, 2, 1,
        help="After independent scoring, the system can refine weak dimensions."
    )
    target_score = st.number_input(
        "Target overall score:", min_value=9.0, max_value=10.0,
        value=9.9, step=0.05
    )
    st.caption("Target dimensions: novelty · systemic architecture · interdisciplinarity · practicality · clarity")

    st.divider()
    st.subheader("🕸️ UNIFIED GRAPH")
    graph_perspective = st.selectbox(
        "Graph view:", ["organic", "hierarchical", "concentric", "circular", "grid"],
        index=0, format_func=lambda x: x.title()
    )
    graph_module = st.selectbox(
        "Organic module:", ["Unified", "Metamodel", "Mental Approach", "Science",
                            "Semantic", "Network", "Analytical", "Energetic", "Innovation"],
        index=0
    )
    graph_node_count = st.slider("Key nodes:", 15, 60, 40, 1)

    st.divider()
    st.subheader("🧮 EQUATION SYSTEM")
    explicit_calculation = st.checkbox(
        "Enable calculation for this inquiry",
        value=False,
        help="Off by default. Equations are calculated only when explicitly requested."
    )
    initial_energy = st.number_input("WI — initial energy", 1.0, 100000.0, 2500.0, 100.0)
    f_pf = st.number_input("FPF — positive factors", 0.001, 100.0, 0.70, 0.01)
    f_sf = st.number_input("FSF — stress factors", 0.0, 100.0, 0.40, 0.01)
    f_pr = st.number_input("FPR — prevalence", 0.0, 100.0, 0.30, 0.01)

    with st.expander("Advanced equation inputs", expanded=False):
        eq_N = st.number_input("N — total observations", 1.0, 1000000.0, 100.0, 1.0)
        eq_v = st.number_input("v — distinct observations", 0.0, 1000000.0, 25.0, 1.0)
        eq_fc = st.number_input("fc — category frequency", 0.0, 1000000.0, 20.0, 1.0)
        eq_sum_f2 = st.number_input("Σf² — category concentration numerator", 0.0, 1e12, 500.0, 10.0)
        eq_Pxy = st.number_input("Pxy — joint probability", 0.000001, 1.0, 0.05, 0.01, format="%.6f")
        eq_Px = st.number_input("Px — probability x", 0.000001, 1.0, 0.20, 0.01, format="%.6f")
        eq_Py = st.number_input("Py — probability y", 0.000001, 1.0, 0.20, 0.01, format="%.6f")
        eq_k = st.number_input("k — node degree", 0.0, 1000000.0, 5.0, 1.0)
        eq_n = st.number_input("n — graph nodes", 2.0, 100000.0, 20.0, 1.0)
        eq_E = st.number_input("E — graph edges", 0.0, 1000000.0, 30.0, 1.0)
        eq_BC = st.number_input("BC — betweenness centrality", 0.0, 1.0, 0.20, 0.01)
        eq_EC = st.number_input("EC — eigenvector centrality", 0.0, 1.0, 0.30, 0.01)
        eq_sum_AS = st.number_input("ΣAS — associative strengths", -1000000.0, 1000000.0, 4.0, 0.1)
        eq_sum_cij = st.number_input("Σcij — co-occurrences", 0.0, 1000000.0, 40.0, 1.0)

    st.divider()
    col_res, col_gui = st.columns(2)
    with col_res:
        if st.button("♻️ RESET", key="sidebar_reset_btn_v250"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    with col_gui:
        if st.button("📖 GUIDE", key="sidebar_guide_btn_v250"):
            st.session_state.show_user_guide = not st.session_state.get("show_user_guide", False)
            st.rerun()

# -------------------------------------------------------------------------
# Main UI
# -------------------------------------------------------------------------
st.markdown('<h1 class="main-header-gradient">🧱 SIS Universal Knowledge Synthesizer</h1>', unsafe_allow_html=True)
st.markdown(
    f"**Adaptive multi-stage architecture v25.0** | {SYSTEM_DATE} | "
    f"Optimization target: **{target_score:.2f}+ / 10.00**"
)

if st.session_state.get("show_user_guide"):
    st.info("""
    **v25 architecture:** IMA builds the structural knowledge foundation; MA transforms
    contradictions into innovations; an independent critic scores five dimensions; an
    adaptive refinement pass repairs weak dimensions. The graph is a single unified
    network spanning lexical, category, hierarchy, semantic, network, analytical and
    energetic layers plus IMA, MA, science and logical relations. The equation engine is
    opt-in and calculates only when explicitly requested.
    """)

col_ref1, col_ref2 = st.columns(2)
with col_ref1:
    st.markdown(
        '<div class="metamodel-box"><b>🏛️ IMA — Structural intelligence</b><br>'
        'Problem → context → hierarchy → evidence → system architecture → constraints.</div>',
        unsafe_allow_html=True
    )
with col_ref2:
    st.markdown(
        '<div class="mental-approach-box"><b>🧠 MA — Generative intelligence</b><br>'
        'Contradiction → mental approach → transformation → new configuration → innovation → effect.</div>',
        unsafe_allow_html=True
    )

st.markdown("### 🛠️ CONFIGURE SYNTHESIS")

r1c1, r1c2, r1c3 = st.columns([1.4, 2.2, 1])
with r1c1:
    target_authors = st.text_input("👤 Authors for ORCID Analysis:", placeholder="Optional")
with r1c2:
    sel_sciences = st.multiselect(
        "Science fields:",
        sorted(KNOWLEDGE_BASE["Science fields"].keys()),
        default=["Physics", "Psychology", "Sociology", "Computer Science", "Philosophy"]
    )
with r1c3:
    expertise = st.select_slider("Expertise:", ["Novice", "Intermediate", "Expert"], value="Expert")

r2c1, r2c2, r2c3 = st.columns(3)
with r2c1:
    sel_paradigms = st.multiselect(
        "Scientific paradigms:",
        list(KNOWLEDGE_BASE["Scientific paradigms"].keys()),
        default=["Systems Theory", "Holism", "Pragmatism", "Computational Paradigm"]
    )
with r2c2:
    sel_models = st.multiselect(
        "Structural models:",
        list(KNOWLEDGE_BASE["Structural models"].keys()),
        default=["Concepts", "Principles & Relations", "Causal Connections", "Generalizations"]
    )
with r2c3:
    goal_context = st.selectbox(
        "Strategic goal:",
        ["Scientific Research", "Problem Solving", "Educational", "Policy Making", "Innovation Design"]
    )

available_methods = sorted({
    method for science in sel_sciences
    for method in KNOWLEDGE_BASE["Science fields"].get(science, {}).get("methods", [])
})
available_tools = sorted({
    tool for science in sel_sciences
    for tool in KNOWLEDGE_BASE["Science fields"].get(science, {}).get("tools", [])
})

r3c1, r3c2 = st.columns(2)
with r3c1:
    sel_methods = st.multiselect("Methodology:", available_methods, default=available_methods)
with r3c2:
    sel_tools = st.multiselect("Tools:", available_tools, default=available_tools)

st.divider()
st.markdown("### 🧬 INNOVATION STRATEGY")
selected_techniques = st.multiselect(
    "Ideation frameworks:",
    list(IDEATION_TECHNIQUES.keys()),
    default=["First Principles", "TRIZ (Simplified)", "SCAMPER", "Lateral Thinking"]
)

st.divider()
col_inq1, col_inq2, col_inq3 = st.columns([2, 2, 1])
with col_inq1:
    user_query = st.text_area(
        "❓ STEP 1 — Research inquiry:",
        placeholder="Describe the knowledge problem, evidence or system to analyze.",
        height=220
    )
with col_inq2:
    idea_query = st.text_area(
        "💡 STEP 2 — Innovation objective:",
        placeholder="Describe what should become more novel, systemic, interdisciplinary and practical.",
        height=220
    )
with col_inq3:
    uploaded_file = st.file_uploader("📂 ATTACH TEXT DATA:", type=["txt"], key="final_file_uploader_v250")
    file_content = ""
    if uploaded_file is not None:
        try:
            file_content = uploaded_file.read().decode("utf-8")
            st.success(f"📎 {uploaded_file.name}")
            with st.expander("Preview"):
                st.text(file_content[:600] + ("..." if len(file_content) > 600 else ""))
        except Exception as exc:
            st.error(f"Error reading file: {exc}")

def google_generate(client, model_id, system_prompt, user_content, temperature, max_retries=4):
    """Robust Google GenAI gateway with transient-error retry."""
    if client is None:
        raise RuntimeError("Google client is not initialized.")
    kwargs = {"system_instruction": system_prompt, "temperature": temperature}
    if model_id.startswith("gemini-3"):
        try:
            kwargs["thinking_config"] = types.ThinkingConfig(thinking_level="medium")
        except Exception:
            pass
    config = types.GenerateContentConfig(**kwargs)
    last_exc = None
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=model_id, contents=user_content, config=config
            )
            text_out = getattr(response, "text", None)
            if text_out:
                return text_out
            return response.candidates[0].content.parts[0].text
        except Exception as exc:
            last_exc = exc
            s = str(exc)
            transient = any(code in s for code in ["503", "UNAVAILABLE", "429",
                                                    "RESOURCE_EXHAUSTED", "500", "INTERNAL"])
            if transient and attempt < max_retries - 1:
                wait = 2 ** attempt + 1
                st.toast(f"Google API retry {attempt+1}/{max_retries} in {wait}s")
                time.sleep(wait)
                continue
            raise
    raise RuntimeError(f"Google API unavailable: {last_exc}")

def evaluate_quality(client, model_id, synthesis, innovation, objective, target):
    prompt = f"""
You are the independent SIS Quality Auditor. Evaluate the proposed synthesis and
innovation architecture against EXACTLY five dimensions, each from 0.00 to 10.00:

1 conceptual_novelty
2 systemic_architecture
3 interdisciplinary_integration
4 practicality
5 clarity

Do not reward verbosity. Reward explicit mechanisms, non-obvious but defensible
conceptual combinations, coherent architecture, cross-field transfer, implementability,
and clear communication. Detect generic brainstorming, unsupported claims, logical gaps,
circular reasoning, and decorative graph concepts.

Target: {target:.2f}+.
Return JSON ONLY:
{{
  "scores": {{
    "conceptual_novelty": 0.0,
    "systemic_architecture": 0.0,
    "interdisciplinary_integration": 0.0,
    "practicality": 0.0,
    "clarity": 0.0
  }},
  "overall_score": 0.0,
  "strengths": [],
  "gaps": [],
  "repair_actions": []
}}

OBJECTIVE:
{objective}

IMA:
{synthesis}

MA INNOVATION:
{innovation}
"""
    raw = google_generate(client, model_id, prompt, objective, temperature=0.15)
    return extract_json_object(raw) or {}

def build_architecture_context():
    ima = "\n".join(
        f"- {n}: {d['desc']}" for n,d in HUMAN_THINKING_METAMODEL["nodes"].items()
    )
    ma = "\n".join(
        f"- {n}: {d['desc']}" for n,d in MENTAL_APPROACHES_ONTOLOGY["nodes"].items()
    )
    science = "\n".join(
        f"- {s}: {KNOWLEDGE_BASE['Science fields'][s]['cat']}; "
        f"methods={', '.join(KNOWLEDGE_BASE['Science fields'][s]['methods'][:4])}; "
        f"facets={', '.join(KNOWLEDGE_BASE['Science fields'][s]['facets'][:4])}"
        for s in sel_sciences if s in KNOWLEDGE_BASE["Science fields"]
    )
    return ima, ma, science

if st.button("🚀 EXECUTE ADAPTIVE SIS SYNTHESIS", use_container_width=True, key="exec_pipeline_v250"):
    if not google_api_key:
        st.error("❌ Google Gemini API key is required.")
    elif not user_query:
        st.warning("⚠️ Research inquiry is required.")
    elif not selected_techniques:
        st.warning("⚠️ Select at least one innovation framework.")
    else:
        try:
            ima_defs, ma_defs, science_defs = build_architecture_context()
            file_context = f"\nSOURCE FILE:\n{file_content}" if file_content else ""
            biblio_data = fetch_author_bibliographies(target_authors) if target_authors else ""

            base_context = f"""
SIS v25 ARCHITECTURE KERNEL
IMA:
{ima_defs}

MENTAL APPROACHES:
{ma_defs}

SCIENCE FIELDS:
{science_defs}

HIERARCHICAL LEVELS:
{json.dumps(HIERARCHOLOGY_ONTOLOGY['hierarchical_levels'], ensure_ascii=False, indent=2)}

SCIENTIFIC PARADIGMS:
{', '.join(sel_paradigms)}

STRUCTURAL MODELS:
{', '.join(sel_models)}

METHODS:
{', '.join(sel_methods)}

TOOLS:
{', '.join(sel_tools)}

INNOVATION FRAMEWORKS:
{', '.join(selected_techniques)}

EXPERTISE:
{expertise}

GOAL:
{goal_context}
"""

            client = genai.Client(api_key=google_api_key)

            phase1_prompt = f"""
You are the SIS Lead Hierarchologist and systems architect.

Build a high-information IMA foundation. The purpose is NOT to brainstorm. Reconstruct
the problem as a system of concepts, actors, mechanisms, constraints, levels and evidence.

Mandatory quality architecture:
- distinguish evidence from inference;
- identify causal and structural dependencies;
- use Macro–Meso–Micro where justified;
- integrate selected scientific paradigms, explicitly including Holism when relevant;
- expose contradictions and bottlenecks;
- identify what must change for an innovation to be meaningful;
- identify transferable principles across disciplines;
- end with a compact "Innovation Opportunity Matrix".

Do not invent unsupported facts or named theories.

{base_context}
"""
            with st.spinner(f"PHASE 1 — IMA with {p1_model_label}"):
                phase1 = google_generate(
                    client, p1_model, phase1_prompt,
                    f"{base_context}\nRESEARCH INQUIRY:\n{user_query}{file_context}",
                    temperature=0.35
                )

            phase2_prompt = f"""
You are the SIS Strategic Innovation Architect.

Transform the IMA foundation into 4–6 high-value innovations. Avoid generic ideas.
Every innovation must follow this chain:

IMA finding
→ bottleneck / contradiction
→ selected Mental Approach
→ transformation operation
→ changed system architecture
→ innovation
→ interdisciplinary transfer
→ practical implementation
→ test / falsification condition
→ expected benefit

Optimize for the five dimensions:
conceptual novelty, systemic architecture, interdisciplinary integration, practicality,
clarity.

The final graph must be ONE network, not separate graphs. Use only key nodes and key
relations. Relations may come from ISO-thesaurus-style TT/BT/NT/RT/EQ/AS/IN, UML
Generalization/Specialization/Composition/Aggregation/Dependency/Realization/Containment,
and logical AND/OR/XOR/NOT/IF-THEN.

Use node fields: id, label, shape, color, description, layer, module, importance.
Use edge fields: source, target, rel_type, weight, evidence.

Required layers when semantically relevant:
Lexical, Category, Hierarchy, Semantic, Network, Analytical, Energetic,
Metamodel, Mental Approach, Science, Innovation, Logic, Equation.

Return a readable report followed by:
### SEMANTIC_GRAPH_JSON
Then JSON only.

Graph limits: {graph_node_count} nodes maximum, 80 edges maximum.
No duplicate edges, no orphan edges, no decorative bridges.
{base_context}
"""
            with st.spinner(f"PHASE 2 — MA innovation with {p2_model_label}"):
                phase2_raw = google_generate(
                    client, p2_model, phase2_prompt,
                    f"IMA FOUNDATION:\n{phase1}\n\nINNOVATION OBJECTIVE:\n{idea_query}{file_context}",
                    temperature=0.80
                )
            innovation_text, graph_data = parse_graph_payload(phase2_raw)
            graph_data = normalize_graph(graph_data, max_nodes=graph_node_count, max_edges=80)

            # Independent audit
            with st.spinner(f"QUALITY AUDIT — {critic_model_label}"):
                evaluation = evaluate_quality(
                    client, critic_model, phase1, innovation_text,
                    idea_query or user_query, target_score
                )

            # Adaptive repair loop
            for round_no in range(optimization_rounds):
                overall = evaluation.get("overall_score")
                if isinstance(overall, (int, float)) and overall >= target_score:
                    break

                repair_actions = evaluation.get("repair_actions", [])
                repair_prompt = f"""
You are the SIS Senior Refinement Architect.

Improve the existing synthesis ONLY where the audit identifies weaknesses.
Do not merely rewrite. Perform structural repair.

AUDIT:
{json.dumps(evaluation, ensure_ascii=False, indent=2)}

CURRENT IMA:
{phase1}

CURRENT INNOVATION:
{innovation_text}

OBJECTIVE:
{idea_query or user_query}

Return:
1. Revised synthesis/innovation report.
2. A single unified graph in the exact marker format:
### SEMANTIC_GRAPH_JSON
{{"nodes":[...],"edges":[...],"system_metrics":{{}}}}

Every innovation must remain traceable to an IMA finding and an MA transformation.
Increase novelty without sacrificing feasibility. Increase interdisciplinarity by
showing explicit mechanism transfer, not by listing disciplines.
Increase systemic architecture by showing dependencies, feedbacks, constraints and
logical conditions.
Increase clarity by removing redundancy.
"""
                with st.spinner(f"ADAPTIVE REFINEMENT ROUND {round_no+1}"):
                    refined_raw = google_generate(
                        client, critic_model, repair_prompt,
                        f"REPAIR ACTIONS:\n{json.dumps(repair_actions, ensure_ascii=False)}",
                        temperature=0.55
                    )
                refined_text, refined_graph = parse_graph_payload(refined_raw)
                if refined_text.strip():
                    innovation_text = refined_text
                if refined_graph.get("nodes"):
                    graph_data = normalize_graph(
                        refined_graph, max_nodes=graph_node_count, max_edges=80
                    )
                with st.spinner(f"RE-AUDIT ROUND {round_no+1}"):
                    evaluation = evaluate_quality(
                        client, critic_model, phase1, innovation_text,
                        idea_query or user_query, target_score
                    )

            # Optional equation engine
            equations = None
            calc_active = calculation_requested(user_query, idea_query, explicit_calculation)
            if calc_active:
                equations = calculate_equation_chain({
                    "WI": initial_energy,
                    "FPF": f_pf,
                    "FSF": f_sf,
                    "FPR": f_pr,
                    "base": 2,
                    "N": eq_N,
                    "v": eq_v,
                    "fc": eq_fc,
                    "sum_f2": eq_sum_f2,
                    "Pxy": eq_Pxy,
                    "Px": eq_Px,
                    "Py": eq_Py,
                    "k": eq_k,
                    "n": eq_n,
                    "E": eq_E,
                    "BC": eq_BC,
                    "EC": eq_EC,
                    "sum_AS": eq_sum_AS,
                    "sum_cij": eq_sum_cij,
                })

            # Add equation backbone only when calculation was explicitly requested.
            if equations and equations.get("results"):
                eq_nodes = []
                existing_ids = {n["id"] for n in graph_data["nodes"]}
                last_id = len(existing_ids) + 1
                previous = None
                for eq_name, spec in EQUATION_SYSTEM.items():
                    if eq_name not in equations["results"]:
                        continue
                    nid = f"eq{last_id}"
                    while nid in existing_ids:
                        last_id += 1
                        nid = f"eq{last_id}"
                    existing_ids.add(nid)
                    eq_nodes.append({
                        "id": nid,
                        "label": f"{spec['symbol']} — {eq_name}",
                        "shape": "rectangle",
                        "color": GRAPH_LAYER_COLORS.get("Equation", "#f08c00"),
                        "description": f"{spec['formula']} | {spec['description']}",
                        "layer": "Equation",
                        "module": "Equation",
                        "importance": 0.72,
                    })
                    if previous:
                        graph_data["edges"].append({
                            "id": f"eqe{last_id}",
                            "source": previous,
                            "target": nid,
                            "rel_type": "Dependency",
                            "weight": 0.85,
                            "label": "feeds",
                            "evidence": "Connected equation chain",
                        })
                    previous = nid
                    last_id += 1
                graph_data["nodes"].extend(eq_nodes)
                graph_data = normalize_graph(graph_data, max_nodes=graph_node_count, max_edges=80)

            final_elements = graph_to_cytoscape(graph_data)
            st.session_state.final_graph_elements = final_elements
            st.session_state.final_graph_data = graph_data
            st.session_state.report_ready = True
            st.session_state.last_evaluation = evaluation
            st.session_state.last_equations = equations

            # -----------------------------------------------------------------
            # Report
            # -----------------------------------------------------------------
            st.divider()
            st.subheader("🧠 ADAPTIVE SIS SYNTHESIS REPORT")
            score = evaluation.get("overall_score")
            if isinstance(score, (int, float)):
                if score >= target_score:
                    st.success(f"🎯 Optimization target reached: {score:.2f} / 10.00")
                else:
                    st.warning(f"Optimization target not yet reached: {score:.2f} / 10.00")
            else:
                st.info("Quality auditor did not return a valid numeric overall score.")

            scores = evaluation.get("scores", {})
            if scores:
                metric_cols = st.columns(5)
                for col, dim in zip(metric_cols, QUALITY_DIMENSIONS):
                    val = scores.get(dim)
                    col.metric(dim.replace("_", " ").title(), f"{float(val):.2f}" if isinstance(val,(int,float)) else "—")

            with st.expander("🔎 Audit strengths, gaps and repair actions", expanded=False):
                st.write("**Strengths**")
                st.write(evaluation.get("strengths", []))
                st.write("**Gaps**")
                st.write(evaluation.get("gaps", []))
                st.write("**Repair actions**")
                st.write(evaluation.get("repair_actions", []))

            st.markdown(
                f"### Phase 1 — IMA Structural Foundation ({p1_model_label})\n\n{phase1}"
            )
            st.markdown(
                f"### Phase 2 — MA Innovation Architecture ({p2_model_label})\n\n{innovation_text}"
            )

            if biblio_data:
                with st.expander("📚 AUTHOR RESEARCH BACKGROUND"):
                    st.markdown(biblio_data)

            if equations and equations.get("results"):
                st.divider()
                st.subheader("🧮 CONNECTED EQUATION CALCULATION")
                st.caption("Calculation was activated explicitly for this inquiry.")
                eq_rows = []
                for name, value in equations["results"].items():
                    eq_rows.append({
                        "Equation": name,
                        "Symbol": EQUATION_SYSTEM[name]["symbol"],
                        "Formula": EQUATION_SYSTEM[name]["formula"],
                        "Value": round(value, 8),
                        "Layer": EQUATION_SYSTEM[name]["layer"],
                    })
                st.dataframe(eq_rows, use_container_width=True, hide_index=True)

            st.divider()
            st.subheader(
                f"🕸️ UNIFIED HIERARCHOGRAPHIC NETWORK — {graph_perspective.upper()} / {graph_module.upper()}"
            )

            visible_elements = final_elements
            if graph_module != "Unified":
                allowed = {graph_module}
                visible_node_ids = {
                    e["data"]["id"] for e in final_elements
                    if "source" not in e["data"] and e["data"].get("module") == graph_module
                }
                # For a module view, keep direct neighbors to preserve structural readability.
                neighbor_ids = set(visible_node_ids)
                for e in final_elements:
                    d = e["data"]
                    if "source" in d and (d.get("source") in visible_node_ids or d.get("target") in visible_node_ids):
                        neighbor_ids.update([d.get("source"), d.get("target")])
                visible_elements = [
                    e for e in final_elements
                    if ("source" not in e["data"] and e["data"]["id"] in neighbor_ids)
                    or ("source" in e["data"] and e["data"].get("source") in neighbor_ids and e["data"].get("target") in neighbor_ids)
                ]

            render_cytoscape_network(
                visible_elements, graph_perspective,
                f"cy_{int(time.time()*1000)}",
                "Unified cross-layer semantic network"
            )

            export_html = build_html_report(
                f"<h2>Phase 1 — IMA</h2>{html.escape(phase1).replace(chr(10), '<br>')}"
                f"<h2>Phase 2 — MA</h2>{html.escape(innovation_text).replace(chr(10), '<br>')}",
                final_elements, graph_perspective, evaluation, equations
            )
            st.download_button(
                "🌐 EXPORT COMPLETE REPORT + UNIFIED GRAPH (HTML)",
                data=export_html,
                file_name=f"SIS_v25_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                mime="text/html",
                use_container_width=True,
                key="export_complete_html_v250"
            )

        except Exception as exc:
            st.error(f"❌ Pipeline Failure: {exc}")
            st.exception(exc)

# -------------------------------------------------------------------------
# Persistent gallery
# -------------------------------------------------------------------------
if st.session_state.get("report_ready") and st.session_state.get("final_graph_elements"):
    st.divider()
    st.subheader("🖼️ MODULAR GRAPH GALLERY")
    gallery_tabs = st.tabs(["🌐 Unified Organic", "🏛️ IMA", "🧠 MA", "🔬 Science", "🧮 Equations"])
    graph_all = st.session_state.final_graph_elements

    with gallery_tabs[0]:
        render_cytoscape_network(graph_all, "organic", "gallery_unified_v250", "Unified Organic View")
    with gallery_tabs[1]:
        ids = {e["data"]["id"] for e in graph_all if "source" not in e["data"] and e["data"].get("module") == "Metamodel"}
        els = [e for e in graph_all if ("source" not in e["data"] and e["data"]["id"] in ids) or
               ("source" in e["data"] and e["data"].get("source") in ids and e["data"].get("target") in ids)]
        render_cytoscape_network(els or graph_all, "hierarchical", "gallery_ima_v250", "IMA Module")
    with gallery_tabs[2]:
        ids = {e["data"]["id"] for e in graph_all if "source" not in e["data"] and e["data"].get("module") == "Mental Approach"}
        els = [e for e in graph_all if ("source" not in e["data"] and e["data"]["id"] in ids) or
               ("source" in e["data"] and e["data"].get("source") in ids and e["data"].get("target") in ids)]
        render_cytoscape_network(els or graph_all, "organic", "gallery_ma_v250", "Mental Approach Module")
    with gallery_tabs[3]:
        ids = {e["data"]["id"] for e in graph_all if "source" not in e["data"] and e["data"].get("module") == "Science"}
        els = [e for e in graph_all if ("source" not in e["data"] and e["data"]["id"] in ids) or
               ("source" in e["data"] and e["data"].get("source") in ids and e["data"].get("target") in ids)]
        render_cytoscape_network(els or graph_all, "concentric", "gallery_science_v250", "Science Integration Module")
    with gallery_tabs[4]:
        eqs = st.session_state.get("last_equations")
        if eqs and eqs.get("results"):
            st.dataframe([
                {"Equation": k, "Symbol": EQUATION_SYSTEM[k]["symbol"],
                 "Formula": EQUATION_SYSTEM[k]["formula"], "Value": round(v, 8)}
                for k,v in eqs["results"].items()
            ], use_container_width=True, hide_index=True)
        else:
            st.info("No equation calculation was explicitly requested in the last run.")

st.divider()
st.caption(
    f"SIS Universal Knowledge Synthesizer | {VERSION_CODE} | "
    f"Adaptive target {TARGET_SCORE:.2f}+ | Unified semantic + logical + equation architecture"
)
