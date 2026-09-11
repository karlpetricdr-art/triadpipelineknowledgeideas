import streamlit as st
import json
import base64
import requests
import urllib.parse
import re
import time
import html
from datetime import datetime
from google import genai
from google.genai import types as genai_types
import streamlit.components.v1 as components


# =============================================================================
# SIS UNIVERSAL KNOWLEDGE SYNTHESIZER
# Multidimensional Thesaurus + Polyhierarchical Ontology + UML +
# Hierarchical-Associative Logic + Operational Logic + Hierarchography
# =============================================================================

SYSTEM_DATE = datetime.now().strftime("%B %d, %Y")
VERSION_CODE = "v24.0.0-IMA-MA-TWO-PHASE-PRO"

# =============================================================================
# MODEL CATALOG
# =============================================================================

GEMINI_MODEL_CATALOG = {
    "Gemini 3.6 Flash (najnovejši, agentni)": "gemini-3.6-flash",
    "Gemini 3.5 Flash (vsestranski)": "gemini-3.5-flash",
    "Gemini 3.5 Flash-Lite (najhitrejši)": "gemini-3.5-flash-lite",
    "Gemini 3.1 Flash-Lite": "gemini-3.1-flash-lite",
    "Gemini 3.1 Pro Preview": "gemini-3.1-pro-preview",
    "Gemma 4 31B": "gemma-4-31b-it",
    "Gemma 4 26B A4B": "gemma-4-26b-a4b-it",
    "Hugging Face – Qwen2.5-72B-Instruct": "hf:Qwen/Qwen2.5-72B-Instruct",
}

GEMINI_MODEL_LABELS = list(GEMINI_MODEL_CATALOG.keys())
HF_ROUTER_URL = "https://router.huggingface.co/v1/chat/completions"


# =============================================================================
# SESSION STATE
# =============================================================================

DEFAULT_SESSION = {
    "show_user_guide": False,
    "groq_synthesis": "",
    "gemini_innovation": "",
    "final_graph_elements": [],
    "report_ready": False,
    "last_graph_data": {},
    "phase1_graph_data": {},
    "phase2_graph_data": {},
    "phase1_report": "",
    "phase2_report": "",
    "integrated_report": "",
    "selected_graph_components": [
        "Innovations",
        "Science Fields",
        "Scientific Paradigms",
        "Structural Models",
        "Human Thinking Metamodel",
        "Mental Approaches",
        "Processes",
        "Goals / Vision",
        "Constraints / Rules",
        "Entities",
        "Facts / Concepts",
        "System States",
        "Data / Evidence",
    ],
}

for key, value in DEFAULT_SESSION.items():
    if key not in st.session_state:
        st.session_state[key] = value


st.set_page_config(
    page_title=f"SIS Universal Knowledge Synthesizer - {SYSTEM_DATE}",
    page_icon="🌳",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =============================================================================
# CSS
# =============================================================================

st.markdown(
    """
<style>
[data-testid="stSidebar"] {
    background-color:#151b24 !important;
    border-right:2px solid #566273 !important;
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] .stCaption,
[data-testid="stSidebar"] .stTextInput,
[data-testid="stSidebar"] .stSelectbox,
[data-testid="stSidebar"] .stMultiSelect,
[data-testid="stSidebar"] .stLinkButton,
[data-testid="stSidebar"] .stSlider,
[data-testid="stSidebar"] .stExpander {
    color:#ffffff !important;
}
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] textarea {
    color:#ffffff !important;
    background:#0d1219 !important;
    border:1px solid #718096 !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] > div {
    color:#ffffff !important;
    background:#0d1219 !important;
    border-color:#718096 !important;
}
[data-testid="stSidebar"] [data-baseweb="tag"] {
    color:#ffffff !important;
    background:#263241 !important;
}
[data-testid="stSidebar"] [data-testid="stSlider"] label,
[data-testid="stSidebar"] [data-testid="stSlider"] div {
    color:#ffffff !important;
}
[data-testid="stSidebar"] .stButton button, 
[data-testid="stSidebar"] .stLinkButton a {
    color: #ffffff !important;
    background-color: #263241 !important;
    border: 1px solid #718096 !important;
    font-weight: 800 !important;
    text-decoration: none !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}
[data-testid="stSidebar"] .stLinkButton a p {
    color: #ffffff !important;
}
[data-testid="stSidebar"] .stButton button:hover, 
[data-testid="stSidebar"] .stLinkButton a:hover {
    background-color: #3a4a5f !important;
    border-color: #a8b4c2 !important;
}
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] .stMarkdown li,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stExpander p,
[data-testid="stSidebar"] .stExpander li,
[data-testid="stSidebar"] .stMarkdown span,
[data-testid="stSidebar"] .stMarkdown div {
    color:#ffffff !important;
    opacity:1 !important;
}
[data-testid="stSidebar"] button {
    color:#ffffff !important;
}
.stExpander {
    background-color:#303947 !important;
    border:1px solid #485463 !important;
    border-radius:12px !important;
    margin-bottom:10px !important;
}
.stExpander details summary p {
    color:#ffffff !important;
    font-weight:800 !important;
}
.main-header-gradient {
    background:linear-gradient(90deg,#1d3557,#457b9d);
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
    font-weight:800;
    font-size:2.8rem;
}
.date-badge {
    background:#1d3557;
    color:#ffffff;
    padding:12px 20px;
    border-radius:50px;
    font-size:1em;
    font-weight:800;
    margin-bottom:25px;
    display:block;
    text-align:center;
    box-shadow:0 4px 15px rgba(29,53,87,.3);
}
.sidebar-logo-container {
    display:flex;
    justify-content:center;
    padding:10px 0;
}
.metamodel-box,
.ontology-box,
.operational-box,
.hierarchography-box {
    padding:24px;
    border-radius:15px;
    margin-bottom:20px;
    box-shadow:0 4px 12px rgba(0,0,0,.06);
}
.metamodel-box {
    background:#f4f8fb;
    border-left:8px solid #00b0f0;
}
.ontology-box {
    background:#f6f4ff;
    border-left:8px solid #7b2cb1;
}
.operational-box {
    background:#f4fff7;
    border-left:8px solid #2a9d8f;
}
.hierarchography-box {
    background:#fff9ed;
    border-left:8px solid #f4a261;
}
.semantic-node-highlight {
    color:#007f73;
    font-weight:bold;
    border-bottom:2px solid #2a9d8f;
    padding:0 2px;
    background:#effcf9;
    border-radius:4px;
    text-decoration:none !important;
}
.semantic-node-highlight:hover {
    background:#ccfbf1;
}
.stButton>button {
    width:100%;
    border-radius:10px;
    font-weight:800;
    transition:.2s;
    border:1px solid #718096;
}
.graph-legend {
    font-size:.82em;
    color:#333;
    background:#fff;
    padding:18px 24px;
    border-radius:15px;
    border:1px solid #e9ecef;
    margin-top:25px;
}
</style>
""",
    unsafe_allow_html=True,
)


# =============================================================================
# LOGO
# =============================================================================

def get_svg_base64(svg_str):
    return base64.b64encode(svg_str.encode("utf-8")).decode("utf-8")


SVG_3D_RELIEF = """
<svg width="240" height="240" viewBox="0 0 240 240"
xmlns="http://www.w3.org/2000/svg">
<defs>
<filter id="shadow" x="-20%" y="-20%" width="150%" height="150%">
<feDropShadow dx="4" dy="4" stdDeviation="3"
flood-color="#000" flood-opacity=".4"/>
</filter>
<linearGradient id="pyramid" x1="0%" y1="0%" x2="100%" y2="100%">
<stop offset="0%" stop-color="#e0e0e0"/>
<stop offset="100%" stop-color="#bdbdbd"/>
</linearGradient>
<linearGradient id="tree" x1="0%" y1="0%" x2="0%" y2="100%">
<stop offset="0%" stop-color="#66bb6a"/>
<stop offset="100%" stop-color="#2e7d32"/>
</linearGradient>
</defs>
<circle cx="120" cy="120" r="100" fill="#f0f0f0"
stroke="#000" stroke-width="4" filter="url(#shadow)"/>
<path d="M120 40L50 180L120 200Z" fill="url(#pyramid)"/>
<path d="M120 40L190 180L120 200Z" fill="#9e9e9e"/>
<rect x="116" y="110" width="8" height="70" rx="2" fill="#5d4037"/>
<circle cx="120" cy="85" r="30" fill="url(#tree)" filter="url(#shadow)"/>
<circle cx="95" cy="125" r="22" fill="#43a047" filter="url(#shadow)"/>
<circle cx="145" cy="125" r="22" fill="#43a047" filter="url(#shadow)"/>
<rect x="70" y="170" width="20" height="12" rx="2" fill="#1565c0"/>
<rect x="150" y="170" width="20" height="12" rx="2" fill="#c62828"/>
<rect x="110" y="185" width="20" height="12" rx="2" fill="#f9a825"/>
</svg>
"""


# =============================================================================
# HIERARCHICAL / ASSOCIATIVE / OPERATIONAL RELATION VOCABULARY
# =============================================================================

RELATION_DEFINITIONS = {
    "TT": "Top Term — root concept of a domain.",
    "BT": "Broader Term — hierarchical superordinate concept.",
    "NT": "Narrower Term — hierarchical subordinate concept.",
    "RT": "Related Term — lateral semantic association.",
    "EQ": "Equivalence — synonymous or conceptually equivalent term.",
    "AS": "Associative — functional or contextual association.",
    "IN": "Instance — category-to-instance relation.",
    "Generalization": "Generalization / inheritance.",
    "Specialization": "Specialization / deductive narrowing.",
    "Composition": "Strong whole-part relation.",
    "Aggregation": "Weak whole-part relation.",
    "Containment": "Structural containment.",
    "Realization": "Implementation of an abstract specification.",
    "Dependency": "Operational dependency.",
    "Conflict": "Systemic incompatibility or tension.",
    "AND": "Conjunctive synthesis.",
    "OR": "Alternative path.",
    "XOR": "Exclusive alternative.",
    "NOT": "Negation or prohibition.",
    "IF-THEN": "Conditional transformation.",
    "CAUSES": "Causal transformation.",
    "ENABLES": "Enabling relation.",
    "TRANSFORMS": "Transformation from one system state to another.",
    "PRODUCES": "Operational production.",
    "CONSUMES": "Operational consumption.",
    "FEEDS": "Input into another operation.",
    "FEEDBACK": "Feedback loop.",
    "POSITIVE-FEEDBACK": "Amplifying feedback.",
    "NEGATIVE-FEEDBACK": "Balancing feedback.",
    "TRIGGERS": "Event activation.",
    "PRECEDES": "Temporal/process precedence.",
    "CONSTRAINS": "Operational constraint.",
    "MEASURES": "Measurement relation.",
    "VALIDATES": "Validation relation.",
}


RELATION_COLORS = {
    "TT": "#14213d",
    "BT": "#1d3557",
    "NT": "#457b9d",
    "RT": "#2a9d8f",
    "EQ": "#f1c40f",
    "AS": "#7b2cb1",
    "IN": "#0077b6",
    "Generalization": "#e63946",
    "Specialization": "#111111",
    "Composition": "#d62828",
    "Aggregation": "#f77f00",
    "Containment": "#1d3557",
    "Realization": "#e63946",
    "Dependency": "#6c757d",
    "Conflict": "#b91d1d",
    "AND": "#008000",
    "OR": "#00a6d6",
    "XOR": "#ff8c00",
    "NOT": "#ff0000",
    "IF-THEN": "#d4a900",
    "CAUSES": "#c1121f",
    "ENABLES": "#2a9d8f",
    "TRANSFORMS": "#8a2be2",
    "PRODUCES": "#218739",
    "CONSUMES": "#9b2226",
    "FEEDS": "#0077b6",
    "FEEDBACK": "#6a4c93",
    "POSITIVE-FEEDBACK": "#008000",
    "NEGATIVE-FEEDBACK": "#c77d00",
    "TRIGGERS": "#e76f51",
    "PRECEDES": "#577590",
    "CONSTRAINS": "#6c757d",
    "MEASURES": "#118ab2",
    "VALIDATES": "#06a77d",
}


# =============================================================================
# NODE GEOMETRY
# =============================================================================

NODE_GEOMETRY = {
    "star": {
        "size": 135,
        "color": "#ffd166",
        "layer": "goal",
        "description": "Goal / macro-vision",
    },
    "hexagon": {
        "size": 115,
        "color": "#118ab2",
        "layer": "domain",
        "description": "Science field / domain",
    },
    "diamond": {
        "size": 120,
        "color": "#f4a261",
        "layer": "innovation",
        "description": "Innovation / transformation",
    },
    "triangle": {
        "size": 105,
        "color": "#2a9d8f",
        "layer": "process",
        "description": "Process / method / operation",
    },
    "octagon": {
        "size": 110,
        "color": "#e9c46a",
        "layer": "constraint",
        "description": "Rule / ethical boundary / constraint",
    },
    "ellipse": {
        "size": 100,
        "color": "#90be6d",
        "layer": "entity",
        "description": "Human / identity / biological entity",
    },
    "rectangle": {
        "size": 90,
        "color": "#dbe7f3",
        "layer": "fact",
        "description": "Fact / concept / micro-component",
    },
    "round-rectangle": {
        "size": 95,
        "color": "#cdb4db",
        "layer": "state",
        "description": "System state",
    },
    "barrel": {
        "size": 100,
        "color": "#adb5bd",
        "layer": "data",
        "description": "Data / evidence",
    },
}


VALID_SHAPES = set(NODE_GEOMETRY.keys())


# =============================================================================
# MULTIDIMENSIONAL THESAURUS
# =============================================================================

THESAURUS_ONTOLOGY = {
    "dimensions": {
        "semantic": [
            "concept",
            "term",
            "definition",
            "synonym",
            "equivalence",
        ],
        "hierarchical": [
            "top-term",
            "broader-term",
            "narrower-term",
            "whole",
            "part",
        ],
        "associative": [
            "related-term",
            "cause",
            "effect",
            "function",
            "context",
            "analogy",
            "contrast",
        ],
        "operational": [
            "input",
            "process",
            "transformation",
            "output",
            "feedback",
            "state",
        ],
        "epistemic": [
            "fact",
            "hypothesis",
            "model",
            "principle",
            "theory",
            "evidence",
        ],
        "temporal": [
            "precondition",
            "event",
            "transition",
            "sequence",
            "cycle",
        ],
        "systemic": [
            "micro",
            "meso",
            "macro",
            "boundary",
            "environment",
            "agent",
        ],
    },
    "relations": RELATION_DEFINITIONS,
}


# =============================================================================
# POLYHIERARCHICAL ONTOLOGY
# =============================================================================

POLYHIERARCHY = {
    "levels": {
        "Macro": "Universal, societal, scientific or strategic level.",
        "Meso": "Organizational, disciplinary or subsystem level.",
        "Micro": "Concrete entity, instance, process or observation level.",
    },
    "hierarchies": [
        {
            "id": "H1",
            "name": "Taxonomic hierarchy",
            "root": "Knowledge Domain",
            "relations": ["TT", "BT", "NT", "IN"],
        },
        {
            "id": "H2",
            "name": "Part-whole hierarchy",
            "root": "System",
            "relations": ["Composition", "Aggregation", "Containment"],
        },
        {
            "id": "H3",
            "name": "Operational hierarchy",
            "root": "System Process",
            "relations": [
                "PRECEDES",
                "CAUSES",
                "TRANSFORMS",
                "PRODUCES",
                "FEEDS",
            ],
        },
        {
            "id": "H4",
            "name": "Epistemic hierarchy",
            "root": "Knowledge",
            "relations": [
                "Evidence",
                "Fact",
                "Concept",
                "Model",
                "Theory",
                "Principle",
            ],
        },
        {
            "id": "H5",
            "name": "Decision hierarchy",
            "root": "Goal",
            "relations": [
                "CONSTRAINS",
                "IF-THEN",
                "AND",
                "OR",
                "XOR",
                "NOT",
            ],
        },
    ],
}


# =============================================================================
# UML METAMODEL
# =============================================================================

UML_METAMODEL = {
    "classes": {
        "Entity": ["identity", "properties", "state"],
        "Concept": ["definition", "domain", "scope"],
        "Goal": ["desired_state", "criterion"],
        "Problem": ["current_state", "target_state", "gap"],
        "Process": ["input", "operation", "output"],
        "Rule": ["condition", "constraint", "consequence"],
        "Innovation": ["novelty", "mechanism", "impact"],
        "Evidence": ["source", "strength", "validity"],
        "SystemState": ["state_id", "conditions", "transition"],
    },
    "relationships": {
        "Generalization": "is-a",
        "Specialization": "specialized-from",
        "Composition": "strong-part-of",
        "Aggregation": "weak-part-of",
        "Containment": "contains",
        "Realization": "implements",
        "Dependency": "requires",
        "Conflict": "conflicts-with",
    },
}


# =============================================================================
# HIERARCHOLOGY / HIERARCHOGRAPHY
# =============================================================================

HIERARCHOLOGY_ONTOLOGY = {
    "core_definitions": {
        "Hierarchology": (
            "Interdisciplinary study of hierarchical associative systems "
            "across Micro, Meso and Macro levels."
        ),
        "Hierarchography": (
            "Visual and structural description of hierarchical-associative "
            "systems through graphs, workflows, trees, UML and network forms."
        ),
        "Hierarchical Associative System": (
            "A system in which vertical hierarchy and lateral association "
            "operate simultaneously."
        ),
        "Polyhierarchy": (
            "A knowledge structure in which a concept may have more than one "
            "legitimate broader parent depending on semantic context."
        ),
        "Scientific Cage": (
            "A conceptual boundary produced when an established paradigm "
            "prevents alternative associations or transformations."
        ),
    },
    "levels": {
        "Macro": "Universal, strategic, societal or theoretical level.",
        "Meso": "Disciplinary, organizational or subsystem level.",
        "Micro": "Concrete entities, observations, methods and instances.",
    },
    "operational_logic": {
        "Internal": (
            "Inductive movement from observations and micro-components toward "
            "patterns, concepts and models."
        ),
        "External": (
            "Deductive and dialectical movement from models and principles "
            "toward concrete applications and transformations."
        ),
        "Transformational": (
            "A state-transition logic connecting input, operation, output "
            "and feedback."
        ),
        "Associative": (
            "Non-linear lateral movement between concepts sharing context, "
            "function, contrast, analogy or causal relevance."
        ),
    },
    "visual_methods": [
        "Polyhierarchical tree",
        "Hierarchograph",
        "UML metamodel",
        "Semantic network",
        "Operational flow",
        "State-transition graph",
        "Feedback loop",
        "Knowledge lattice",
        "Concept map",
        "Oligograph",
    ],
}


# =============================================================================
# HUMAN THINKING METAMODEL
# =============================================================================

HUMAN_THINKING_METAMODEL = {
    "nodes": {
        "Human mental concentration": {
            "color": "#adb5bd",
            "shape": "ellipse",
            "desc": "Foundational cognitive focus.",
        },
        "Identity": {
            "color": "#90be6d",
            "shape": "ellipse",
            "desc": "Identity and perspective of the cognitive agent.",
        },
        "Autobiographical memory": {
            "color": "#90be6d",
            "shape": "ellipse",
            "desc": "Historical experience influencing current reasoning.",
        },
        "Mission": {
            "color": "#92d050",
            "shape": "star",
            "desc": "High-level imperative.",
        },
        "Vision": {
            "color": "#ffd166",
            "shape": "star",
            "desc": "Desired future system state.",
        },
        "Goal": {
            "color": "#00b0f0",
            "shape": "star",
            "desc": "Operationalized desired outcome.",
        },
        "Problem": {
            "color": "#f2dcdb",
            "shape": "octagon",
            "desc": "Gap between current and desired state.",
        },
        "Ethics/moral": {
            "color": "#ffc000",
            "shape": "octagon",
            "desc": "Normative boundary.",
        },
        "Rule": {
            "color": "#f2f2f2",
            "shape": "octagon",
            "desc": "Constraint or governing rule.",
        },
        "Decision-making": {
            "color": "#ffff99",
            "shape": "triangle",
            "desc": "Selection among alternatives.",
        },
        "Problem solving": {
            "color": "#d9d9d9",
            "shape": "triangle",
            "desc": "Transformation of a problem state.",
        },
        "Conflict situation": {
            "color": "#ff9999",
            "shape": "octagon",
            "desc": "Competing states, goals or rules.",
        },
        "Knowledge": {
            "color": "#ddebf7",
            "shape": "rectangle",
            "desc": "Structured knowledge.",
        },
        "Tool": {
            "color": "#00b050",
            "shape": "triangle",
            "desc": "Instrument used by a process.",
        },
        "Experience": {
            "color": "#70ad47",
            "shape": "rectangle",
            "desc": "Knowledge obtained through application.",
        },
        "Classification": {
            "color": "#ccc0da",
            "shape": "diamond",
            "desc": "Semantic organization.",
        },
        "Psychological aspect": {
            "color": "#f8cbad",
            "shape": "ellipse",
            "desc": "Individual mental dimension.",
        },
        "Sociological aspect": {
            "color": "#00ffff",
            "shape": "ellipse",
            "desc": "Collective social dimension.",
        },
        "Hierarchical Associative System": {
            "color": "#fd7e14",
            "shape": "ellipse",
            "desc": "Core hierarchical-associative architecture.",
        },
        "Scientific Cage": {
            "color": "#6c757d",
            "shape": "octagon",
            "desc": "Paradigmatic boundary.",
        },
        "Hierarchography": {
            "color": "#e63946",
            "shape": "diamond",
            "desc": "Visual representation of the hierarchy-association system.",
        },
    },
    "relations": [
        ("Human mental concentration", "Identity", "Dependency"),
        ("Identity", "Autobiographical memory", "Aggregation"),
        ("Mission", "Vision", "Realization"),
        ("Vision", "Goal", "Generalization"),
        ("Problem", "Identity", "Dependency"),
        ("Rule", "Decision-making", "CONSTRAINS"),
        ("Knowledge", "Classification", "TRANSFORMS"),
        ("Experience", "Knowledge", "PRODUCES"),
        ("Conflict situation", "Decision-making", "Conflict"),
        ("Hierarchical Associative System", "Hierarchography", "Realization"),
        ("Scientific Cage", "Decision-making", "CONSTRAINS"),
    ],
}


# =============================================================================
# MENTAL APPROACHES
# =============================================================================

MENTAL_APPROACHES_ONTOLOGY = {
    "Perspective shifting": "Change the analytical viewpoint.",
    "Similarity and difference": "Detect structural similarity and distinction.",
    "Core": "Reduce a phenomenon to essential structure.",
    "Attraction": "Identify concepts that can be combined.",
    "Repulsion": "Separate incompatible elements.",
    "Condensation": "Compress complexity into a useful model.",
    "Framework and foundation": "Establish structural boundaries.",
    "Bipolarity and dialectics": "Use opposing forces to produce synthesis.",
    "Constant": "Identify invariant system properties.",
    "Associativity": "Build lateral semantic connections.",
    "Induction": "Move from instances to general patterns.",
    "Whole and part": "Move between systemic and component perspectives.",
    "Mini-max": "Optimize utility under constraints.",
    "Addition and composition": "Combine independent structures.",
    "Hierarchy": "Order concepts by level and dependency.",
    "Balance": "Search for dynamic equilibrium.",
    "Deduction": "Apply general principles to concrete situations.",
    "Abstraction and elimination": "Remove noise and generalize.",
    "Pleasure and displeasure": "Evaluate desirability and resistance.",
    "Openness and closedness": "Analyze system boundaries.",
}


# =============================================================================
# SCIENCE KNOWLEDGE BASE
# =============================================================================

SCIENCE_FIELDS = {
    "Mathematics": {
        "cat": "Formal",
        "methods": ["Axiomatization", "Formal Proof", "Stochastic Modeling", "Topology"],
        "tools": ["MATLAB", "LaTeX", "WolframAlpha"],
        "facets": ["Algebra", "Analysis", "Number Theory", "Calculus"],
    },
    "Physics": {
        "cat": "Natural",
        "methods": ["Quantum Modeling", "Particle Tracking", "Interferometry", "Simulation"],
        "tools": ["Accelerator", "Spectrometer", "Oscilloscope", "Cryostat"],
        "facets": ["Relativity", "Quantum Mechanics", "Thermodynamics", "Optics"],
    },
    "Chemistry": {
        "cat": "Natural",
        "methods": ["Organic Synthesis", "Chromatography", "NMR Spectroscopy", "Titration"],
        "tools": ["NMR", "Mass Spectrometer", "Incubator", "Burette"],
        "facets": ["Biochemistry", "Physical Chemistry", "Analytical Chemistry", "Inorganic Chemistry"],
    },
    "Biology": {
        "cat": "Natural",
        "methods": ["Gene Sequencing", "CRISPR", "Cell Culture", "In-vivo Observation"],
        "tools": ["Electron Microscope", "PCR Machine", "Centrifuge", "Incubator"],
        "facets": ["Genetics", "Microbiology", "Ecology", "Cell Biology"],
    },
    "Neuroscience": {
        "cat": "Natural",
        "methods": ["Neuroimaging", "Optogenetics", "Behavioral Mapping", "Electrophysiology"],
        "tools": ["fMRI", "EEG", "Electrodes", "Patch Clamp"],
        "facets": ["Cognitive Neuroscience", "Neural Plasticity", "Synaptic Physiology"],
    },
    "Psychology": {
        "cat": "Social",
        "methods": ["Psychometrics", "Longitudinal Studies", "Behavioral Experiments", "CBT"],
        "tools": ["Standardized Tests", "Surveys", "Biofeedback", "Eye Tracking"],
        "facets": ["Behavioral", "Clinical", "Developmental", "Cognitive Psychology"],
    },
    "Sociology": {
        "cat": "Social",
        "methods": ["Ethnography", "Network Analysis", "Survey Design", "Grounded Theory"],
        "tools": ["NVivo", "SPSS", "Census Data", "Social Graphs"],
        "facets": ["Demography", "Stratification", "Social Dynamics", "Urban Sociology"],
    },
    "Political Science": {
        "cat": "Social",
        "methods": ["Comparative Method", "Institutional Analysis", "Quantitative Modeling", "Political Theory"],
        "tools": ["STATA", "Polling Data", "Legislative Archives"],
        "facets": ["International Relations", "Comparative Politics", "Political Theory", "Public Policy", "Geopolitics"],
    },
    "Anthropology": {
        "cat": "Social/Humanities",
        "methods": ["Participant Observation", "Ethnography", "Cross-Cultural Comparison", "Archaeological Excavation"],
        "tools": ["Field Journals", "GIS", "Radiocarbon Dating"],
        "facets": ["Cultural Anthropology", "Biological Anthropology", "Archaeology", "Linguistic Anthropology"],
    },
    "Cognitive Science": {
        "cat": "Interdisciplinary",
        "methods": ["Computational Modeling", "Experimental Design", "Turing Analysis"],
        "tools": ["AI Architectures", "Eye Tracking", "Reaction-Time Analysis"],
        "facets": ["Artificial Intelligence", "Philosophy of Mind", "Cognitive Psychology", "Linguistics"],
    },
    "Complexity Science": {
        "cat": "Formal/Interdisciplinary",
        "methods": ["Agent-Based Modeling", "Network Topology", "Chaos Theory", "Fractal Analysis"],
        "tools": ["NetLogo", "Graph Theory Software", "Non-linear Simulators"],
        "facets": ["Self-Organization", "Emergence", "System Dynamics", "Complex Adaptive Systems"],
    },
    "Computer Science": {
        "cat": "Formal",
        "methods": ["Algorithm Design", "Verification", "Complexity Analysis", "Parallelism"],
        "tools": ["GPU Clusters", "Docker", "Compilers", "IDEs", "Kubernetes"],
        "facets": ["AI", "Cybersecurity", "Blockchain", "Cloud Computing"],
    },
    "Medicine": {
        "cat": "Applied",
        "methods": ["Clinical Trials", "Epidemiology", "Radiology", "Pathology"],
        "tools": ["MRI", "CT Scanner", "Biomarker Assays", "Ultrasound"],
        "facets": ["Genomics", "Immunology", "Oncology", "Internal Medicine"],
    },
    "Psychiatry": {
        "cat": "Applied/Medical",
        "methods": ["Clinical Trials", "Diagnostic Interviewing", "Case Formulation", "Neuroimaging Analysis"],
        "tools": ["DSM-5-TR", "ICD-11", "EEG", "fMRI"],
        "facets": ["Clinical Psychiatry", "Neuropsychiatry", "Forensic Psychiatry", "Geriatric Psychiatry"],
    },
    "Public Health": {
        "cat": "Applied/Social",
        "methods": ["Biostatistics", "Community Health Assessment", "Policy Advocacy", "Epidemiological Surveillance"],
        "tools": ["Vital Statistics", "Health Registries", "GIS"],
        "facets": ["Epidemiology", "Environmental Health", "Global Health", "Health Policy"],
    },
    "Engineering": {
        "cat": "Applied",
        "methods": ["FEA Analysis", "Prototyping", "Stress Testing", "Systems Integration"],
        "tools": ["CAD", "3D Printers", "CNC Machines", "Simulation Software"],
        "facets": ["Robotics", "Nanotechnology", "Civil Engineering", "Electrical Engineering"],
    },
    "Materials Science": {
        "cat": "Applied/Natural",
        "methods": ["Crystallography", "Metallography", "Polymer Characterization", "Nanofabrication"],
        "tools": ["SEM", "X-Ray Diffraction", "Spectroscopy"],
        "facets": ["Nanomaterials", "Biomaterials", "Metallurgy", "Semiconductors"],
    },
    "Economics": {
        "cat": "Social",
        "methods": ["Econometrics", "Game Theory", "Macroeconomic Modeling", "Forecasting"],
        "tools": ["Bloomberg", "Stata", "R", "Python"],
        "facets": ["Finance", "Behavioral Economics", "Macroeconomics", "Microeconomics"],
    },
    "Philosophy": {
        "cat": "Humanities",
        "methods": ["Socratic Method", "Dialectics", "Phenomenology", "Conceptual Analysis"],
        "tools": ["Logic Mapping", "Primary Texts", "Semantic Analysis"],
        "facets": ["Epistemology", "Ethics", "Metaphysics", "Aesthetics"],
    },
    "Linguistics": {
        "cat": "Humanities",
        "methods": ["Corpus Analysis", "Syntactic Parsing", "Historical Phonetics", "Transcription"],
        "tools": ["Praat", "NLTK", "WordNet", "ELAN"],
        "facets": ["Semantics", "Phonology", "Sociolinguistics", "Computational Linguistics"],
    },
    "Ecology": {
        "cat": "Natural",
        "methods": ["Remote Sensing", "Trophic Modeling", "Field Sampling", "Biogeochemistry"],
        "tools": ["GIS", "Biosensors", "Drones", "Satellite Imagery"],
        "facets": ["Biodiversity", "Conservation Biology", "Restoration Ecology"],
    },
    "History": {
        "cat": "Humanities",
        "methods": ["Archival Research", "Historiography", "Oral History", "Prosopography"],
        "tools": ["Radiocarbon Dating", "Microfilm", "Digital Archives"],
        "facets": ["Military History", "Diplomacy", "Ancient Civilizations", "Social History"],
    },
    "Architecture": {
        "cat": "Applied",
        "methods": ["Parametric Design", "Environmental Analysis", "BIM", "Urbanism"],
        "tools": ["Revit", "Rhino 3D", "AutoCAD", "Photogrammetry"],
        "facets": ["Urban Design", "Sustainability", "Landscape Architecture", "Heritage"],
    },
    "Geology": {
        "cat": "Natural",
        "methods": ["Stratigraphy", "Mineralogy", "Seismology", "Petrology"],
        "tools": ["Seismograph", "GIS", "Magnetometers", "Thin Sectioning"],
        "facets": ["Tectonics", "Petrology", "Paleontology", "Geophysics"],
    },
    "Geography": {
        "cat": "Natural/Social",
        "methods": ["Spatial Analysis", "Geospatial Modeling", "Remote Sensing", "Field Observation"],
        "tools": ["ArcGIS/QGIS", "GPS", "Satellite Imagery", "Lidar"],
        "facets": ["Physical Geography", "Human Geography", "Geomorphology", "Urban Geography"],
    },
    "Climatology": {
        "cat": "Natural",
        "methods": ["Climate Modeling", "Paleoclimatic Reconstruction", "Time-Series Analysis"],
        "tools": ["HPC", "Weather Stations", "Satellite Radiometers"],
        "facets": ["Meteorology", "Paleoclimatology", "Dynamic Climatology", "Applied Climatology"],
    },
    "Library Science": {
        "cat": "Applied",
        "methods": ["Taxonomy", "Archival Appraisal", "Retrieval Logic", "Metadata"],
        "tools": ["OPAC", "Metadata Systems", "Thesauri", "Digital Archives"],
        "facets": ["Knowledge Organization", "Information Retrieval", "Digital Curation"],
    },
    "Criminology": {
        "cat": "Social",
        "methods": ["Profiling", "Longitudinal Studies", "Victimology Analysis", "Ethnography"],
        "tools": ["Crime Mapping", "AFIS", "CODIS", "SPSS"],
        "facets": ["Penology", "Forensic Psychology", "Police Science", "Criminal Justice"],
    },
    "Forensic Sciences": {
        "cat": "Applied/Natural",
        "methods": ["DNA Profiling", "Ballistics", "Toxicology", "Trace Analysis"],
        "tools": ["Mass Spectrometer", "Luminol", "Comparison Microscope", "AFIS"],
        "facets": ["Forensic Biology", "Forensic Chemistry", "Forensic Pathology", "Digital Forensics"],
    },
    "Legal Science": {
        "cat": "Social",
        "methods": ["Legal Hermeneutics", "Comparative Law", "Dogmatic Method", "Empirical Legal Research"],
        "tools": ["Legislative Databases", "Case Law Archives", "Constitutional Records", "Westlaw"],
        "facets": ["Jurisprudence", "Constitutional Law", "Criminal Law", "Civil Law", "International Law"],
    },
}


SCIENTIFIC_PARADIGMS = {
    "Empiricism": "Knowledge grounded in observation and experience.",
    "Rationalism": "Knowledge grounded in reason and deductive logic.",
    "Constructivism": "Knowledge constructed through cognitive and social processes.",
    "Positivism": "Emphasis on observable and verifiable facts.",
    "Pragmatism": "Evaluation through practical consequences and utility.",
    "Reductionism": "Explanation through component decomposition.",
    "Holism": "Understanding systems as integrated wholes.",
    "Systems Theory": "Analysis of relationships, boundaries and system behavior.",
    "Phenomenology": "Analysis of lived experience and consciousness.",
    "Falsificationism": "Scientific claims must be potentially refutable.",
    "Critical Theory": "Analysis aimed at identifying and transforming structural conditions.",
    "Hermeneutics": "Interpretation of texts, meanings and actions.",
    "Relativism": "Knowledge and values may depend on historical or cultural context.",
    "Structuralism": "Meaning arises through relations within a structure.",
    "Post-Structuralism": "Emphasis on instability, plurality and transformation of structures.",
}


STRUCTURAL_MODELS = {
    "Causal Connections": "Cause-effect chains and mechanisms.",
    "Principles & Relations": "Principles and relations among entities.",
    "Episodes & Sequences": "Temporal ordering and process flow.",
    "Facts & Characteristics": "Properties, evidence and observations.",
    "Generalizations": "Higher-order models and abstractions.",
    "Glossary": "Definitions and terminology.",
    "Concepts": "Abstract conceptual building blocks.",
}


IDEATION_TECHNIQUES = {
    "Six Thinking Hats": "Data, emotion, risk, value, creativity and control perspectives.",
    "SCAMPER": "Substitute, Combine, Adapt, Modify, Put to another use, Eliminate, Reverse.",
    "First Principles": "Decompose a problem into fundamental assumptions and rebuild.",
    "TRIZ": "Resolve contradictions through inventive principles.",
    "Lateral Thinking": "Break established patterns and explore non-obvious paths.",
    "Blue Ocean Strategy": "Create new value spaces through eliminate-reduce-raise-create.",
    "Synectics": "Use direct, personal and symbolic analogies.",
}


# =============================================================================
# COMPONENT FILTER DEFINITIONS
# =============================================================================

GRAPH_COMPONENT_OPTIONS = [
    "Innovations",
    "Science Fields",
    "Scientific Paradigms",
    "Structural Models",
    "Human Thinking Metamodel",
    "Mental Approaches",
    "Processes",
    "Goals / Vision",
    "Constraints / Rules",
    "Entities",
    "Facts / Concepts",
    "System States",
    "Data / Evidence",
    "Root / Knowledge System",
]


def node_matches_component(node, selected_components):
    """Return True if the node belongs to at least one selected component category."""
    if not selected_components:
        return True

    shape = node.get("shape", "")
    layer = node.get("layer", "")
    semantic = node.get("semantic_type", "")
    label_lower = node.get("label", "").lower()

    if "Root / Knowledge System" in selected_components:
        if semantic == "root" or "sis knowledge system" in label_lower or node.get("id") == "knowledge_root":
            return True

    if "Innovations" in selected_components:
        if shape == "diamond" or layer == "innovation" or semantic == "innovation":
            return True

    if "Science Fields" in selected_components:
        if shape == "hexagon" or layer == "domain" or semantic == "science-domain":
            return True

    if "Scientific Paradigms" in selected_components:
        if any(p.lower() in label_lower for p in SCIENTIFIC_PARADIGMS):
            return True
        if "paradigm" in label_lower or "paradigm" in semantic:
            return True

    if "Structural Models" in selected_components:
        if any(m.lower() in label_lower for m in STRUCTURAL_MODELS):
            return True
        if "structural" in label_lower or "model" in semantic:
            return True

    if "Human Thinking Metamodel" in selected_components:
        if semantic == "human-thinking-metamodel":
            return True

    if "Mental Approaches" in selected_components:
        if semantic in {"mental-approach", "mental-approaches-hub"}:
            return True

    if "Processes" in selected_components:
        if shape == "triangle" or layer == "process":
            return True

    if "Goals / Vision" in selected_components:
        if shape == "star" or layer == "goal":
            return True

    if "Constraints / Rules" in selected_components:
        if shape == "octagon" or layer == "constraint":
            return True

    if "Entities" in selected_components:
        if shape == "ellipse" or layer == "entity":
            return True

    if "Facts / Concepts" in selected_components:
        if shape == "rectangle" or layer == "fact":
            return True

    if "System States" in selected_components:
        if shape == "round-rectangle" or layer == "state":
            return True

    if "Data / Evidence" in selected_components:
        if shape == "barrel" or layer == "data":
            return True

    return False


def filter_graph_by_components(graph, selected_components):
    """Keep only nodes that match the selected components and their connecting edges."""
    if not selected_components or set(selected_components) == set(GRAPH_COMPONENT_OPTIONS):
        return graph

    graph = normalize_graph_data(graph)
    nodes = graph["nodes"]
    edges = graph["edges"]

    kept_ids = {
        n["id"] for n in nodes
        if node_matches_component(n, selected_components)
    }

    # Always keep the root if present so the graph stays anchored
    for n in nodes:
        if n.get("semantic_type") == "root" or n.get("id") == "knowledge_root":
            kept_ids.add(n["id"])

    filtered_nodes = [n for n in nodes if n["id"] in kept_ids]
    filtered_edges = [
        e for e in edges
        if e.get("source") in kept_ids and e.get("target") in kept_ids
    ]

    return {"nodes": filtered_nodes, "edges": filtered_edges}


# =============================================================================
# API FUNCTIONS
# =============================================================================

def huggingface_generate(
    api_key,
    model_id,
    system_prompt,
    user_content,
    temperature=0.5,
    top_p=None,
):
    if not api_key:
        raise ValueError(
            "Hugging Face API key is required for Qwen2.5-72B-Instruct."
        )

    clean_model_id = model_id[3:] if model_id.startswith("hf:") else model_id
    routed_model = f"{clean_model_id}"

    headers = {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json",
    }

    messages = []

    if system_prompt:
        messages.append({
            "role": "system",
            "content": system_prompt,
        })

    messages.append({
        "role": "user",
        "content": user_content,
    })

    payload = {
        "model": routed_model,
        "messages": messages,
        "temperature": temperature,
        "stream": False,
        "max_tokens": 8192,
    }

    if top_p is not None:
        payload["top_p"] = top_p

    response = requests.post(
        HF_ROUTER_URL,
        headers=headers,
        json=payload,
        timeout=300,
    )

    if response.status_code != 200:
        try:
            data = response.json()
            error_message = data.get("error", response.text)
        except Exception:
            error_message = response.text

        raise RuntimeError(
            f"Hugging Face API error ({response.status_code}): {error_message}"
        )

    result = response.json()

    try:
        return result["choices"][0]["message"]["content"]
    except Exception:
        raise RuntimeError(
            "Unexpected Hugging Face response format: "
            + json.dumps(result, ensure_ascii=False)[:3000]
        )


def gemini_generate(
    client,
    model_id,
    system_prompt,
    user_content,
    temperature=0.5,
    top_p=None,
    huggingface_api_key=None,
):
    if model_id.startswith("hf:"):
        return huggingface_generate(
            huggingface_api_key,
            model_id,
            system_prompt,
            user_content,
            temperature,
            top_p,
        )

    if client is None:
        raise RuntimeError(
            "Google GenAI client is not initialized."
        )

    config_kwargs = {
        "temperature": temperature,
    }

    if top_p is not None:
        config_kwargs["top_p"] = top_p

    is_gemma = model_id.startswith("gemma")

    if is_gemma:
        combined_input = (
            "### SYSTEM INSTRUCTIONS ###\n"
            + system_prompt
            + "\n\n### USER INPUT ###\n"
            + user_content
        )

        config = genai_types.GenerateContentConfig(
            **config_kwargs
        )

        response = client.models.generate_content(
            model=model_id,
            contents=combined_input,
            config=config,
        )
    else:
        config_kwargs["system_instruction"] = system_prompt

        config = genai_types.GenerateContentConfig(
            **config_kwargs
        )

        response = client.models.generate_content(
            model=model_id,
            contents=user_content,
            config=config,
        )

    if not response or not response.text:
        raise RuntimeError(
            "Google model returned an empty response."
        )

    return response.text


# =============================================================================
# ORCID
# =============================================================================

def fetch_author_bibliographies(author_input):
    if not author_input:
        return ""

    authors = [x.strip() for x in author_input.split(",") if x.strip()]
    output = ""

    for author in authors:
        try:
            search_url = (
                "https://pub.orcid.org/v3.0/search/"
                "?q=" + urllib.parse.quote(author)
            )

            response = requests.get(
                search_url,
                headers={"Accept": "application/json"},
                timeout=8,
            )

            response.raise_for_status()
            data = response.json()

            results = data.get("result", [])

            if not results:
                continue

            orcid_id = (
                results[0]
                .get("orcid-identifier", {})
                .get("path")
            )

            if not orcid_id:
                continue

            record_url = (
                f"https://pub.orcid.org/v3.0/{orcid_id}/record"
            )

            record_response = requests.get(
                record_url,
                headers={"Accept": "application/json"},
                timeout=8,
            )

            record_response.raise_for_status()
            record = record_response.json()

            groups = (
                record
                .get("activities-summary", {})
                .get("works", {})
                .get("group", [])
            )

            output += (
                f"#### ORCID: {author} ({orcid_id})\n"
            )

            for group in groups[:15]:
                summary = group.get("work-summary", [{}])[0]

                title = (
                    summary
                    .get("title", {})
                    .get("title", {})
                    .get("value", "Unknown Title")
                )

                pub_date = summary.get("publication-date")
                year = (
                    pub_date
                    .get("year", {})
                    .get("value", "n.d.")
                    if pub_date
                    else "n.d."
                )

                output += f"- **{year}**: {title}\n"

            output += "\n---\n"

        except Exception:
            continue

    return output


# =============================================================================
# KNOWLEDGE CONTEXT BUILDERS
# =============================================================================

def build_knowledge_architecture_context(
    sciences,
    paradigms,
    structural_models,
    techniques,
):
    science_context = []

    for field in sciences:
        info = SCIENCE_FIELDS.get(field, {})
        science_context.append(
            f"{field}: "
            f"category={info.get('cat', '')}; "
            f"methods={', '.join(info.get('methods', []))}; "
            f"facets={', '.join(info.get('facets', []))}"
        )

    paradigm_context = "\n".join(
        f"- {name}: {SCIENTIFIC_PARADIGMS[name]}"
        for name in paradigms
        if name in SCIENTIFIC_PARADIGMS
    )

    model_context = "\n".join(
        f"- {name}: {STRUCTURAL_MODELS[name]}"
        for name in structural_models
        if name in STRUCTURAL_MODELS
    )

    technique_context = "\n".join(
        f"- {name}: {IDEATION_TECHNIQUES[name]}"
        for name in techniques
        if name in IDEATION_TECHNIQUES
    )

    thesaurus_relations = "\n".join(
        f"- {key}: {value}"
        for key, value in RELATION_DEFINITIONS.items()
    )

    hierarchy_context = "\n".join(
        f"- {x['id']} {x['name']}: "
        f"root={x['root']}; relations={', '.join(x['relations'])}"
        for x in POLYHIERARCHY["hierarchies"]
    )

    uml_context = "\n".join(
        f"- {name}: {', '.join(attrs)}"
        for name, attrs in UML_METAMODEL["classes"].items()
    )

    return f"""
SIS KNOWLEDGE ARCHITECTURE

1. MULTIDIMENSIONAL THESAURUS
Dimensions:
{json.dumps(THESAURUS_ONTOLOGY["dimensions"], ensure_ascii=False, indent=2)}

2. THESAURUS RELATION VOCABULARY
{thesaurus_relations}

3. POLYHIERARCHICAL ONTOLOGY
Levels:
{json.dumps(POLYHIERARCHY["levels"], ensure_ascii=False, indent=2)}

Hierarchies:
{hierarchy_context}

4. UML METAMODEL
{uml_context}

5. UML RELATIONS
{json.dumps(UML_METAMODEL["relationships"], ensure_ascii=False, indent=2)}

6. HIERARCHOLOGY
{json.dumps(HIERARCHOLOGY_ONTOLOGY, ensure_ascii=False, indent=2)}

7. HUMAN THINKING METAMODEL
{json.dumps(HUMAN_THINKING_METAMODEL, ensure_ascii=False, indent=2)}

8. MENTAL APPROACHES
{json.dumps(MENTAL_APPROACHES_ONTOLOGY, ensure_ascii=False, indent=2)}

9. SELECTED SCIENCE FIELDS
{chr(10).join('- ' + x for x in science_context)}

10. SCIENTIFIC PARADIGMS
{paradigm_context}

11. STRUCTURAL MODELS
{model_context}

12. IDEATION TECHNIQUES
{technique_context}
"""


# =============================================================================
# ROBUST JSON EXTRACTION
# =============================================================================

def extract_json_object(text):
    if not text:
        return None

    candidates = []

    fenced = re.findall(
        r"```(?:json)?\s*(\{.*?\})\s*```",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )

    candidates.extend(fenced)

    marker_index = text.find("### SEMANTIC_GRAPH_JSON")

    if marker_index >= 0:
        candidates.append(
            text[marker_index + len("### SEMANTIC_GRAPH_JSON"):]
        )

    candidates.append(text)

    for candidate in candidates:
        start = candidate.find("{")

        if start < 0:
            continue

        depth = 0
        in_string = False
        escape = False

        for i in range(start, len(candidate)):
            char = candidate[i]

            if escape:
                escape = False
                continue

            if char == "\\":
                escape = True
                continue

            if char == '"':
                in_string = not in_string
                continue

            if in_string:
                continue

            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1

                if depth == 0:
                    raw = candidate[start:i + 1]

                    try:
                        return json.loads(raw)
                    except Exception:
                        cleaned = sanitize_json_text(raw)

                        try:
                            return json.loads(cleaned)
                        except Exception:
                            pass

                    break

    return None


def sanitize_json_text(raw):
    raw = raw.replace("\ufeff", "")
    raw = raw.replace("```json", "")
    raw = raw.replace("```", "")

    raw = "".join(
        ch for ch in raw
        if ord(ch) >= 32 or ch in "\n\r\t"
    )

    raw = re.sub(r"\bNone\b", "null", raw)
    raw = re.sub(r"\bTrue\b", "true", raw)
    raw = re.sub(r"\bFalse\b", "false", raw)

    return raw.strip()


# =============================================================================
# GRAPH NORMALIZATION
# =============================================================================

def normalize_graph_data(data):
    if not isinstance(data, dict):
        return {"nodes": [], "edges": []}

    nodes = data.get("nodes", [])
    edges = data.get("edges", [])

    if not isinstance(nodes, list):
        nodes = []

    if not isinstance(edges, list):
        edges = []

    normalized_nodes = []
    node_ids = set()

    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            continue

        node_id = str(
            node.get("id")
            or f"n{index + 1}"
        )

        label = str(
            node.get("label")
            or node.get("name")
            or node_id
        ).strip()

        if not label:
            label = node_id

        if node_id in node_ids:
            node_id = f"{node_id}_{index}"

        node_ids.add(node_id)

        shape = str(
            node.get("shape", "rectangle")
        )

        if shape not in VALID_SHAPES:
            shape = "rectangle"

        geometry = NODE_GEOMETRY[shape]

        color = str(
            node.get("color")
            or geometry["color"]
        )

        description = str(
            node.get("description")
            or node.get("desc")
            or ""
        ).replace("\n", " ").strip()

        layer = str(
            node.get("layer")
            or geometry["layer"]
        )

        level = str(
            node.get("level")
            or infer_hierarchy_level(layer, shape)
        )

        semantic_type = str(
            node.get("semantic_type")
            or layer
        )

        state = str(
            node.get("state")
            or ""
        )

        normalized_nodes.append({
            "id": node_id,
            "label": label[:160],
            "shape": shape,
            "color": color,
            "description": description[:2000],
            "layer": layer,
            "level": level,
            "semantic_type": semantic_type,
            "state": state,
            "source_phase": str(node.get("source_phase") or ""),
            "importance": float(node.get("importance", 0.0) or 0.0),
            "innovation_score": float(node.get("innovation_score", 0.0) or 0.0),
            "feasibility_score": float(node.get("feasibility_score", 0.0) or 0.0),
            "size": int(node.get("size") or geometry["size"]),
        })

    valid_ids = {node["id"] for node in normalized_nodes}

    normalized_edges = []

    for index, edge in enumerate(edges):
        if not isinstance(edge, dict):
            continue

        source = str(edge.get("source", ""))
        target = str(edge.get("target", ""))

        if source not in valid_ids or target not in valid_ids:
            continue

        relation = str(
            edge.get("rel_type")
            or edge.get("relation")
            or "RT"
        )

        if relation not in RELATION_DEFINITIONS:
            relation = "RT"

        normalized_edges.append({
            "id": str(edge.get("id") or f"e{index + 1}"),
            "source": source,
            "target": target,
            "rel_type": relation,
            "label": relation,
            "full_label": RELATION_DEFINITIONS[relation],
            "weight": float(
                edge.get("weight", 1.0)
                if str(edge.get("weight", "1.0")).replace(".", "", 1).isdigit()
                else 1.0
            ),
            "direction": str(
                edge.get("direction", "directed")
            ),
        })

    return {
        "nodes": normalized_nodes,
        "edges": normalized_edges,
    }


def infer_hierarchy_level(layer, shape):
    layer = layer.lower()

    if layer in {"goal", "domain", "macro", "vision"}:
        return "Macro"

    if layer in {"process", "innovation", "constraint", "system", "meso"}:
        return "Meso"

    if layer in {"fact", "data", "entity", "state", "micro"}:
        return "Micro"

    if shape == "star":
        return "Macro"

    if shape in {"diamond", "hexagon", "octagon", "triangle"}:
        return "Meso"

    return "Micro"


# =============================================================================
# DETERMINISTIC ONTOLOGICAL ENRICHMENT (RICH RELATIONS)
# =============================================================================

def enrich_graph_with_architecture(graph, selected_sciences):
    graph = normalize_graph_data(graph)

    nodes = graph["nodes"]
    edges = graph["edges"]

    if not nodes:
        return graph

    node_map = {n["id"]: n for n in nodes}

    for node in nodes:
        if not node.get("level"):
            node["level"] = infer_hierarchy_level(
                node.get("layer", ""),
                node.get("shape", "rectangle"),
            )

        if node["shape"] == "diamond":
            if "Mental Approaches" not in node["description"]:
                node["description"] += (
                    " Innovation node: identify the synthesized Mental "
                    "Approaches and transformational mechanism in the report."
                )

    existing_labels = {
        n["label"].strip().lower()
        for n in nodes
    }

    for science in selected_sciences[:8]:
        if science.lower() in existing_labels:
            continue

        node_id = unique_node_id(
            "domain_" + slugify(science),
            node_map,
        )

        node = {
            "id": node_id,
            "label": science,
            "shape": "hexagon",
            "color": NODE_GEOMETRY["hexagon"]["color"],
            "description": (
                SCIENCE_FIELDS.get(science, {})
                .get("cat", "Scientific domain")
            ),
            "layer": "domain",
            "level": "Macro",
            "semantic_type": "science-domain",
            "state": "",
            "size": 115,
        }

        nodes.append(node)
        node_map[node_id] = node
        existing_labels.add(science.lower())

    root_id = find_label_node(
        nodes,
        ["Knowledge Domain", "Knowledge", "System", "SIS Knowledge System"],
    )

    if root_id is None:
        root_id = unique_node_id("knowledge_root", node_map)

        root_node = {
            "id": root_id,
            "label": "SIS Knowledge System",
            "shape": "star",
            "color": "#1d3557",
            "description": (
                "Root of the multidimensional SIS knowledge architecture."
            ),
            "layer": "goal",
            "level": "Macro",
            "semantic_type": "root",
            "state": "initial",
            "size": 135,
        }

        nodes.insert(0, root_node)
        node_map[root_id] = root_node

    existing_pairs = {
        (
            edge["source"],
            edge["target"],
            edge["rel_type"],
        )
        for edge in edges
    }

    def add_edge(source, target, relation, weight=1.0):
        key = (source, target, relation)

        if key in existing_pairs:
            return

        if source not in node_map or target not in node_map:
            return

        if source == target:
            return

        edges.append({
            "id": f"auto_{len(edges) + 1}",
            "source": source,
            "target": target,
            "rel_type": relation,
            "label": relation,
            "full_label": RELATION_DEFINITIONS.get(relation, relation),
            "weight": weight,
            "direction": "directed",
        })

        existing_pairs.add(key)

    for node in nodes:
        if node["id"] == root_id:
            continue
        if node["layer"] == "domain" or node["semantic_type"] == "science-domain":
            add_edge(root_id, node["id"], "NT", 2.0)
            add_edge(root_id, node["id"], "TT", 1.5)

    macro_nodes = [n for n in nodes if n["level"] == "Macro" and n["id"] != root_id]
    meso_nodes = [n for n in nodes if n["level"] == "Meso"]
    micro_nodes = [n for n in nodes if n["level"] == "Micro"]

    for macro in macro_nodes[:15]:
        for meso in meso_nodes[:25]:
            if macro["id"] == meso["id"]:
                continue
            if semantic_related(macro, meso, threshold=0.30):
                add_edge(macro["id"], meso["id"], "BT", 1.1)
                add_edge(meso["id"], macro["id"], "NT", 0.9)

    for meso in meso_nodes[:30]:
        for micro in micro_nodes[:30]:
            if meso["id"] == micro["id"]:
                continue
            if semantic_related(meso, micro, threshold=0.30):
                add_edge(meso["id"], micro["id"], "NT", 0.85)
                add_edge(micro["id"], meso["id"], "BT", 0.7)

    for meso in meso_nodes[:20]:
        for micro in micro_nodes[:20]:
            if semantic_related(meso, micro, threshold=0.40):
                add_edge(meso["id"], micro["id"], "IN", 0.75)

    all_nodes = nodes[:70]
    for i, source in enumerate(all_nodes):
        for target in all_nodes[i + 1:]:
            if source["id"] == target["id"]:
                continue
            score = semantic_similarity(source, target)
            if score >= 0.55:
                add_edge(source["id"], target["id"], "EQ", 0.9)
            elif score >= 0.38:
                add_edge(source["id"], target["id"], "RT", 0.45)
            elif score >= 0.28 and (
                source.get("layer") == target.get("layer")
                or source.get("semantic_type") == target.get("semantic_type")
            ):
                add_edge(source["id"], target["id"], "AS", 0.35)

    goal_nodes = [n for n in nodes if n["shape"] == "star" or n["layer"] == "goal"]
    domain_nodes = [n for n in nodes if n["shape"] == "hexagon" or n["layer"] == "domain"]
    process_nodes = [n for n in nodes if n["shape"] == "triangle" or n["layer"] == "process"]
    innovation_nodes = [n for n in nodes if n["shape"] == "diamond" or n["layer"] == "innovation"]
    constraint_nodes = [n for n in nodes if n["shape"] == "octagon" or n["layer"] == "constraint"]
    entity_nodes = [n for n in nodes if n["shape"] == "ellipse" or n["layer"] == "entity"]
    fact_nodes = [n for n in nodes if n["shape"] == "rectangle" or n["layer"] == "fact"]
    state_nodes = [n for n in nodes if n["shape"] == "round-rectangle" or n["layer"] == "state"]
    data_nodes = [n for n in nodes if n["shape"] == "barrel" or n["layer"] == "data"]

    for goal in goal_nodes[:8]:
        for domain in domain_nodes[:12]:
            if semantic_related(goal, domain, threshold=0.25):
                add_edge(domain["id"], goal["id"], "Generalization", 1.0)
                add_edge(goal["id"], domain["id"], "Specialization", 0.8)

    for domain in domain_nodes[:12]:
        for process in process_nodes[:15]:
            if semantic_related(domain, process, threshold=0.28):
                add_edge(process["id"], domain["id"], "Generalization", 0.9)
                add_edge(domain["id"], process["id"], "Specialization", 0.75)

    for goal in goal_nodes[:6]:
        for process in process_nodes[:12]:
            add_edge(goal["id"], process["id"], "Composition", 1.2)
        for innovation in innovation_nodes[:10]:
            add_edge(goal["id"], innovation["id"], "Composition", 1.1)

    for domain in domain_nodes[:10]:
        for fact in fact_nodes[:15]:
            if semantic_related(domain, fact, threshold=0.25):
                add_edge(domain["id"], fact["id"], "Aggregation", 0.8)
        for entity in entity_nodes[:10]:
            add_edge(domain["id"], entity["id"], "Aggregation", 0.7)

    for domain in domain_nodes[:10]:
        for process in process_nodes[:12]:
            add_edge(domain["id"], process["id"], "Containment", 0.9)
        for state in state_nodes[:8]:
            add_edge(domain["id"], state["id"], "Containment", 0.7)

    for innovation in innovation_nodes[:12]:
        for process in process_nodes[:15]:
            if semantic_related(innovation, process, threshold=0.28):
                add_edge(process["id"], innovation["id"], "Realization", 1.0)
        for goal in goal_nodes[:6]:
            add_edge(innovation["id"], goal["id"], "Realization", 0.9)

    for process in process_nodes[:15]:
        for data in data_nodes[:10]:
            add_edge(process["id"], data["id"], "Dependency", 0.8)
        for entity in entity_nodes[:10]:
            add_edge(process["id"], entity["id"], "Dependency", 0.7)
        for constraint in constraint_nodes[:10]:
            add_edge(process["id"], constraint["id"], "Dependency", 0.85)

    for innovation in innovation_nodes[:10]:
        for process in process_nodes[:12]:
            add_edge(innovation["id"], process["id"], "Dependency", 0.9)

    for constraint in constraint_nodes[:10]:
        for goal in goal_nodes[:8]:
            add_edge(constraint["id"], goal["id"], "Conflict", 0.7)
        for innovation in innovation_nodes[:10]:
            if semantic_related(constraint, innovation, threshold=0.20):
                add_edge(constraint["id"], innovation["id"], "Conflict", 0.65)
        for process in process_nodes[:12]:
            add_edge(constraint["id"], process["id"], "Conflict", 0.6)

    for constraint in constraint_nodes[:12]:
        for process in process_nodes[:15]:
            add_edge(constraint["id"], process["id"], "IF-THEN", 0.85)
        for innovation in innovation_nodes[:10]:
            add_edge(constraint["id"], innovation["id"], "IF-THEN", 0.8)

    for i, p1 in enumerate(process_nodes[:12]):
        for p2 in process_nodes[i + 1:12]:
            if semantic_related(p1, p2, threshold=0.30):
                add_edge(p1["id"], p2["id"], "AND", 0.7)
            else:
                add_edge(p1["id"], p2["id"], "OR", 0.5)

    for i, inn1 in enumerate(innovation_nodes[:8]):
        for inn2 in innovation_nodes[i + 1:8]:
            add_edge(inn1["id"], inn2["id"], "XOR", 0.55)

    for constraint in constraint_nodes[:8]:
        for state in state_nodes[:8]:
            add_edge(constraint["id"], state["id"], "NOT", 0.6)
        for process in process_nodes[:8]:
            if not semantic_related(constraint, process, threshold=0.35):
                add_edge(constraint["id"], process["id"], "NOT", 0.5)

    for process in process_nodes[:20]:
        for innovation in innovation_nodes[:15]:
            if semantic_related(process, innovation, threshold=0.25):
                add_edge(process["id"], innovation["id"], "TRANSFORMS", 1.2)
                add_edge(process["id"], innovation["id"], "ENABLES", 1.0)

    for innovation in innovation_nodes[:15]:
        for state in state_nodes[:12]:
            add_edge(innovation["id"], state["id"], "TRANSFORMS", 1.0)
            add_edge(innovation["id"], state["id"], "PRODUCES", 0.9)

    for process in process_nodes[:15]:
        for state in state_nodes[:10]:
            add_edge(process["id"], state["id"], "CAUSES", 0.95)
            add_edge(process["id"], state["id"], "PRECEDES", 0.8)

    for data in data_nodes[:10]:
        for process in process_nodes[:12]:
            add_edge(data["id"], process["id"], "FEEDS", 0.85)
            add_edge(process["id"], data["id"], "CONSUMES", 0.7)

    for constraint in constraint_nodes[:10]:
        for process in process_nodes[:12]:
            add_edge(constraint["id"], process["id"], "CONSTRAINS", 1.0)
        for goal in goal_nodes[:6]:
            add_edge(constraint["id"], goal["id"], "CONSTRAINS", 0.9)

    for process in process_nodes[:12]:
        for process2 in process_nodes[:12]:
            if process["id"] != process2["id"] and semantic_related(process, process2, threshold=0.30):
                add_edge(process["id"], process2["id"], "TRIGGERS", 0.7)

    for data in data_nodes[:8]:
        for fact in fact_nodes[:10]:
            add_edge(data["id"], fact["id"], "MEASURES", 0.75)
            add_edge(fact["id"], data["id"], "VALIDATES", 0.7)

    if len(state_nodes) >= 2:
        add_edge(state_nodes[1]["id"], state_nodes[0]["id"], "FEEDBACK", 0.8)
        if len(state_nodes) >= 3:
            add_edge(state_nodes[2]["id"], state_nodes[0]["id"], "NEGATIVE-FEEDBACK", 0.7)
            add_edge(state_nodes[0]["id"], state_nodes[1]["id"], "POSITIVE-FEEDBACK", 0.65)

    return {
        "nodes": nodes,
        "edges": edges,
    }


# =============================================================================
# HUMAN THINKING METAMODEL (HTM) + MENTAL APPROACHES (MA) ENRICHMENT
# =============================================================================

def enrich_graph_with_human_thinking_metamodel(graph):
    graph = normalize_graph_data(graph)

    nodes = graph["nodes"]
    edges = graph["edges"]

    node_map = {n["id"]: n for n in nodes}

    existing_labels = {
        n["label"].strip().lower(): n["id"]
        for n in nodes
    }

    label_to_id = {}

    for label, meta in HUMAN_THINKING_METAMODEL["nodes"].items():
        lower_label = label.strip().lower()

        if lower_label in existing_labels:
            label_to_id[label] = existing_labels[lower_label]
            continue

        shape = meta.get("shape", "rectangle")

        if shape not in VALID_SHAPES:
            shape = "rectangle"

        geometry = NODE_GEOMETRY[shape]

        node_id = unique_node_id(
            "htm_" + slugify(label),
            node_map,
        )

        node = {
            "id": node_id,
            "label": label,
            "shape": shape,
            "color": meta.get("color", geometry["color"]),
            "description": meta.get(
                "desc",
                "Human Thinking Metamodel node.",
            ),
            "layer": geometry["layer"],
            "level": infer_hierarchy_level(geometry["layer"], shape),
            "semantic_type": "human-thinking-metamodel",
            "state": "",
            "size": geometry["size"],
        }

        nodes.append(node)
        node_map[node_id] = node
        existing_labels[lower_label] = node_id
        label_to_id[label] = node_id

    existing_pairs = {
        (edge["source"], edge["target"], edge["rel_type"])
        for edge in edges
    }

    def add_edge(source, target, relation, weight=1.0):
        key = (source, target, relation)

        if key in existing_pairs:
            return

        if source not in node_map or target not in node_map:
            return

        if relation not in RELATION_DEFINITIONS:
            relation = "RT"

        edges.append({
            "id": f"htm_e{len(edges) + 1}",
            "source": source,
            "target": target,
            "rel_type": relation,
            "label": relation,
            "full_label": RELATION_DEFINITIONS[relation],
            "weight": weight,
            "direction": "directed",
        })

        existing_pairs.add(key)

    for source_label, target_label, relation in HUMAN_THINKING_METAMODEL["relations"]:
        source_id = label_to_id.get(source_label)
        target_id = label_to_id.get(target_label)

        if source_id and target_id:
            add_edge(source_id, target_id, relation, 1.0)

    return {
        "nodes": nodes,
        "edges": edges,
    }


def enrich_graph_with_mental_approaches(graph, selected_techniques=None):
    graph = normalize_graph_data(graph)

    nodes = graph["nodes"]
    edges = graph["edges"]

    node_map = {n["id"]: n for n in nodes}

    existing_labels = {
        n["label"].strip().lower(): n["id"]
        for n in nodes
    }

    hub_id = find_label_node(
        nodes,
        ["Mental Approaches", "Mental Approaches Hub"],
    )

    if hub_id is None:
        hub_id = unique_node_id("mental_approaches_hub", node_map)

        hub_node = {
            "id": hub_id,
            "label": "Mental Approaches",
            "shape": "hexagon",
            "color": NODE_GEOMETRY["hexagon"]["color"],
            "description": (
                "Framework of cognitive/mental approaches used for "
                "knowledge transformation and innovation synthesis."
            ),
            "layer": "domain",
            "level": "Macro",
            "semantic_type": "mental-approaches-hub",
            "state": "",
            "size": 115,
        }

        nodes.append(hub_node)
        node_map[hub_id] = hub_node
        existing_labels["mental approaches"] = hub_id

    existing_pairs = {
        (edge["source"], edge["target"], edge["rel_type"])
        for edge in edges
    }

    def add_edge(source, target, relation, weight=1.0):
        key = (source, target, relation)

        if key in existing_pairs:
            return

        if source not in node_map or target not in node_map:
            return

        edges.append({
            "id": f"ma_e{len(edges) + 1}",
            "source": source,
            "target": target,
            "rel_type": relation,
            "label": relation,
            "full_label": RELATION_DEFINITIONS[relation],
            "weight": weight,
            "direction": "directed",
        })

        existing_pairs.add(key)

    diamond_nodes = [
        n for n in nodes
        if n["shape"] == "diamond"
    ]

    preferred = set(selected_techniques or [])

    for name, desc in MENTAL_APPROACHES_ONTOLOGY.items():
        lower_name = name.strip().lower()

        if lower_name in existing_labels:
            approach_id = existing_labels[lower_name]
        else:
            approach_id = unique_node_id(
                "ma_" + slugify(name),
                node_map,
            )

            approach_node = {
                "id": approach_id,
                "label": name,
                "shape": "triangle",
                "color": NODE_GEOMETRY["triangle"]["color"],
                "description": desc,
                "layer": "process",
                "level": "Meso",
                "semantic_type": "mental-approach",
                "state": "",
                "size": 105,
            }

            nodes.append(approach_node)
            node_map[approach_id] = approach_node
            existing_labels[lower_name] = approach_id

        add_edge(hub_id, approach_id, "NT", 1.0)

        pseudo_source = {
            "label": name,
            "layer": "process",
            "level": "Meso",
        }

        for diamond in diamond_nodes[:15]:
            if diamond["id"] == approach_id:
                continue

            if semantic_related(diamond, pseudo_source):
                add_edge(
                    approach_id,
                    diamond["id"],
                    "ENABLES",
                    0.9 if name in preferred else 0.6,
                )

    return {
        "nodes": nodes,
        "edges": edges,
    }


def slugify(value):
    return re.sub(
        r"[^a-zA-Z0-9]+",
        "_",
        str(value).strip().lower(),
    ).strip("_")


def unique_node_id(base, node_map):
    candidate = base or "node"

    if candidate not in node_map:
        return candidate

    i = 2

    while f"{candidate}_{i}" in node_map:
        i += 1

    return f"{candidate}_{i}"


def find_label_node(nodes, labels):
    wanted = {
        x.strip().lower()
        for x in labels
    }

    for node in nodes:
        if node["label"].strip().lower() in wanted:
            return node["id"]

    return None


SEMANTIC_STOPWORDS = {
    "knowledge", "system", "domain", "concept", "process",
    "approach", "method", "aspect", "level", "state", "human",
    "mental", "thinking", "science", "scientific", "model",
    "structure", "framework", "general", "specific", "information",
}


def _semantic_tokens(node):
    text = " ".join([
        str(node.get("label", "")),
        str(node.get("description", "")),
        str(node.get("semantic_type", "")),
    ]).lower()
    tokens = set(re.findall(r"[a-zA-ZÀ-ž0-9]{4,}", text))
    return {t for t in tokens if t not in SEMANTIC_STOPWORDS}


def semantic_similarity(a, b):
    if not a or not b:
        return 0.0

    if a.get("id") == b.get("id"):
        return 1.0

    a_label = str(a.get("label", "")).strip().lower()
    b_label = str(b.get("label", "")).strip().lower()

    if a_label and a_label == b_label:
        return 1.0

    a_words = _semantic_tokens(a)
    b_words = _semantic_tokens(b)

    if not a_words or not b_words:
        return 0.0

    intersection = len(a_words & b_words)
    if intersection == 0:
        return 0.0

    union = len(a_words | b_words)
    jaccard = intersection / max(union, 1)
    containment = intersection / max(min(len(a_words), len(b_words)), 1)

    return min(1.0, 0.65 * containment + 0.35 * jaccard)


def semantic_related(a, b, threshold=0.38):
    if not a or not b:
        return False

    if a.get("id") == b.get("id"):
        return False

    score = semantic_similarity(a, b)
    if score >= threshold:
        return True

    a_words = _semantic_tokens(a)
    b_words = _semantic_tokens(b)
    shared = a_words & b_words

    if shared and (
        a.get("semantic_type") == b.get("semantic_type")
        or a.get("layer") == b.get("layer")
    ):
        return len(shared) >= 1

    return False


def _edge_exists(edges, source, target, relation=None):
    for edge in edges:
        if edge.get("source") == source and edge.get("target") == target:
            if relation is None or edge.get("rel_type") == relation:
                return True
        if relation is not None and edge.get("source") == target and edge.get("target") == source and edge.get("rel_type") == relation:
            return True
    return False


def connect_isolated_components(graph):
    graph = normalize_graph_data(graph)
    nodes = graph["nodes"]
    edges = graph["edges"]

    if not nodes:
        return graph

    node_map = {n["id"]: n for n in nodes}

    def add_edge(source, target, relation, weight=0.6):
        if source not in node_map or target not in node_map or source == target:
            return False
        if _edge_exists(edges, source, target, relation):
            return False
        edges.append({
            "id": f"connect_e{len(edges) + 1}",
            "source": source,
            "target": target,
            "rel_type": relation,
            "label": relation,
            "full_label": RELATION_DEFINITIONS.get(relation, relation),
            "weight": weight,
            "direction": "directed",
        })
        return True

    root_id = find_label_node(
        nodes,
        ["SIS Knowledge System", "Knowledge Domain", "Knowledge", "System"],
    )
    if root_id is None:
        root_id = "knowledge_root"

    if root_id not in node_map:
        root_id = next((n["id"] for n in nodes if n.get("semantic_type") == "root"), nodes[0]["id"])

    htm = find_label_node(nodes, ["Human Thinking Metamodel", "Human Thinking"])
    ma = find_label_node(nodes, ["Mental Approaches", "Mental Approaches Hub"])

    if htm and htm != root_id:
        add_edge(root_id, htm, "NT", 2.0)
    if ma and ma != root_id:
        add_edge(root_id, ma, "NT", 2.0)

    def components():
        adjacency = {n["id"]: set() for n in nodes}
        for e in edges:
            s, t = e.get("source"), e.get("target")
            if s in adjacency and t in adjacency:
                adjacency[s].add(t)
                adjacency[t].add(s)
        seen = set()
        result = []
        for nid in adjacency:
            if nid in seen:
                continue
            stack = [nid]
            comp = set()
            while stack:
                cur = stack.pop()
                if cur in seen:
                    continue
                seen.add(cur)
                comp.add(cur)
                stack.extend(adjacency[cur] - seen)
            result.append(comp)
        return result

    comps = components()
    root_comp = next((c for c in comps if root_id in c), {root_id})

    for comp in comps:
        if comp is root_comp or root_id in comp:
            continue

        comp_nodes = [node_map[nid] for nid in comp if nid in node_map]
        if not comp_nodes:
            continue

        anchors = [node_map[nid] for nid in root_comp if nid in node_map]

        best_pair = None
        best_score = -1.0

        for source in comp_nodes:
            for target in anchors:
                score = semantic_similarity(source, target)

                if target.get("semantic_type") in {
                    "root", "science-domain", "human-thinking-metamodel",
                    "mental-approaches-hub", "mental-approach",
                }:
                    score += 0.08

                if source.get("level") == target.get("level"):
                    score += 0.02

                if score > best_score:
                    best_score = score
                    best_pair = (source, target)

        if best_pair is None:
            continue

        source, target = best_pair
        relation = "AS"
        weight = max(0.45, min(0.9, best_score))
        add_edge(source["id"], target["id"], relation, weight)

        comps = components()
        root_comp = next((c for c in comps if root_id in c), root_comp)

    return {"nodes": nodes, "edges": edges}


# =============================================================================
# TWO-PHASE GRAPH INTEGRATION + IMPORTANCE RANKING
# =============================================================================

def _label_key(label):
    return re.sub(r"[^a-z0-9]+", " ", str(label).lower()).strip()


def merge_phase_graphs(phase1_graph, phase2_graph):
    """Merge IMA and MA graphs by semantic label while preserving provenance."""
    g1 = normalize_graph_data(phase1_graph)
    g2 = normalize_graph_data(phase2_graph)

    nodes = []
    edges = []
    label_to_id = {}
    id_map = {}

    def add_phase(graph, phase_name):
        for node in graph["nodes"]:
            key = _label_key(node["label"])
            if not key:
                continue

            if key in label_to_id:
                existing = next(n for n in nodes if n["id"] == label_to_id[key])
                existing_phase = existing.get("source_phase", "")
                if phase_name not in existing_phase.split("+"):
                    existing["source_phase"] = "+".join(
                        [x for x in [existing_phase, phase_name] if x]
                    )
                if node.get("description") and node["description"] not in existing["description"]:
                    existing["description"] = (
                        existing["description"].rstrip(".") + ". " +
                        node["description"].strip()
                    )[:2000]
                id_map[(phase_name, node["id"])] = existing["id"]
                continue

            new_id = node["id"]
            if new_id in {n["id"] for n in nodes}:
                new_id = unique_node_id(f"{phase_name.lower()}_{new_id}", {n["id"]: n for n in nodes})

            copied = dict(node)
            copied["id"] = new_id
            copied["source_phase"] = phase_name
            copied["importance"] = 0.0
            nodes.append(copied)
            label_to_id[key] = new_id
            id_map[(phase_name, node["id"])] = new_id

        for edge in graph["edges"]:
            source = id_map.get((phase_name, edge["source"]))
            target = id_map.get((phase_name, edge["target"]))
            if not source or not target or source == target:
                continue
            edges.append({
                **edge,
                "id": f"{phase_name.lower()}_{edge['id']}",
                "source": source,
                "target": target,
            })

    add_phase(g1, "IMA")
    add_phase(g2, "MA")

    # Deduplicate semantically identical edges while preserving strongest weight.
    dedup = {}
    for edge in edges:
        key = (edge["source"], edge["target"], edge["rel_type"])
        if key not in dedup or edge["weight"] > dedup[key]["weight"]:
            dedup[key] = edge

    return normalize_graph_data({"nodes": nodes, "edges": list(dedup.values())})


def rank_integrated_graph(graph):
    """Compute structural importance so the displayed graph favors meaningful bridges."""
    graph = normalize_graph_data(graph)
    nodes = graph["nodes"]
    edges = graph["edges"]

    adjacency = {n["id"]: [] for n in nodes}
    for edge in edges:
        s, t = edge["source"], edge["target"]
        if s in adjacency and t in adjacency:
            w = max(0.1, float(edge.get("weight", 1.0)))
            adjacency[s].append((t, w, edge))
            adjacency[t].append((s, w, edge))

    for node in nodes:
        nid = node["id"]
        degree = len(adjacency.get(nid, []))
        weighted_degree = sum(x[1] for x in adjacency.get(nid, []))
        p = min(100.0, degree * 5.0 + weighted_degree * 3.0)

        p += {"Macro": 18, "Meso": 13, "Micro": 7}.get(node.get("level"), 4)
        p += {
            "root": 80,
            "goal": 22,
            "innovation": 32,
            "process": 16,
            "domain": 18,
            "constraint": 12,
            "state": 12,
            "fact": 8,
            "entity": 8,
            "data": 7,
        }.get(node.get("layer"), 5)

        if node.get("source_phase") == "IMA+MA":
            p += 42
        elif node.get("source_phase") in {"IMA", "MA"}:
            p += 12

        if node.get("semantic_type") in {
            "human-thinking-metamodel",
            "mental-approach",
            "mental-approaches-hub",
            "science-domain",
        }:
            p += 8

        # Prefer bridges between phases and operationally meaningful relations.
        phase_bridge = 0
        for other, weight, edge in adjacency.get(nid, []):
            other_node = next((x for x in nodes if x["id"] == other), None)
            if not other_node:
                continue
            if {node.get("source_phase"), other_node.get("source_phase")} == {"IMA", "MA"}:
                phase_bridge += 18
            if edge.get("rel_type") in {
                "CAUSES", "ENABLES", "TRANSFORMS", "PRODUCES",
                "REALIZATION", "Realization", "Dependency",
                "IF-THEN", "FEEDBACK", "VALIDATES",
            }:
                p += 3
        p += phase_bridge

        node["importance"] = round(p, 2)
        node["innovation_score"] = 1.0 if node.get("layer") == "innovation" else 0.0

    return graph


def select_key_integrated_graph(graph, max_nodes=80):
    """Return a connected, cross-phase, importance-ranked view of the integrated graph."""
    graph = rank_integrated_graph(graph)
    nodes = graph["nodes"]
    edges = graph["edges"]

    if not nodes or max_nodes is None or len(nodes) <= max_nodes:
        return graph

    node_map = {n["id"]: n for n in nodes}
    adjacency = {n["id"]: [] for n in nodes}
    for edge in edges:
        if edge["source"] in adjacency and edge["target"] in adjacency:
            adjacency[edge["source"]].append(edge)
            adjacency[edge["target"]].append(edge)

    root = next(
        (n for n in nodes if n.get("semantic_type") == "root" or n.get("id") == "knowledge_root"),
        max(nodes, key=lambda n: n.get("importance", 0)),
    )

    # Seeds ensure that the view visibly represents both reports and the innovations.
    seeds = [root["id"]]
    candidates = sorted(
        nodes,
        key=lambda n: (
            1 if n.get("source_phase") == "IMA+MA" else 0,
            1 if n.get("layer") == "innovation" else 0,
            n.get("importance", 0),
        ),
        reverse=True,
    )
    for node in candidates:
        if len(seeds) >= min(max_nodes, 14):
            break
        if node["id"] not in seeds and (
            node.get("source_phase") in {"IMA+MA", "IMA", "MA"}
            or node.get("layer") in {"innovation", "goal", "domain"}
        ):
            seeds.append(node["id"])

    selected = set(seeds)

    # Expand through strongest edges, keeping the graph connected where possible.
    while len(selected) < max_nodes:
        frontier = []
        for sid in selected:
            for edge in adjacency.get(sid, []):
                other = edge["target"] if edge["source"] == sid else edge["source"]
                if other in selected:
                    continue
                n = node_map[other]
                score = (
                    n.get("importance", 0)
                    + float(edge.get("weight", 1.0)) * 15
                    + (25 if n.get("source_phase") == "IMA+MA" else 0)
                )
                frontier.append((score, other))

        if not frontier:
            break
        frontier.sort(reverse=True)
        selected.add(frontier[0][1])

    # Fill remaining slots by importance.
    for node in sorted(nodes, key=lambda n: n.get("importance", 0), reverse=True):
        if len(selected) >= max_nodes:
            break
        selected.add(node["id"])

    selected_nodes = [n for n in nodes if n["id"] in selected]
    selected_edges = [
        e for e in edges
        if e["source"] in selected and e["target"] in selected
    ]
    return {"nodes": selected_nodes, "edges": selected_edges}


# =============================================================================
# COMPACT KNOWLEDGE ARCHITECTURE SYNTHESIS
# =============================================================================

def compact_knowledge_architecture_synthesis(graph, max_concepts=10, max_relations=8):
    """
    Replace low-value graph statistics with a compact semantic synthesis.

    This is deliberately deterministic and uses the already constructed
    integrated graph, so it adds report value without making another AI call.
    """
    graph = normalize_graph_data(graph)
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    if not nodes:
        return (
            "The integrated knowledge architecture contains no sufficiently "
            "structured graph data for a compact synthesis."
        )

    node_map = {n.get("id"): n for n in nodes}

    def node_score(node):
        try:
            return float(node.get("importance", 0))
        except (TypeError, ValueError):
            return 0.0

    ranked_nodes = sorted(
        nodes,
        key=lambda n: (node_score(n), n.get("label", "")),
        reverse=True,
    )

    key_concepts = []
    seen_labels = set()
    for node in ranked_nodes:
        label = str(node.get("label", "")).strip()
        if not label:
            continue
        normalized = label.casefold()
        if normalized in seen_labels:
            continue
        seen_labels.add(normalized)
        key_concepts.append(
            (
                label,
                str(node.get("level", "Meso")),
                str(node.get("semantic_type", "concept")),
            )
        )
        if len(key_concepts) >= max_concepts:
            break

    relation_counts = {}
    for edge in edges:
        rel = str(edge.get("rel_type", "ASSOCIATED"))
        relation_counts[rel] = relation_counts.get(rel, 0) + 1

    top_relations = sorted(
        relation_counts.items(),
        key=lambda item: (item[1], item[0]),
        reverse=True,
    )[:max_relations]

    level_counts = {}
    for node in nodes:
        level = str(node.get("level", "Meso"))
        level_counts[level] = level_counts.get(level, 0) + 1

    phase_counts = {}
    for node in nodes:
        phase = str(node.get("source_phase", "")).strip()
        if phase:
            phase_counts[phase] = phase_counts.get(phase, 0) + 1

    cross_phase_edges = 0
    for edge in edges:
        source = node_map.get(edge.get("source"), {})
        target = node_map.get(edge.get("target"), {})
        source_phase = str(source.get("source_phase", ""))
        target_phase = str(target.get("source_phase", ""))
        if source_phase and target_phase and source_phase != target_phase:
            cross_phase_edges += 1

    concept_text = ", ".join(
        f"**{label}** ({level})"
        for label, level, _ in key_concepts
    )

    relation_text = ", ".join(
        f"`{rel}` ({count})"
        for rel, count in top_relations
    )

    level_text = ", ".join(
        f"{level}: {count}"
        for level, count in sorted(level_counts.items())
    )

    if phase_counts:
        phase_text = ", ".join(
            f"{phase}: {count}"
            for phase, count in sorted(phase_counts.items())
        )
    else:
        phase_text = "Phase provenance is not explicitly encoded in the graph."

    bridge_text = (
        f"The integrated graph contains **{cross_phase_edges} explicit cross-phase "
        f"bridging relation(s)** between IMA and MA material."
        if cross_phase_edges
        else
        "The graph does not contain explicit cross-phase bridges in the current "
        "representation."
    )

    return f"""
### Compact Knowledge Architecture Synthesis

The integrated hierarchograph is organized as a **multi-level, hierarchical-associative knowledge structure** rather than as an isolated collection of concepts. The strongest semantic nodes are {concept_text}. Together they indicate the principal conceptual backbone of the synthesis.

The dominant relation vocabulary is {relation_text}. This shows how the architecture combines hierarchical relations with associative, UML, logical and operational relations rather than relying on a single relation type. The current level distribution is {level_text}.

The graph provenance is distributed as follows: {phase_text}. {bridge_text} This bridging is important because Phase 1 provides the structured knowledge substrate, while Phase 2 transforms that substrate through Mental Approaches into innovation-oriented structures.

The resulting architecture should therefore be read primarily through **conceptual centrality, hierarchical position, cross-domain association, operational transformation and IMA→MA bridging**, rather than through raw node or edge counts. The graph is consequently used as an analytical knowledge model and as a substrate for further synthesis and innovation.
""".strip()



# =============================================================================
# PRACTICAL INNOVATION GUIDANCE FROM IMA ARCHITECTURE
# =============================================================================

def build_practical_innovation_guidance(graph, max_items=6):
    """
    Convert the useful architectural information from the IMA graph into a
    compact deterministic briefing for Phase 2. This replaces the former
    architecture-report exposition with actionable innovation guidance.
    No additional AI call is made.
    """
    graph = normalize_graph_data(graph)
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    if not nodes:
        return "No structured IMA graph is available. Derive practical constraints and implementation requirements directly from Phase 1."

    def score(n):
        try:
            return float(n.get("importance", 0))
        except (TypeError, ValueError):
            return 0.0

    def label(n):
        return str(n.get("label", "")).strip()

    def is_type(n, *types):
        st = str(n.get("semantic_type", "")).lower()
        layer = str(n.get("layer", "")).lower()
        shape = str(n.get("shape", "")).lower()
        return any(t in st or t in layer or t in shape for t in types)

    groups = {
        "goals": [],
        "problems": [],
        "processes": [],
        "constraints": [],
        "states": [],
        "evidence": [],
        "innovations": [],
        "mental_approaches": [],
    }

    for n in nodes:
        text = " ".join([
            str(n.get("semantic_type", "")),
            str(n.get("layer", "")),
            str(n.get("shape", "")),
            label(n),
        ]).lower()
        if any(k in text for k in ("goal", "vision", "mission")):
            groups["goals"].append(n)
        if "problem" in text or "conflict" in text:
            groups["problems"].append(n)
        if any(k in text for k in ("process", "operation", "method")):
            groups["processes"].append(n)
        if any(k in text for k in ("constraint", "rule", "ethic")):
            groups["constraints"].append(n)
        if "state" in text:
            groups["states"].append(n)
        if any(k in text for k in ("evidence", "data", "fact")):
            groups["evidence"].append(n)
        if "innovation" in text:
            groups["innovations"].append(n)
        if n.get("semantic_type") == "mental-approach":
            groups["mental_approaches"].append(n)

    for key in groups:
        groups[key] = sorted(groups[key], key=score, reverse=True)[:max_items]

    operational_types = {
        "CAUSES", "ENABLES", "TRANSFORMS", "PRODUCES", "CONSUMES",
        "FEEDS", "TRIGGERS", "PRECEDES", "CONSTRAINS", "MEASURES",
        "VALIDATES", "IF-THEN",
    }
    node_map = {n.get("id"): n for n in nodes}
    operational_edges = []
    for e in edges:
        if str(e.get("rel_type", "")) in operational_types:
            a = node_map.get(e.get("source"), {})
            b = node_map.get(e.get("target"), {})
            if a and b:
                operational_edges.append((
                    float(e.get("weight", 1.0) or 1.0),
                    label(a),
                    str(e.get("rel_type", "")),
                    label(b),
                ))
    operational_edges.sort(reverse=True)

    def names(items):
        return ", ".join(label(n) for n in items[:max_items] if label(n)) or "none explicitly identified"

    edge_text = "; ".join(
        f"{a} → {rel} → {b}"
        for _, a, rel, b in operational_edges[:max_items]
        if a and b
    ) or "none explicitly identified"

    return f"""
PRACTICAL INNOVATION BRIEFING FROM THE IMA ARCHITECTURE
=======================================================
Use the following extracted architecture as an implementation-oriented design constraint for Phase 2. Do NOT reproduce it as a separate theoretical section in the final report.

1. Desired outcomes / strategic direction: {names(groups['goals'])}
2. Problems, gaps or conflicts to solve: {names(groups['problems'])}
3. Processes and mechanisms already indicated by the knowledge structure: {names(groups['processes'])}
4. Constraints, rules and ethical boundaries: {names(groups['constraints'])}
5. Relevant system states / transitions: {names(groups['states'])}
6. Evidence, facts or data anchors: {names(groups['evidence'])}
7. Existing innovation/transformation concepts: {names(groups['innovations'])}
8. Most relevant Mental Approaches already connected to the architecture: {names(groups['mental_approaches'])}
9. Strong operational relations to preserve or exploit: {edge_text}

PRACTICALITY REQUIREMENT
------------------------
For every proposed innovation, convert the architectural information above into concrete action. Explicitly identify: the user/problem served; the mechanism; required inputs and capabilities; dependencies; constraints; first prototype or pilot; measurable success criteria; responsible actor or organizational owner; principal implementation risk; mitigation; approximate implementation horizon; and the next executable step. Prefer innovations that can be tested, piloted, measured and progressively scaled over ideas that remain primarily conceptual.
""".strip()

# =============================================================================
# GRAPH DISPLAY LIMITER
# =============================================================================

def limit_graph_nodes(graph, max_nodes=80):
    """Limit the visual graph by integrated semantic importance, not insertion order."""
    graph = normalize_graph_data(graph)
    if not graph["nodes"]:
        return graph
    if max_nodes is None or max_nodes >= len(graph["nodes"]):
        return rank_integrated_graph(graph)
    return select_key_integrated_graph(graph, max_nodes=max_nodes)


# =============================================================================
# GRAPH RELATION VISIBILITY
# =============================================================================

# Default visual language: keep the graph understandable by prioritising
# thesaurus, UML and explicit logical relations. Operational relations remain
# available through an optional display switch.
PRIMARY_GRAPH_RELATIONS = {
    # Thesaurus / hierarchical-associative relations
    "TT", "BT", "NT", "RT", "EQ", "AS", "IN",
    # UML relations
    "Generalization", "Specialization", "Composition", "Aggregation",
    "Containment", "Realization", "Dependency", "Conflict",
    # Explicit logical relations
    "IF-THEN", "AND", "OR", "XOR", "NOT",
}

LOGICAL_GRAPH_RELATIONS = {
    "IF-THEN", "AND", "OR", "XOR", "NOT",
}

THESAURUS_GRAPH_RELATIONS = {
    "TT", "BT", "NT", "RT", "EQ", "AS", "IN",
}

UML_GRAPH_RELATIONS = {
    "Generalization", "Specialization", "Composition", "Aggregation",
    "Containment", "Realization", "Dependency", "Conflict",
}


def filter_graph_relations_for_display(graph, show_additional_relations=False):
    """
    Simplify the visual graph without changing the underlying knowledge graph.

    By default only thesaurus, UML and explicit logical relations are shown.
    Other operational relations can be enabled by the user when needed.
    Nodes are never deleted here; only visual edges are filtered.
    """
    graph = normalize_graph_data(graph)
    if show_additional_relations:
        return graph

    edges = [
        e for e in graph["edges"]
        if e.get("rel_type") in PRIMARY_GRAPH_RELATIONS
    ]
    return {
        "nodes": graph["nodes"],
        "edges": edges,
    }


# =============================================================================
# CYTOSCAPE HIERARCHOGRAPHIC RENDERER
# =============================================================================

def render_cytoscape_network(
    graph,
    layout_type="hierarchical",
    container_id="cy_canvas",
    max_nodes=None,
    show_additional_relations=False,
):
    graph = limit_graph_nodes(graph, max_nodes=max_nodes)
    graph = filter_graph_relations_for_display(
        graph,
        show_additional_relations=show_additional_relations,
    )

    elements = []

    for node in graph["nodes"]:
        elements.append({
            "data": {
                "id": node["id"],
                "label": node["label"],
                "color": node["color"],
                "shape": node["shape"],
                "size": node["size"],
                "description": node["description"],
                "layer": node["layer"],
                "level": node["level"],
                "semantic_type": node["semantic_type"],
                "state": node["state"],
                "source_phase": node.get("source_phase", ""),
                "importance": node.get("importance", 0.0),
            }
        })

    for edge in graph["edges"]:
        color = RELATION_COLORS.get(
            edge["rel_type"],
            "#adb5bd",
        )

        elements.append({
            "data": {
                "id": edge["id"],
                "source": edge["source"],
                "target": edge["target"],
                "rel_type": edge["rel_type"],
                "label": edge["rel_type"],
                "full_label": edge.get("full_label", RELATION_DEFINITIONS.get(edge["rel_type"], edge["rel_type"])),
                "color": color,
                "weight": edge["weight"],
            }
        })

    layout_configs = {
        "organic": """
        {
            name:'cose',
            animate:false,
            fit:true,
            padding:60,
            nodeRepulsion:180000,
            idealEdgeLength:150,
            edgeElasticity:100,
            nestingFactor:1.2,
            gravity:0.25,
            numIter:1800
        }
        """,

        "hierarchical": """
        {
            name:'breadthfirst',
            directed:true,
            circle:false,
            padding:70,
            spacingFactor:1.45,
            maximal:false,
            roots:'#knowledge_root'
        }
        """,

        "circular": """
        {
            name:'circle',
            padding:70,
            spacingFactor:1.1
        }
        """,

        "concentric": """
        {
            name:'concentric',
            padding:70,
            minNodeSpacing:65,
            concentric:function(node){
                var level=node.data('level');
                if(level==='Macro') return 3;
                if(level==='Meso') return 2;
                return 1;
            },
            levelWidth:function(){return 1;}
        }
        """,

        "grid": """
        {
            name:'grid',
            padding:70,
            avoidOverlap:true,
            avoidOverlapPadding:35,
            rows:Math.ceil(Math.sqrt(elements.length))
        }
        """,

        "operational": """
        {
            name:'breadthfirst',
            directed:true,
            circle:false,
            padding:90,
            spacingFactor:1.55,
            roots:'#knowledge_root'
        }
        """,
    }

    selected_layout = layout_configs.get(
        layout_type,
        layout_configs["hierarchical"],
    )

    safe_elements = json.dumps(
        elements,
        ensure_ascii=False,
    )

    html_doc = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.26.0/cytoscape.min.js"></script>
<style>
body {{
    margin:0;
    background:#ffffff;
    font-family:Arial,Helvetica,sans-serif;
}}

.wrapper {{
    position:relative;
    width:100%;
}}

#legend {{
    position:absolute;
    left:18px;
    top:18px;
    z-index:1000;
    background:rgba(255,255,255,.96);
    border:1px solid #d9dee5;
    border-radius:12px;
    padding:12px 15px;
    font-size:11px;
    line-height:1.55;
    box-shadow:0 4px 18px rgba(0,0,0,.10);
    max-width:330px;
}}

#toolbar {{
    position:absolute;
    right:18px;
    top:18px;
    z-index:1000;
    display:flex;
    gap:7px;
}}

.tool {{
    border:0;
    border-radius:8px;
    padding:9px 12px;
    background:#1d3557;
    color:white;
    font-weight:700;
    cursor:pointer;
}}

.tool:hover {{
    background:#457b9d;
}}

#zoomctl {{
    position:absolute;
    right:18px;
    top:64px;
    z-index:1000;
    display:flex;
    flex-direction:column;
    gap:7px;
}}

#cy {{
    width:100%;
    height:900px;
    background:#fbfcfe;
    border:1px solid #dfe5eb;
    border-radius:18px;
    box-shadow:0 8px 35px rgba(0,0,0,.08);
}}

.layer {{
    display:inline-block;
    margin-right:7px;
    font-weight:bold;
}}

.macro {{color:#1d3557;}}
.meso {{color:#7b2cb1;}}
.micro {{color:#2a9d8f;}}
</style>
</head>

<body>
<div class="wrapper">

<div id="legend">
<b>SIS HIERARCHOGRAPHY</b><br>
<span class="layer macro">● MACRO</span>
Goals · domains · principles<br>
<span class="layer meso">● MESO</span>
Processes · innovations · rules<br>
<span class="layer micro">● MICRO</span>
Facts · entities · states<br><br>
<b>Vertical:</b> hierarchy / taxonomy<br>
<b>Horizontal:</b> association / relation<br>
<b>Operational:</b> transformation / process<br>
<b>Cross-phase:</b> IMA ↔ MA bridge concepts are prioritized<br>
<b>Feedback:</b> cyclic system regulation<br>
<b>Primary edges:</b> thesaurus · UML · IF-THEN / AND / OR / XOR / NOT<br>
<b>Additional edges:</b> optional operational relations
</div>

<div id="toolbar">
<button class="tool" id="fit">FIT</button>
<button class="tool" id="hier">HIERARCHY</button>
<button class="tool" id="save">EXPORT PNG</button>
</div>

<div id="zoomctl">
<button class="tool" id="zoomin" title="Povečaj">➕ ZOOM</button>
<button class="tool" id="zoomout" title="Pomanjšaj">➖ ZOOM</button>
</div>

<div id="cy"></div>
</div>

<script>
const elements = {safe_elements};

const cy = cytoscape({{
    container: document.getElementById('cy'),
    elements: elements,

    minZoom: 0.05,
    maxZoom: 6,
    wheelSensitivity: 0.25,
    zoomingEnabled: true,
    userZoomingEnabled: true,
    panningEnabled: true,
    userPanningEnabled: true,

    style: [

        {{
            selector:'node',
            style:{{
                'label':'data(label)',
                'shape':'data(shape)',
                'background-color':'data(color)',
                'width':'data(size)',
                'height':'data(size)',
                'color':'#17202a',
                'font-size':'11px',
                'font-weight':'bold',
                'text-wrap':'wrap',
                'text-max-width':'110px',
                'text-valign':'center',
                'text-halign':'center',
                'border-width':2,
                'border-color':'#ffffff',
                'border-opacity':.95,
                'text-outline-color':'#ffffff',
                'text-outline-width':2
            }}
        }},

        {{
            selector:'node[level="Macro"]',
            style:{{
                'border-width':5,
                'border-color':'#1d3557',
                'font-size':'13px'
            }}
        }},

        {{
            selector:'node[level="Meso"]',
            style:{{
                'border-width':3,
                'border-color':'#7b2cb1'
            }}
        }},

        {{
            selector:'node[level="Micro"]',
            style:{{
                'border-width':2,
                'border-color':'#2a9d8f'
            }}
        }},

        {{
            selector:'node[shape="star"]',
            style:{{
                'border-width':6,
                'border-color':'#e9b949'
            }}
        }},

        {{
            selector:'node[shape="diamond"]',
            style:{{
                'border-width':4,
                'border-color':'#d97706'
            }}
        }},

        {{
            selector:'node[shape="octagon"]',
            style:{{
                'border-width':4,
                'border-color':'#8a6d1d'
            }}
        }},

        {{
            selector:'node[shape="triangle"]',
            style:{{
                'border-width':3,
                'border-color':'#167d70'
            }}
        }},

        {{
            selector:'edge',
            style:{{
                'width':'mapData(weight,0.3,2,1.5,6)',
                'line-color':'data(color)',
                'target-arrow-color':'data(color)',
                'target-arrow-shape':'vee',
                'curve-style':'bezier',
                'label':'data(label)',
                'font-size':'9px',
                'font-weight':'bold',
                'color':'#1a1a1a',
                'text-background-color':'#ffffff',
                'text-background-opacity':0.95,
                'text-background-padding':'3px',
                'text-rotation':'autorotate',
                'text-margin-y':-8,
                'opacity':0.92
            }}
        }},

        {{
            selector:'edge[rel_type="TT"]',
            style:{{
                'width':6,
                'target-arrow-shape':'triangle',
                'line-color':'#14213d'
            }}
        }},

        {{
            selector:'edge[rel_type="BT"]',
            style:{{
                'width':5,
                'target-arrow-shape':'triangle',
                'line-color':'#1d3557'
            }}
        }},

        {{
            selector:'edge[rel_type="NT"]',
            style:{{
                'width':4,
                'target-arrow-shape':'vee',
                'line-color':'#457b9d'
            }}
        }},

        {{
            selector:'edge[rel_type="RT"]',
            style:{{
                'width':2,
                'line-style':'dotted',
                'target-arrow-shape':'none',
                'line-color':'#2a9d8f'
            }}
        }},

        {{
            selector:'edge[rel_type="EQ"]',
            style:{{
                'width':5,
                'line-style':'dashed',
                'target-arrow-shape':'none',
                'line-color':'#f1c40f'
            }}
        }},

        {{
            selector:'edge[rel_type="AS"]',
            style:{{
                'width':3,
                'line-style':'dashed',
                'line-color':'#7b2cb1'
            }}
        }},

        {{
            selector:'edge[rel_type="IN"]',
            style:{{
                'width':3,
                'target-arrow-shape':'circle',
                'line-color':'#0077b6'
            }}
        }},

        {{
            selector:'edge[rel_type="Generalization"]',
            style:{{
                'width':4,
                'target-arrow-shape':'triangle',
                'target-arrow-fill':'hollow',
                'line-color':'#e63946'
            }}
        }},

        {{
            selector:'edge[rel_type="Specialization"]',
            style:{{
                'width':3,
                'line-style':'dashed',
                'target-arrow-shape':'triangle',
                'target-arrow-fill':'hollow',
                'line-color':'#111111'
            }}
        }},

        {{
            selector:'edge[rel_type="Composition"]',
            style:{{
                'width':5,
                'source-arrow-shape':'diamond',
                'source-arrow-fill':'filled',
                'line-color':'#d62828'
            }}
        }},

        {{
            selector:'edge[rel_type="Aggregation"]',
            style:{{
                'width':4,
                'source-arrow-shape':'diamond',
                'source-arrow-fill':'hollow',
                'line-color':'#f77f00'
            }}
        }},

        {{
            selector:'edge[rel_type="Containment"]',
            style:{{
                'width':4,
                'target-arrow-shape':'circle',
                'target-arrow-fill':'hollow',
                'line-color':'#1d3557'
            }}
        }},

        {{
            selector:'edge[rel_type="Realization"]',
            style:{{
                'width':4,
                'line-style':'dashed',
                'target-arrow-shape':'triangle',
                'target-arrow-fill':'hollow',
                'line-color':'#e63946'
            }}
        }},

        {{
            selector:'edge[rel_type="Dependency"]',
            style:{{
                'width':3,
                'line-style':'dashed',
                'target-arrow-shape':'vee',
                'line-color':'#6c757d'
            }}
        }},

        {{
            selector:'edge[rel_type="Conflict"]',
            style:{{
                'width':6,
                'line-color':'#b91d1d',
                'target-arrow-shape':'triangle-cross',
                'source-arrow-shape':'triangle-cross',
                'target-arrow-color':'#b91d1d',
                'source-arrow-color':'#b91d1d'
            }}
        }},

        {{
            selector:'edge[rel_type="AND"]',
            style:{{
                'width':5,
                'line-color':'#008000',
                'target-arrow-shape':'triangle'
            }}
        }},

        {{
            selector:'edge[rel_type="OR"]',
            style:{{
                'width':3,
                'line-style':'dashed',
                'line-color':'#00a6d6',
                'target-arrow-shape':'vee'
            }}
        }},

        {{
            selector:'edge[rel_type="XOR"]',
            style:{{
                'width':4,
                'line-style':'dashed',
                'line-color':'#ff8c00',
                'target-arrow-shape':'diamond'
            }}
        }},

        {{
            selector:'edge[rel_type="NOT"]',
            style:{{
                'width':4,
                'line-style':'dashed',
                'line-color':'#ff0000',
                'target-arrow-shape':'tee'
            }}
        }},

        {{
            selector:'edge[rel_type="IF-THEN"]',
            style:{{
                'width':4,
                'line-color':'#d4a900',
                'target-arrow-shape':'triangle'
            }}
        }},

        {{
            selector:'edge[rel_type="CAUSES"]',
            style:{{
                'width':5,
                'line-color':'#c1121f',
                'target-arrow-shape':'triangle'
            }}
        }},

        {{
            selector:'edge[rel_type="TRANSFORMS"]',
            style:{{
                'width':5,
                'line-color':'#8a2be2',
                'target-arrow-shape':'triangle'
            }}
        }},

        {{
            selector:'edge[rel_type="PRODUCES"]',
            style:{{
                'width':4,
                'line-color':'#218739',
                'target-arrow-shape':'triangle'
            }}
        }},

        {{
            selector:'edge[rel_type="FEEDS"]',
            style:{{
                'width':4,
                'line-color':'#0077b6',
                'target-arrow-shape':'vee'
            }}
        }},

        {{
            selector:'edge[rel_type="FEEDBACK"]',
            style:{{
                'width':5,
                'line-color':'#6a4c93',
                'line-style':'dashed',
                'target-arrow-shape':'vee',
                'curve-style':'unbundled-bezier',
                'control-point-distances':[60,-60]
            }}
        }},

        {{
            selector:'edge[rel_type="POSITIVE-FEEDBACK"]',
            style:{{
                'width':5,
                'line-color':'#008000',
                'target-arrow-shape':'vee',
                'curve-style':'unbundled-bezier',
                'control-point-distances':[70]
            }}
        }},

        {{
            selector:'edge[rel_type="NEGATIVE-FEEDBACK"]',
            style:{{
                'width':5,
                'line-color':'#c77d00',
                'target-arrow-shape':'vee',
                'curve-style':'unbundled-bezier',
                'control-point-distances':[-70]
            }}
        }},

        {{
            selector:'edge[rel_type="PRECEDES"]',
            style:{{
                'width':3,
                'line-color':'#577590',
                'target-arrow-shape':'vee'
            }}
        }},

        {{
            selector:'edge[rel_type="CONSTRAINS"]',
            style:{{
                'width':4,
                'line-style':'dashed',
                'line-color':'#6c757d',
                'target-arrow-shape':'tee'
            }}
        }},

        {{
            selector:'edge[rel_type="MEASURES"]',
            style:{{
                'width':3,
                'line-style':'dotted',
                'line-color':'#118ab2',
                'target-arrow-shape':'vee'
            }}
        }},

        {{
            selector:'edge[rel_type="VALIDATES"]',
            style:{{
                'width':4,
                'line-color':'#06a77d',
                'target-arrow-shape':'triangle'
            }}
        }},

        {{
            selector:'edge[rel_type="ENABLES"]',
            style:{{
                'width':4,
                'line-color':'#2a9d8f',
                'target-arrow-shape':'triangle'
            }}
        }},

        {{
            selector:'edge[rel_type="CONSUMES"]',
            style:{{
                'width':4,
                'line-color':'#9b2226',
                'target-arrow-shape':'triangle'
            }}
        }},

        {{
            selector:'edge[rel_type="TRIGGERS"]',
            style:{{
                'width':4,
                'line-color':'#e76f51',
                'target-arrow-shape':'triangle'
            }}
        }},

        {{
            selector:':selected',
            style:{{
                'border-color':'#000000',
                'border-width':7,
                'line-color':'#000000',
                'target-arrow-color':'#000000',
                'opacity':1
            }}
        }}
    ],

    layout:{selected_layout}
}});

cy.ready(function(){{
    cy.fit(null,80);
}});

cy.on('tap','node',function(evt){{
    const n=evt.target;
    const d=n.data();

    const level=d.level || '';
    const layer=d.layer || '';
    const state=d.state || '';

    let text =
        '<b>'+escapeHtml(d.label)+'</b><br><br>'+
        '<b>Level:</b> '+escapeHtml(level)+'<br>'+
        '<b>Layer:</b> '+escapeHtml(layer)+'<br>'+
        '<b>Semantic type:</b> '+escapeHtml(d.semantic_type||'')+'<br>'+
        (state ? '<b>State:</b> '+escapeHtml(state)+'<br>' : '')+
        '<br>'+escapeHtml(d.description||'');

    alert(text.replace(/<br>/g,'\\n').replace(/<[^>]*>/g,''));
}});

cy.on('tap','edge',function(evt){{
    const e=evt.target;
    const d=e.data();
    const text =
        'Relation: '+ (d.rel_type || '') + '\\n' +
        'Meaning: ' + (d.full_label || d.label || '') + '\\n' +
        'Weight: ' + (d.weight || 1);
    alert(text);
}});

document.getElementById('fit').onclick=function(){{
    cy.fit(null,80);
}};

document.getElementById('hier').onclick=function(){{
    cy.layout({{
        name:'breadthfirst',
        directed:true,
        circle:false,
        padding:90,
        spacingFactor:1.35,
        roots:'#knowledge_root',
        animate:false
    }}).run();
}};

document.getElementById('zoomin').onclick=function(){{
    const center = {{
        x: cy.width()/2,
        y: cy.height()/2
    }};
    cy.zoom({{
        level: cy.zoom() * 1.25,
        renderedPosition: center
    }});
}};

document.getElementById('zoomout').onclick=function(){{
    const center = {{
        x: cy.width()/2,
        y: cy.height()/2
    }};
    cy.zoom({{
        level: cy.zoom() * 0.8,
        renderedPosition: center
    }});
}};

document.getElementById('save').onclick=function(){{
    const png=cy.png({{
        full:true,
        bg:'white',
        scale:2
    }});

    const link=document.createElement('a');
    const stamp=new Date().toISOString()
        .replace(/[:.]/g,'-')
        .slice(0,19);

    link.href=png;
    link.download='SIS_Hierarchograph_'+stamp+'.png';
    link.click();
}};

function escapeHtml(value){{
    return String(value)
        .replace(/&/g,'&amp;')
        .replace(/</g,'&lt;')
        .replace(/>/g,'&gt;')
        .replace(/"/g,'&quot;')
        .replace(/'/g,'&#039;');
}}
</script>
</body>
</html>
"""

    components.html(
        html_doc,
        height=950,
        scrolling=False,
    )


# =============================================================================
# AI PROMPTS – NATURAL NARRATIVE SYNTHESIS
# =============================================================================

def build_phase1_system_prompt():
    ima_nodes = "\n".join(
        f"- {name}: {meta.get('desc', '')}"
        for name, meta in HUMAN_THINKING_METAMODEL["nodes"].items()
    )
    ima_relations = "\n".join(
        f"- {s} --{r}--> {t}"
        for s, t, r in HUMAN_THINKING_METAMODEL["relations"]
    )

    return f"""
You are the SIS Lead Knowledge Synthesizer, Hierarchologist and IMA Architect.

PHASE 1 — IMA KNOWLEDGE SYNTHESIS
=================================
IMA means the COMPLETE METAMODEL OF HUMAN THINKING. Phase 1 is therefore not
merely a literature summary. It is a professional, structured reconstruction
of the knowledge space through the full Human Thinking Metamodel (IMA),
supported by multidimensional thesaurus, polyhierarchy, UML, hierarchical-
associative logic, operational logic, epistemic relations, system states and
hierarchography.

The complete IMA architecture is active. Do not select only a few cognitive
components. Integrate the complete supplied IMA metamodel where relevant:

IMA NODES:
{ima_nodes}

IMA RELATIONS:
{ima_relations}

REPORT QUALITY
==============
Produce a professional scholarly report suitable for an expert reader.
Use clear section headings and substantial continuous prose. The report must
contain, in this order:

1. Executive synthesis — the central finding of the inquiry.
2. Scope, assumptions and epistemic status — distinguish established
   knowledge, interpretation, inference and unresolved uncertainty.
3. Conceptual and scientific landscape — define and relate the major concepts.
4. IMA reconstruction — show how the inquiry maps onto the complete human
   thinking metamodel: identity, memory, mission, vision, goals, problem,
   ethics, rules, decision-making, problem solving, conflict, knowledge,
   tools, experience, classification, psychological/social aspects and the
   hierarchical-associative system.
5. Polyhierarchical knowledge architecture — explain the most important
   simultaneous taxonomic, part-whole, process and associative structures.
6. Operational and systemic logic — explain inputs, processes, transformations,
   outputs, states, feedback, constraints and causal mechanisms.
7. Cross-disciplinary synthesis — identify meaningful bridges among the
   selected sciences, paradigms and structural models.
8. Critical assessment — expose contradictions, gaps, assumptions and
   scientific/operational limitations.
9. Strategic knowledge implications — identify the knowledge structures that
   Phase 2 should transform, without proposing the innovations themselves.
10. Conclusion.

Do NOT solve the innovation objective in Phase 1. Phase 1 creates the
knowledge substrate from which Phase 2 will innovate.

STYLE
=====
Professional, precise, analytical and readable. Avoid keyword dumps and
telegraphic prose. Bullets may be used only for compact metadata; the
substantive report must be continuous academic prose.

SEMANTIC GRAPH
==============
After the report, output the exact marker:

### IMA_SEMANTIC_GRAPH_JSON

Then output valid JSON with:
{{
  "nodes": [...],
  "edges": [...]
}}

The IMA graph should contain approximately 18–45 of the MOST IMPORTANT
concepts from the report, not every word. It must represent actual concepts
from the report and the IMA architecture.

Every node:
id, label, shape, color, description, layer, level, semantic_type, state,
source_phase

Every edge:
id, source, target, rel_type, label, weight, direction

Use a balanced mixture of TT, BT, NT, RT, EQ, AS, IN, UML relations,
logical operators, operational relations and feedback relations where
semantically justified. Never manufacture a relation merely to satisfy a
quota.

GEOMETRY:
star=mission/vision/goal; hexagon=science/domain; diamond=transformation or
synthesis; triangle=process/method; octagon=rule/constraint/conflict;
ellipse=human/agent; rectangle=concept/fact/evidence; round-rectangle=state;
barrel=data/evidence repository.

LEVEL:
Macro, Meso or Micro.

The JSON must be the final content of the response.
Do not put markdown inside JSON. No comments. No trailing commas.

KNOWLEDGE ARCHITECTURE REFERENCE
================================
Use the architecture context supplied with the user input as the governing
semantic vocabulary.
"""


def build_phase2_system_prompt(architecture_context):
    ma_nodes = "\n".join(
        f"- {name}: {description}"
        for name, description in MENTAL_APPROACHES_ONTOLOGY.items()
    )

    return f"""
You are the SIS Lead Innovation Architect, MA Architect and Hierarchographist.

PHASE 2 — MA INNOVATION ARCHITECTURE
====================================
MA means ALL MENTAL APPROACHES. Phase 2 must therefore activate the complete
Mental Approaches architecture, not merely the user-selected ideation
techniques. The selected ideation frameworks are supplementary tools; they do
not replace MA.

COMPLETE MENTAL APPROACHES
==========================
{ma_nodes}

PURPOSE
=======
Use the completed Phase 1 IMA knowledge synthesis as the knowledge substrate
and transform it exclusively in response to the explicit Innovation Objective.
Do not repeat Phase 1 as background. Find what can be invented, recombined,
reframed, improved, operationalized or implemented.

VISIONARY BUT REALISTIC INNOVATION
==================================
Every proposed innovation must satisfy BOTH criteria:
1. VISIONARY: it should create a meaningful new configuration, capability,
   relationship, service, process, technology or conceptual architecture.
2. REALIZABLE: it must remain within a defensible path of technical,
   organizational, economic, ethical/legal and temporal feasibility.

Do not confuse visionary with speculative. Avoid science-fiction claims,
unsupported technological promises and impossible implementation assumptions.

For each major innovation, explicitly reason about:
- novelty and value;
- the problem/gap it addresses;
- mechanism of action;
- the Mental Approaches that generated it;
- required knowledge, technology and organizational capabilities;
- feasibility across technical, organizational, economic, ethical/legal and
  temporal dimensions;
- principal risks and failure modes;
- validation or pilot strategy;
- first practical implementation step;
- expected near-term, medium-term and long-term horizon.

PROFESSIONAL PHASE 2 REPORT
===========================
Produce a professional innovation strategy report with these sections:

1. Executive innovation thesis.
2. Transformation logic from Phase 1 to Phase 2.
3. Opportunity landscape and unmet potential.
4. MA synthesis — explicitly show how multiple Mental Approaches interact,
   with ALL Mental Approaches considered and the most productive ones selected
   for each innovation.
5. Innovation portfolio — present 3–7 genuinely differentiated solutions.
6. For each solution: concept, novelty, mechanism, value, MA combination,
   prerequisites, feasibility, risks, validation and implementation path.
7. Vision-to-realization roadmap — distinguish near (0–2 years), medium
   (3–5 years) and long (6–10+ years) horizons where appropriate.
8. Portfolio comparison and prioritization.
9. Strategic recommendation.
10. Conclusion.

Use concise tables only where they materially improve comparison; otherwise
use strong continuous analytical prose.

FEASIBILITY DISCIPLINE
======================
Rate each innovation on a 1–5 scale for:
technical, organizational, economic, ethical/legal and temporal feasibility.
Give an overall feasibility judgment and explain it. An innovation with low
feasibility may remain in the visionary portfolio, but it must be explicitly
labelled as exploratory rather than presented as immediately implementable.

SEMANTIC GRAPH
==============
After the report, output:

### MA_SEMANTIC_GRAPH_JSON

Then valid JSON with:
{{
  "nodes": [...],
  "edges": [...]
}}

The MA graph should contain approximately 20–55 of the most important
innovation concepts, IMA concepts reused by the innovation, Mental Approaches,
processes, states, constraints, goals and evidence. It must explicitly
connect innovations back to concepts from Phase 1.

Every diamond innovation node MUST contain in its description at least three
Mental Approaches used in its synthesis. Preferably identify more when they
genuinely contributed.

Every node:
id, label, shape, color, description, layer, level, semantic_type, state,
source_phase

Every edge:
id, source, target, rel_type, label, weight, direction

Use semantically justified thesaurus, UML, logical, operational and feedback
relations. Do not force artificial relation diversity.

The graph is NOT a mind map. It is a polyhierarchical semantic architecture.

KNOWLEDGE ARCHITECTURE REFERENCE
================================
{architecture_context}
"""


# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:

    st.markdown(
        '<div class="sidebar-logo-container">'
        f'<img src="data:image/svg+xml;base64,{get_svg_base64(SVG_3D_RELIEF)}" width="220">'
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div class="date-badge">{SYSTEM_DATE.upper()}</div>',
        unsafe_allow_html=True,
    )

    st.header("⚙️ SYSTEM CONTROL")

    google_api_key = st.text_input(
        "Google AI (Gemini) API Key",
        type="password",
        key="google_api_key_v230",
    )

    st.header("🤗 HUGGING FACE")

    huggingface_api_key = st.text_input(
        "Hugging Face API Key",
        type="password",
        key="hf_api_key_v230",
    )

    st.caption(
        "Qwen2.5-72B-Instruct uporablja Hugging Face Inference Providers."
    )

    st.subheader("🤖 Sequential Model Selection")

    p1_label = st.selectbox(
        "Phase 1 Model — IMA Knowledge Synthesis",
        GEMINI_MODEL_LABELS,
        index=1,
        key="p1_model_v230",
    )

    p1_model = GEMINI_MODEL_CATALOG[p1_label]

    p2_label = st.selectbox(
        "Phase 2 Model — MA Innovation Architecture",
        GEMINI_MODEL_LABELS,
        index=0,
        key="p2_model_v230",
    )

    p2_model = GEMINI_MODEL_CATALOG[p2_label]

    st.divider()

    st.subheader("🎨 HIERARCHOGRAPHIC VIEW")

    graph_perspective = st.selectbox(
        "Visual Architecture",
        [
            "hierarchical",
            "operational",
            "organic",
            "concentric",
            "circular",
            "grid",
        ],
        index=0,
        key="graph_perspective_v231",
    )

    graph_node_limit = st.slider(
        "🔢 Graph nodes to display",
        min_value=10,
        max_value=200,
        value=80,
        step=5,
        key="graph_node_limit_v231",
        help="Limits the number of displayed nodes while preserving the most structurally important nodes and their valid relations. Changing this slider updates the graph immediately, including after a synthesis/innovation run.",
    )

    st.caption(
        "Polyhierarchy + semantic association + operational transformations "
        "+ system states. Use the slider to control graph density — it "
        "applies live to the current synthesis/innovation graph as well."
    )

    st.divider()

    col_a, col_b = st.columns(2)

    with col_a:
        if st.button(
            "♻️ RESET",
            key="reset_v230",
        ):
            for key in list(st.session_state.keys()):
                del st.session_state[key]

            st.rerun()

    with col_b:
        if st.button(
            "📖 GUIDE",
            key="guide_v230",
        ):
            st.session_state.show_user_guide = (
                not st.session_state.show_user_guide
            )
            st.rerun()

    st.divider()

    st.subheader("🌐 EXTERNAL CONNECTORS")

    st.link_button(
        "📂 GitHub Repository",
        "https://github.com/",
        use_container_width=True,
    )

    st.link_button(
        "🆔 ORCID Registry",
        "https://orcid.org/",
        use_container_width=True,
    )

    st.link_button(
        "🎓 Google Scholar",
        "https://scholar.google.com/",
        use_container_width=True,
    )

    st.divider()

    st.subheader("📚 KNOWLEDGE EXPLORER")

    with st.expander("🧬 Multidimensional Thesaurus"):
        for dimension, terms in THESAURUS_ONTOLOGY["dimensions"].items():
            st.markdown(
                f"**{dimension.upper()}**: "
                + ", ".join(terms)
            )

    with st.expander("🌳 Polyhierarchical Ontology"):
        for hierarchy in POLYHIERARCHY["hierarchies"]:
            st.markdown(
                f"**{hierarchy['id']} — {hierarchy['name']}**"
            )
            st.markdown(
                f"Root: `{hierarchy['root']}`"
            )
            st.markdown(
                "Relations: "
                + ", ".join(hierarchy["relations"])
            )

    with st.expander("📐 UML Metamodel"):
        for cls, attrs in UML_METAMODEL["classes"].items():
            st.markdown(
                f"**{cls}** → "
                + ", ".join(attrs)
            )

        st.markdown("---")

        for rel, meaning in UML_METAMODEL["relationships"].items():
            st.markdown(
                f"**{rel}** — {meaning}"
            )

    with st.expander("🔄 Operational Logic"):
        for key, value in HIERARCHOLOGY_ONTOLOGY[
            "operational_logic"
        ].items():
            st.markdown(
                f"**{key}** — {value}"
            )

    with st.expander("🧠 Human Thinking Metamodel"):
        for label, meta in HUMAN_THINKING_METAMODEL["nodes"].items():
            st.markdown(
                f"**{label}** ({meta.get('shape','')}) — "
                f"{meta.get('desc','')}"
            )

        st.markdown("---")

        for source, target, relation in HUMAN_THINKING_METAMODEL["relations"]:
            st.markdown(
                f"**{source}** `{relation}` **{target}**"
            )

    with st.expander("🧠 Mental Approaches"):
        for name, description in MENTAL_APPROACHES_ONTOLOGY.items():
            st.markdown(
                f"**{name}** — {description}"
            )

    with st.expander("🔬 Science Taxonomy"):
        for field in sorted(SCIENCE_FIELDS):
            st.markdown(
                f"• **{field}**"
            )

    with st.expander("🔗 Relation Vocabulary"):
        for rel, meaning in RELATION_DEFINITIONS.items():
            st.markdown(
                f"**{rel}** — {meaning}"
            )


# =============================================================================
# MAIN HEADER
# =============================================================================

st.markdown(
    '<h1 class="main-header-gradient">'
    "🧱 SIS Universal Knowledge Synthesizer"
    "</h1>",
    unsafe_allow_html=True,
)

st.markdown(
    f"**Multidimensional Knowledge Architecture** | "
    f"**Polyhierarchy · UML · Hierarchical-Associative Logic · "
    f"Operational Logic · Hierarchography** | {SYSTEM_DATE}"
)


if st.session_state.show_user_guide:

    st.info(
        """
### SIS Knowledge Synthesis → Innovation Workflow

**PHASE 1 — KNOWLEDGE SYNTHESIS**
The system synthesizes the inquiry into a rich multidimensional knowledge
structure written as continuous academic prose (introduction → exposition →
conclusion), not as telegraphic bullet lists.

**PHASE 2 — INNOVATION OBJECTIVE**
The system works exclusively on the stated innovation objective and transforms
the Phase 1 knowledge synthesis into an innovation-oriented solution space.

**Thesaurus**
Concepts are expanded into terms, broader terms, narrower terms,
related terms, equivalences and associative relations.

**3. Polyhierarchical Ontology**
Concepts may participate in multiple legitimate hierarchies.

**4. UML / Metamodel**
Entities, concepts, goals, problems, processes, rules, innovations,
evidence and system states are structurally modeled.

**5. Hierarchical-Associative Logic**
Vertical hierarchy is combined with lateral semantic association.

**6. Operational Logic**
Inputs, processes, transformations, outputs, constraints and transitions
are represented explicitly.

**7. Feedback**
Where justified, positive and negative feedback loops are represented
as directed cycles.

**8. Human Thinking Metamodel + Mental Approaches**
The full cognitive metamodel and the full set of Mental Approaches are always
activated as real nodes and relations in the graph.

**9. Hierarchography**
The complete architecture is rendered as a multidimensional graph.
You can select which components (innovations, science fields, paradigms,
structural models, etc.) you want to see under the graph.
"""
    )


# =============================================================================
# ARCHITECTURE BOXES
# =============================================================================

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(
        """
<div class="metamodel-box">
<b>🌳 THESAURUS + POLYHIERARCHY</b><br>
Multidimensional semantic organization with TT, BT, NT, RT, EQ, AS and IN.
Multiple simultaneous hierarchical contexts are supported.
</div>
""",
        unsafe_allow_html=True,
    )

with c2:
    st.markdown(
        """
<div class="ontology-box">
<b>📐 UML + METAMODEL</b><br>
Entities, concepts, goals, problems, processes, rules, innovations,
evidence and states are modeled using structural relationships.
</div>
""",
        unsafe_allow_html=True,
    )

with c3:
    st.markdown(
        """
<div class="operational-box">
<b>⚙️ OPERATION + TRANSFORMATION</b><br>
Inputs, processes, transformations, outputs, conditions, state transitions
and feedback loops form the operational layer of the knowledge system.
</div>
""",
        unsafe_allow_html=True,
    )


# =============================================================================
# CONFIGURATION
# =============================================================================

st.markdown("### 🛠️ CONFIGURE KNOWLEDGE SYNTHESIS")

r1c1, r1c2, r1c3 = st.columns([1.5, 2, 1])

with r1c1:
    target_authors = st.text_input(
        "👤 Authors for ORCID Analysis",
        placeholder="Karl Petrič, Samo Kralj, Teodor Petrič",
        key="authors_v230",
    )

with r1c2:
    selected_sciences = st.multiselect(
        "🔬 Science Fields",
        sorted(SCIENCE_FIELDS.keys()),
        default=[
            "Physics",
            "Psychology",
            "Sociology",
        ],
        key="sciences_v230",
    )

with r1c3:
    expertise = st.select_slider(
        "🎓 Expertise Level",
        ["Novice", "Intermediate", "Expert"],
        value="Expert",
        key="expertise_v230",
    )


r2c1, r2c2, r2c3 = st.columns(3)

with r2c1:
    selected_paradigms = st.multiselect(
        "🧠 Scientific Paradigms",
        list(SCIENTIFIC_PARADIGMS.keys()),
        default=["Rationalism"],
        key="paradigms_v230",
    )

with r2c2:
    selected_models = st.multiselect(
        "📐 Structural Models",
        list(STRUCTURAL_MODELS.keys()),
        default=["Concepts"],
        key="models_v230",
    )

with r2c3:
    goal_context = st.selectbox(
        "🎯 Strategic Knowledge Goal",
        [
            "Scientific Research",
            "Problem Solving",
            "Educational",
            "Policy Making",
            "Interdisciplinary Synthesis",
            "Ontology Construction",
            "System Design",
        ],
        key="goal_v230",
    )


st.divider()


# =============================================================================
# INNOVATION STRATEGY
# =============================================================================

st.markdown("### 🧬 KNOWLEDGE TRANSFORMATION STRATEGY")

selected_techniques = st.multiselect(
    "Additional Ideation Frameworks (supplementary to ALL Mental Approaches)",
    list(IDEATION_TECHNIQUES.keys()),
    default=["First Principles", "Lateral Thinking"],
    key="techniques_v230",
)

if selected_techniques:

    combined = " | ".join(
        f"**{x}**: {IDEATION_TECHNIQUES[x]}"
        for x in selected_techniques
    )

    st.info(
        f"**Active transformation strategy:** {combined}"
    )

else:
    st.warning(
        "Select at least one knowledge transformation framework."
    )


st.divider()


# =============================================================================
# DUAL INQUIRY
# =============================================================================

col_inq1, col_inq2, col_inq3 = st.columns([2, 2, 1])

with col_inq1:

    user_query = st.text_area(
        "🧠 PHASE 1 — IMA KNOWLEDGE SYNTHESIS",
        placeholder=(
             "Enter the scientific, conceptual or systemic inquiry from which the "
            "system should synthesize a rich body of structured knowledge."
        ),
        height=230,
        key="user_query_v230",
    )


with col_inq2:

    idea_query = st.text_area(
        "💡 PHASE 2 — MA INNOVATION ARCHITECTURE",
        placeholder=(
             "Define exclusively what should be invented, transformed, improved, "
            "connected, operationalized or otherwise innovated."
        ),
        height=230,
        key="idea_query_v230",
    )


with col_inq3:

    uploaded_file = st.file_uploader(
        "📂 ATTACH DATA (.txt)",
        type=["txt"],
        key="file_v230",
    )

    file_content = ""

    if uploaded_file:

        try:
            file_content = (
                uploaded_file
                .read()
                .decode("utf-8")
            )

            st.success(
                f"📎 {uploaded_file.name}"
            )

            with st.expander("File Preview"):
                st.text(
                    file_content[:3000]
                )

        except Exception as exc:
            st.error(
                f"Error reading file: {exc}"
            )


# =============================================================================
# EXECUTION — IMA → MA TWO-PHASE PIPELINE
# =============================================================================

if st.button(
    "🚀 EXECUTE IMA → MA KNOWLEDGE & INNOVATION PIPELINE",
    use_container_width=True,
    key="execute_v2400",
):

    p1_is_hf = p1_model.startswith("hf:")
    p2_is_hf = p2_model.startswith("hf:")

    google_required = (not p1_is_hf or not p2_is_hf)
    hf_required = (p1_is_hf or p2_is_hf)

    if google_required and not google_api_key:
        st.error("❌ Google AI API key is required for the selected Google model.")
        st.stop()

    if hf_required and not huggingface_api_key:
        st.error("❌ Hugging Face API key is required for Qwen2.5-72B-Instruct.")
        st.stop()

    if not user_query.strip():
        st.warning("⚠️ Phase 1 — IMA knowledge synthesis inquiry is required.")
        st.stop()

    if not idea_query.strip():
        st.warning("⚠️ Phase 2 — MA innovation objective is required.")
        st.stop()

    if not selected_sciences:
        st.warning("⚠️ Select at least one science field.")
        st.stop()

    try:
        architecture_context = build_knowledge_architecture_context(
            selected_sciences,
            selected_paradigms,
            selected_models,
            selected_techniques,
        )

        file_context = (
            "\n\nSOURCE FILE CONTEXT:\n" + file_content
            if file_content else ""
        )

        biblio_data = ""
        if target_authors:
            with st.spinner("📚 Accessing ORCID bibliographic metadata..."):
                biblio_data = fetch_author_bibliographies(target_authors)

        biblio_context = (
            "\n\nAUTHOR RESEARCH BACKGROUND:\n" + biblio_data
            if biblio_data else ""
        )

        full_input = f"""
USER INQUIRY:
{user_query}

INNOVATION OBJECTIVE:
{idea_query}

EXPERTISE:
{expertise}

STRATEGIC GOAL:
{goal_context}

SELECTED SCIENCE FIELDS:
{", ".join(selected_sciences)}

SELECTED SCIENTIFIC PARADIGMS:
{", ".join(selected_paradigms) if selected_paradigms else "None specified"}

SELECTED STRUCTURAL MODELS:
{", ".join(selected_models) if selected_models else "None specified"}

SUPPLEMENTARY IDEATION FRAMEWORKS:
{", ".join(selected_techniques) if selected_techniques else "None specified"}

IMPORTANT:
The complete IMA architecture is mandatory in Phase 1.
ALL Mental Approaches are mandatory in Phase 2.
The supplementary ideation frameworks above are not a substitute for MA.

{file_context}
{biblio_context}
"""

        gemini_client = None
        if google_required:
            gemini_client = genai.Client(api_key=google_api_key)

        # ---------------------------------------------------------------------
        # PHASE 1 — IMA
        # ---------------------------------------------------------------------
        p1_provider_name = (
            "Hugging Face / Qwen2.5-72B-Instruct"
            if p1_is_hf else f"Google / {p1_model}"
        )

        with st.spinner(
            f"PHASE 1 — IMA Complete Human Thinking Metamodel synthesis with {p1_provider_name}..."
        ):
            phase1_result = gemini_generate(
                gemini_client,
                p1_model,
                build_phase1_system_prompt(),
                architecture_context + "\n\n" + full_input,
                temperature=0.40,
                top_p=0.92 if p1_is_hf else 0.88,
                huggingface_api_key=huggingface_api_key,
            )

        phase1_graph = extract_json_object(phase1_result) or {"nodes": [], "edges": []}
        phase1_graph = normalize_graph_data(phase1_graph)

        # Deterministic IMA enrichment.
        phase1_graph = enrich_graph_with_architecture(
            phase1_graph, selected_sciences
        )
        phase1_graph = enrich_graph_with_human_thinking_metamodel(
            phase1_graph
        )
        phase1_graph = normalize_graph_data(phase1_graph)

        # ---------------------------------------------------------------------
        # PHASE 2 — MA
        # ---------------------------------------------------------------------
        p2_provider_name = (
            "Hugging Face / Qwen2.5-72B-Instruct"
            if p2_is_hf else f"Google / {p2_model}"
        )

        phase1_graph_for_prompt = json.dumps(
            phase1_graph,
            ensure_ascii=False,
            indent=2,
        )

        practical_innovation_guidance = build_practical_innovation_guidance(
            phase1_graph
        )

        with st.spinner(
            f"PHASE 2 — MA All Mental Approaches innovation architecture with {p2_provider_name}..."
        ):
            phase2_system = build_phase2_system_prompt(architecture_context)

            phase2_input = f"""
COMPLETED PHASE 1 — IMA KNOWLEDGE SYNTHESIS
============================================
{phase1_result}

============================================
PHASE 1 IMA SEMANTIC GRAPH
============================================
{phase1_graph_for_prompt}

============================================
PRACTICAL INNOVATION BRIEFING DERIVED FROM PHASE 1
============================================
{practical_innovation_guidance}

============================================
USER INNOVATION OBJECTIVE
============================================
{idea_query}

============================================
ORIGINAL INQUIRY
============================================
{user_query}

============================================
SOURCE MATERIAL
============================================
{file_context}

Now create the professional MA innovation report and its innovation-centric
semantic graph. Reuse and extend important Phase 1 concepts rather than
creating an unrelated graph.
"""

            phase2_result = gemini_generate(
                gemini_client,
                p2_model,
                phase2_system,
                phase2_input,
                temperature=0.85,
                top_p=0.92 if p2_is_hf else 0.90,
                huggingface_api_key=huggingface_api_key,
            )

        phase2_graph = extract_json_object(phase2_result) or {"nodes": [], "edges": []}
        phase2_graph = normalize_graph_data(phase2_graph)

        # Deterministic MA enrichment: the complete MA architecture is always
        # present, while the selected techniques remain supplementary.
        phase2_graph = enrich_graph_with_architecture(
            phase2_graph, selected_sciences
        )
        phase2_graph = enrich_graph_with_mental_approaches(
            phase2_graph, selected_techniques
        )
        phase2_graph = normalize_graph_data(phase2_graph)

        # ---------------------------------------------------------------------
        # INTEGRATED GRAPH — BOTH REPORTS
        # ---------------------------------------------------------------------
        integrated_graph = merge_phase_graphs(
            phase1_graph,
            phase2_graph,
        )

        integrated_graph = enrich_graph_with_architecture(
            integrated_graph,
            selected_sciences,
        )
        integrated_graph = enrich_graph_with_human_thinking_metamodel(
            integrated_graph,
        )
        integrated_graph = enrich_graph_with_mental_approaches(
            integrated_graph,
            selected_techniques,
        )
        integrated_graph = normalize_graph_data(integrated_graph)
        integrated_graph = connect_isolated_components(integrated_graph)
        integrated_graph = rank_integrated_graph(integrated_graph)
        integrated_graph = normalize_graph_data(integrated_graph)

        # Professional report extraction: remove graph payloads from prose.
        report_phase1 = phase1_result
        if "### IMA_SEMANTIC_GRAPH_JSON" in report_phase1:
            report_phase1 = report_phase1.split(
                "### IMA_SEMANTIC_GRAPH_JSON", 1
            )[0].strip()

        report_phase2 = phase2_result
        if "### MA_SEMANTIC_GRAPH_JSON" in report_phase2:
            report_phase2 = report_phase2.split(
                "### MA_SEMANTIC_GRAPH_JSON", 1
            )[0].strip()

        report_phase1 = re.sub(r"```(?:json)?", "", report_phase1, flags=re.I).strip()
        report_phase2 = re.sub(r"```(?:json)?", "", report_phase2, flags=re.I).strip()


        integrated_report = f"""
## 🧠 PHASE 1 — IMA KNOWLEDGE SYNTHESIS
### Complete Metamodel of Human Thinking

{report_phase1}

---

## 💡 PHASE 2 — MA INNOVATION ARCHITECTURE
### All Mental Approaches → Visionary but Realizable Solutions

{report_phase2}

"""

        # Interactive report links only use labels from the integrated graph.
        interactive_report = integrated_report
        labels = sorted(
            [n["label"] for n in integrated_graph["nodes"] if len(n["label"]) > 3],
            key=len,
            reverse=True,
        )

        replacements = 0
        for label in labels[:45]:
            if replacements >= 28:
                break

            query_url = urllib.parse.quote(label)
            safe_label = html.escape(label)
            link_html = (
                f'<a href="https://www.google.com/search?q={query_url}" '
                f'target="_blank" class="semantic-node-highlight">'
                f'{safe_label} ↗</a>'
            )

            pattern = re.compile(
                rf"(?<![\w>])" + re.escape(label) + r"(?![\w<])",
                re.IGNORECASE,
            )
            new_text, count = pattern.subn(
                link_html,
                interactive_report,
                count=1,
            )
            if count:
                interactive_report = new_text
                replacements += count

        st.session_state.phase1_graph_data = phase1_graph
        st.session_state.phase2_graph_data = phase2_graph
        st.session_state.last_graph_data = integrated_graph
        st.session_state.final_graph_elements = integrated_graph
        st.session_state.phase1_report = report_phase1
        st.session_state.phase2_report = report_phase2
        st.session_state.integrated_report = integrated_report
        st.session_state.interactive_report = interactive_report
        st.session_state.report_ready = True
        st.session_state.biblio_data = biblio_data

    except Exception as exc:
        st.error(f"❌ Pipeline Failure: {type(exc).__name__}: {exc}")
        st.exception(exc)


# =============================================================================
# MAIN REPORT + GRAPH DISPLAY
# =============================================================================

if st.session_state.get("report_ready") and st.session_state.get("last_graph_data"):

    graph_data = st.session_state.last_graph_data
    interactive_report = st.session_state.get("interactive_report", "")
    biblio_data = st.session_state.get("biblio_data", "")

    st.subheader(
        "🧠 IMA → MA PROFESSIONAL KNOWLEDGE & INNOVATION REPORT"
    )

    if biblio_data:

        with st.expander(
            "📚 EXTRACTED AUTHOR BACKGROUND",
            expanded=False,
        ):
            st.markdown(
                biblio_data
            )

    if interactive_report:
        st.markdown(
            interactive_report,
            unsafe_allow_html=True,
        )


    st.divider()


    st.divider()

    st.subheader(
        "🕸️ INTEGRATED IMA → MA PRIMARY HIERARCHOGRAPH"
    )

    # -------------------------------------------------------------------------
    # COMPONENT SELECTOR UNDER THE GRAPH
    # -------------------------------------------------------------------------

    st.markdown("#### 🎛️ Select components to display")

    selected_components = st.multiselect(
        "Choose which building blocks you want to see in the graph "
        "(leave all selected to show everything):",
        options=GRAPH_COMPONENT_OPTIONS,
        default=st.session_state.get(
            "selected_graph_components",
            GRAPH_COMPONENT_OPTIONS,
        ),
        key="graph_component_selector",
        help=(
            "You can show only innovations, only science fields, only paradigms, "
            "structural models, human thinking metamodel, mental approaches, "
            "processes, goals, constraints, entities, facts, states, data, "
            "or any combination. The root node is always kept for orientation."
        ),
    )

    st.session_state.selected_graph_components = selected_components

    # Apply component filter
    filtered_graph = filter_graph_by_components(
        graph_data,
        selected_components,
    )

    show_additional_relations = st.checkbox(
        "⚙️ Show additional operational relations",
        value=False,
        key="show_additional_graph_relations",
        help=(
            "By default the graph shows only the most intelligible relations: "
            "thesaurus, UML and IF-THEN / AND / OR / XOR / NOT. Enable this "
            "option to reveal additional causal, transformational, feedback "
            "and other operational relations."
        ),
    )

    st.caption(
        "The hierarchograph is used as an operational design substrate for the "
        "innovation phase. To keep it understandable, the default view emphasises "
        "thesaurus hierarchy/association, UML structure and explicit logical "
        "relations. Additional operational relations remain available on demand. "
        f"Displayed nodes: up to {graph_node_limit}. "
        f"Currently showing {len(filtered_graph['nodes'])} nodes after component filter. "
        "Use the ➕/➖ ZOOM buttons or the mouse wheel to zoom in and out."
    )

    render_cytoscape_network(
        filtered_graph,
        layout_type=graph_perspective,
        container_id="primary_graph",
        max_nodes=graph_node_limit,
        show_additional_relations=show_additional_relations,
    )


# =============================================================================
# MULTI-PERSPECTIVE GALLERY
# =============================================================================

if (
    st.session_state.get("report_ready")
    and st.session_state.get("final_graph_elements")
):

    st.divider()

    st.markdown(
        '<h2 style="color:#1d3557;text-align:center;">'
        "🖼️ MULTI-PERSPECTIVE HIERARCHOGRAPH GALLERY"
        "</h2>",
        unsafe_allow_html=True,
    )

    st.info(
        "The same knowledge architecture is displayed through different "
        "visual grammars. The data model remains identical. Every view "
        "supports mouse-wheel zoom and the ➕/➖ ZOOM buttons. "
        "Relation types are always shown on edges. "
        "The component filter selected above also applies to the gallery."
    )

    # Re-use the same filter for the gallery
    gallery_base = filter_graph_by_components(
        st.session_state.final_graph_elements,
        st.session_state.get("selected_graph_components", GRAPH_COMPONENT_OPTIONS),
    )

    gallery_tabs = st.tabs(
        [
            "🌲 HIERARCHICAL",
            "⚙️ OPERATIONAL",
            "🌐 ORGANIC",
            "🎯 CONCENTRIC",
            "⭕ CIRCULAR",
            "🔲 GRID",
        ]
    )

    gallery_views = [
        ("hierarchical", "Vertical taxonomic and structural hierarchy."),
        ("operational", "Processes, transformations and system states."),
        ("organic", "Emergent associative clusters."),
        ("concentric", "Macro-Meso-Micro systemic layers."),
        ("circular", "Lateral relation density and interdependence."),
        ("grid", "Structured inspection of the same ontology."),
    ]

    for tab, (view, description) in zip(
        gallery_tabs,
        gallery_views,
    ):

        with tab:

            st.markdown(
                f"**{view.upper()} VIEW:** {description}"
            )

            render_cytoscape_network(
                gallery_base,
                layout_type=view,
                container_id=f"gallery_{view}",
                max_nodes=graph_node_limit,
                show_additional_relations=st.session_state.get(
                    "show_additional_graph_relations", False
                ),
            )


# =============================================================================
# RAW ARCHITECTURE INSPECTION
# =============================================================================

if st.session_state.get("report_ready"):

    with st.expander(
        "🔎 RAW HIERARCHOGRAPH DATA",
        expanded=False,
    ):

        st.json(
            st.session_state.last_graph_data
        )


# =============================================================================
# FOOTER
# =============================================================================

st.divider()

st.caption(
    f"SIS Universal Knowledge Synthesizer | "
    f"{VERSION_CODE} | "
    f"{SYSTEM_DATE} | "
    "Multidimensional Thesaurus · Polyhierarchical Ontology · "
    "UML · Hierarchical-Associative Logic · Operational Logic · "
    "Hierarchography"
)
