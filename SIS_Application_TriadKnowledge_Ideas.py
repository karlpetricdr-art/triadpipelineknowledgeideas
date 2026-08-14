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
VERSION_CODE = "v23.1.0-KNOWLEDGE-SYNTHESIS-INNOVATION"

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
[data-testid="stSidebar"] button {
    color:#ffffff !important;
    background:#263241 !important;
    border:1px solid #718096 !important;
    font-weight:800 !important;
}
[data-testid="stSidebar"] button:hover {
    color:#ffffff !important;
    background:#3a4a5f !important;
    border-color:#a8b4c2 !important;
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
    # Thesaurus
    "TT": "Top Term — root concept of a domain.",
    "BT": "Broader Term — hierarchical superordinate concept.",
    "NT": "Narrower Term — hierarchical subordinate concept.",
    "RT": "Related Term — lateral semantic association.",
    "EQ": "Equivalence — synonymous or conceptually equivalent term.",
    "AS": "Associative — functional or contextual association.",
    "IN": "Instance — category-to-instance relation.",

    # UML
    "Generalization": "Generalization / inheritance.",
    "Specialization": "Specialization / deductive narrowing.",
    "Composition": "Strong whole-part relation.",
    "Aggregation": "Weak whole-part relation.",
    "Containment": "Structural containment.",
    "Realization": "Implementation of an abstract specification.",
    "Dependency": "Operational dependency.",
    "Conflict": "Systemic incompatibility or tension.",

    # Logic
    "AND": "Conjunctive synthesis.",
    "OR": "Alternative path.",
    "XOR": "Exclusive alternative.",
    "NOT": "Negation or prohibition.",
    "IF-THEN": "Conditional transformation.",

    # Operational
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
        "max_tokens": 2048,
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

    # Remove control characters while retaining Unicode text.
    raw = "".join(
        ch for ch in raw
        if ord(ch) >= 32 or ch in "\n\r\t"
    )

    # Convert Python-like booleans/null if model accidentally used them.
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
            "label": str(
                edge.get("label")
                or RELATION_DEFINITIONS[relation]
            )[:180],
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
# DETERMINISTIC ONTOLOGICAL ENRICHMENT
# =============================================================================

def enrich_graph_with_architecture(graph, selected_sciences):
    """
    The AI graph remains primary.
    This function adds structural metadata and missing hierarchical,
    UML and operational relationships without importing Stress-Barometer logic.
    """

    graph = normalize_graph_data(graph)

    nodes = graph["nodes"]
    edges = graph["edges"]

    if not nodes:
        return graph

    node_map = {n["id"]: n for n in nodes}

    # -------------------------------------------------------------------------
    # Normalize semantic node metadata.
    # -------------------------------------------------------------------------

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

    # -------------------------------------------------------------------------
    # Add selected science domains when absent.
    # -------------------------------------------------------------------------

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

    # -------------------------------------------------------------------------
    # Create a deterministic hierarchy backbone if the AI did not provide it.
    # -------------------------------------------------------------------------

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

        edges.append({
            "id": f"auto_{len(edges) + 1}",
            "source": source,
            "target": target,
            "rel_type": relation,
            "label": RELATION_DEFINITIONS[relation],
            "weight": weight,
            "direction": "directed",
        })

        existing_pairs.add(key)

    # -------------------------------------------------------------------------
    # Connect domains to root using BT/NT semantics.
    # -------------------------------------------------------------------------

    for node in nodes:
        if node["id"] == root_id:
            continue

        if node["layer"] == "domain":
            add_edge(
                root_id,
                node["id"],
                "NT",
                2.0,
            )

    # -------------------------------------------------------------------------
    # Establish polyhierarchical connections.
    # A concept can participate in several hierarchy dimensions.
    # -------------------------------------------------------------------------

    macro_nodes = [
        n for n in nodes
        if n["level"] == "Macro" and n["id"] != root_id
    ]

    meso_nodes = [
        n for n in nodes
        if n["level"] == "Meso"
    ]

    micro_nodes = [
        n for n in nodes
        if n["level"] == "Micro"
    ]

    for macro in macro_nodes[:12]:
        for meso in meso_nodes[:20]:
            if macro["id"] == meso["id"]:
                continue

            if semantic_related(macro, meso):
                add_edge(
                    macro["id"],
                    meso["id"],
                    "BT",
                    1.0,
                )

    for meso in meso_nodes[:25]:
        for micro in micro_nodes[:25]:
            if meso["id"] == micro["id"]:
                continue

            if semantic_related(meso, micro):
                add_edge(
                    meso["id"],
                    micro["id"],
                    "NT",
                    0.8,
                )

    # -------------------------------------------------------------------------
    # Add lateral associative relations.
    # -------------------------------------------------------------------------

    all_nodes = nodes[:80]

    for i, source in enumerate(all_nodes):
        for target in all_nodes[i + 1:]:
            if source["id"] == target["id"]:
                continue

            if not semantic_related(source, target):
                continue

            existing = any(
                e["source"] == source["id"]
                and e["target"] == target["id"]
                for e in edges
            )

            reverse_existing = any(
                e["source"] == target["id"]
                and e["target"] == source["id"]
                for e in edges
            )

            if not existing and not reverse_existing:
                add_edge(
                    source["id"],
                    target["id"],
                    "RT",
                    0.35,
                )

    # -------------------------------------------------------------------------
    # Detect process -> output operational paths.
    # -------------------------------------------------------------------------

    process_nodes = [
        n for n in nodes
        if n["shape"] == "triangle"
        or n["layer"] == "process"
    ]

    innovation_nodes = [
        n for n in nodes
        if n["shape"] == "diamond"
        or n["layer"] == "innovation"
    ]

    state_nodes = [
        n for n in nodes
        if n["shape"] == "round-rectangle"
        or n["layer"] == "state"
    ]

    for process in process_nodes[:20]:
        for innovation in innovation_nodes[:20]:
            if semantic_related(process, innovation):
                add_edge(
                    process["id"],
                    innovation["id"],
                    "TRANSFORMS",
                    1.2,
                )

    for innovation in innovation_nodes[:20]:
        for state in state_nodes[:20]:
            add_edge(
                innovation["id"],
                state["id"],
                "TRANSFORMS",
                1.0,
            )

    # -------------------------------------------------------------------------
    # Feedback loop representation.
    # Explicitly creates a feedback edge only when states/operations support it.
    # -------------------------------------------------------------------------

    if len(state_nodes) >= 2:
        first_state = state_nodes[0]
        second_state = state_nodes[1]

        add_edge(
            second_state["id"],
            first_state["id"],
            "FEEDBACK",
            0.7,
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


def semantic_related(a, b):
    a_words = set(
        re.findall(
            r"[a-zA-ZÀ-ž0-9]{4,}",
            a["label"].lower(),
        )
    )

    b_words = set(
        re.findall(
            r"[a-zA-ZÀ-ž0-9]{4,}",
            b["label"].lower(),
        )
    )

    if a_words & b_words:
        return True

    if a.get("layer") == b.get("layer"):
        return True

    if a.get("level") != b.get("level"):
        return True

    return False


# =============================================================================
# GRAPH STATISTICS
# =============================================================================

def graph_statistics(graph):
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    levels = {}
    layers = {}
    relations = {}

    for node in nodes:
        levels[node["level"]] = levels.get(node["level"], 0) + 1
        layers[node["layer"]] = layers.get(node["layer"], 0) + 1

    for edge in edges:
        rel = edge["rel_type"]
        relations[rel] = relations.get(rel, 0) + 1

    return {
        "nodes": len(nodes),
        "edges": len(edges),
        "levels": levels,
        "layers": layers,
        "relations": relations,
    }


# =============================================================================
# GRAPH DISPLAY LIMITER
# =============================================================================

def limit_graph_nodes(graph, max_nodes=80):
    """
    Return a display-only graph containing at most max_nodes.
    The underlying AI-generated graph is never modified.
    Selection prioritizes the knowledge root, high-degree nodes, Macro/Meso
    nodes and innovation/process nodes, then fills remaining slots by degree.
    """
    graph = normalize_graph_data(graph)
    nodes = graph["nodes"]
    edges = graph["edges"]

    if max_nodes is None or max_nodes >= len(nodes):
        return graph

    max_nodes = max(1, int(max_nodes))

    degree = {n["id"]: 0 for n in nodes}
    for edge in edges:
        if edge["source"] in degree:
            degree[edge["source"]] += 1
        if edge["target"] in degree:
            degree[edge["target"]] += 1

    def priority(node):
        label = node.get("label", "").lower()
        root_bonus = 100000 if node.get("id") == "knowledge_root" else 0
        semantic_bonus = 5000 if node.get("semantic_type") == "root" else 0
        level_bonus = {
            "Macro": 3000,
            "Meso": 2000,
            "Micro": 1000,
        }.get(node.get("level"), 0)
        shape_bonus = {
            "star": 1500,
            "diamond": 1200,
            "hexagon": 900,
            "triangle": 700,
        }.get(node.get("shape"), 0)
        return (
            root_bonus
            + semantic_bonus
            + level_bonus
            + shape_bonus
            + degree.get(node["id"], 0) * 25
            + min(len(label), 80)
        )

    selected = sorted(nodes, key=priority, reverse=True)[:max_nodes]
    selected_ids = {n["id"] for n in selected}

    selected_edges = [
        edge for edge in edges
        if edge["source"] in selected_ids and edge["target"] in selected_ids
    ]

    return {
        "nodes": selected,
        "edges": selected_edges,
    }


# =============================================================================
# CYTOSCAPE HIERARCHOGRAPHIC RENDERER
# =============================================================================

def render_cytoscape_network(
    graph,
    layout_type="hierarchographic",
    container_id="cy_canvas",
    max_nodes=None,
):
    graph = limit_graph_nodes(graph, max_nodes=max_nodes)

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

        "hierarchographic": """
        {
            name:'breadthfirst',
            directed:true,
            circle:false,
            padding:90,
            spacingFactor:1.35,
            maximal:false,
            roots:'#knowledge_root'
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
        layout_configs["hierarchographic"],
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
<b>Feedback:</b> cyclic system regulation
</div>

<div id="toolbar">
<button class="tool" id="fit">FIT</button>
<button class="tool" id="hier">HIERARCHY</button>
<button class="tool" id="save">EXPORT PNG</button>
</div>

<div id="cy"></div>
</div>

<script>
const elements = {safe_elements};

const cy = cytoscape({{
    container: document.getElementById('cy'),
    elements: elements,

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
                'font-size':'8px',
                'font-weight':'bold',
                'color':'#343a40',
                'text-background-color':'#ffffff',
                'text-background-opacity':.92,
                'text-background-padding':'3px',
                'opacity':.8
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
# AI PROMPTS
# =============================================================================

def build_phase1_system_prompt():
    return """
You are the SIS Lead Knowledge Synthesizer, Hierarchologist and Ontology Engineer.

PHASE 1 HAS ONE PURPOSE: KNOWLEDGE SYNTHESIS.

Do not treat Phase 1 as an Innovation Objective and do not solve the innovation
objective yet. Synthesize the user's inquiry into a rich, structured knowledge
system that can later serve as the knowledge substrate for Phase 2 innovation.

The synthesis MUST simultaneously contain:
1. A rich multidimensional thesaurus.
2. A polyhierarchical ontology.
3. A UML/metamodel representation.
4. Hierarchical-associative relations.
5. Operational relations.
6. State and transformation logic.
7. Temporal/process logic.
8. Feedback loops where logically justified.
9. Macro, Meso and Micro levels.
10. A hierarchographic representation.
11. Relevant scientific domains, paradigms, structural models and evidence.
12. Explicit concepts, definitions, mechanisms, causes, effects, functions,
    contexts, constraints and dependencies.

The central question of Phase 1 is:
WHAT KNOWLEDGE MUST BE SYNTHESIZED, STRUCTURED, RELATED AND ORGANIZED
TO FULLY UNDERSTAND THE USER'S INQUIRY?

Do not optimize for novelty yet. Do not generate the final innovation solution.
Build the richest defensible knowledge substrate for Phase 2.

Do NOT use Stress Barometer concepts, stress degrees, kcal, sigma, positive
factors, negative factors, psychosocial stress scores or similar logic.

Vertical relations:
TT, BT, NT, IN, Generalization, Specialization, Composition, Aggregation,
Containment.

Lateral relations:
RT, EQ, AS, Dependency, Conflict.

Operational relations:
CAUSES, ENABLES, TRANSFORMS, PRODUCES, CONSUMES, FEEDS, TRIGGERS,
PRECEDES, CONSTRAINS, MEASURES, VALIDATES.

Logical relations:
AND, OR, XOR, NOT, IF-THEN.

Feedback:
FEEDBACK, POSITIVE-FEEDBACK, NEGATIVE-FEEDBACK.

Use Micro/Meso/Macro explicitly. Think like an ontology engineer, systems
architect, UML modeler, knowledge organization specialist and hierarchographist
simultaneously.

The result must be a knowledge synthesis, not a simple concept list and not
an innovation proposal.
"""

def build_phase2_system_prompt(architecture_context):
    return f"""
You are the SIS Lead Innovation Architect and Hierarchographist.

PHASE 2 HAS ONE PURPOSE: INNOVATION OBJECTIVE.

It is NOT a second general knowledge synthesis phase and it is NOT a Stress
Barometer.

Use the completed Phase 1 knowledge synthesis as the knowledge substrate, but
focus exclusively on the user's stated INNOVATION OBJECTIVE. Determine what
should be transformed, invented, recombined, improved, operationalized or
implemented.

The innovation output MUST remain grounded in the Phase 1 knowledge synthesis
and must use the system's multidimensional thesaurus, polyhierarchy, UML,
hierarchical-associative logic, operational logic, state transitions and
hierarchography.

Do not reopen the general inquiry as a new research question. Do not produce
generic background knowledge. Do not merely repeat Phase 1. Produce an
innovation-oriented transformation of the Phase 1 knowledge in response to the
explicit Innovation Objective.

The graph must represent:

THESAURUS
ONTOLOGY
POLYHIERARCHY
UML
HIERARCHICAL-ASSOCIATIVE LOGIC
OPERATIONAL LOGIC
TRANSFORMATIONS
SYSTEM STATES
FEEDBACK
HIERARCHOGRAPHY

============================================================
MANDATORY ARCHITECTURAL PRINCIPLE
============================================================

Do not produce a simple mind map.

Build a semantic architecture in which the same concept may participate in
several legitimate hierarchies.

A concept may therefore have:
- one parent in a taxonomic hierarchy,
- another parent in a process hierarchy,
- another relationship in a part-whole hierarchy,
- and lateral RT/AS/EQ relations.

This is POLYHIERARCHY.

============================================================
THESAURUS
============================================================

Use:
TT = Top Term
BT = Broader Term
NT = Narrower Term
RT = Related Term
EQ = Equivalence
AS = Associative
IN = Instance

============================================================
UML
============================================================

Use:
Generalization
Specialization
Composition
Aggregation
Containment
Realization
Dependency
Conflict

============================================================
OPERATIONAL LOGIC
============================================================

Use:
CAUSES
ENABLES
TRANSFORMS
PRODUCES
CONSUMES
FEEDS
TRIGGERS
PRECEDES
CONSTRAINS
MEASURES
VALIDATES

============================================================
LOGICAL CONNECTORS
============================================================

Use:
AND
OR
XOR
NOT
IF-THEN

============================================================
FEEDBACK
============================================================

Where the domain justifies it, use:
FEEDBACK
POSITIVE-FEEDBACK
NEGATIVE-FEEDBACK

Feedback must form genuine directed cycles.

============================================================
GEOMETRIC LANGUAGE
============================================================

star:
Goal, mission, vision, macro objective.

hexagon:
Scientific field, discipline or domain.

diamond:
Innovation, synthesis, transformation or new conceptual construction.

triangle:
Process, method, operation, mechanism.

octagon:
Rule, constraint, ethical boundary, limitation.

ellipse:
Human factor, agent, identity or biological entity.

rectangle:
Fact, concept, evidence, data or micro-component.

round-rectangle:
System state or transition state.

barrel:
Evidence/data repository.

============================================================
HIERARCHICAL LEVELS
============================================================

Every node MUST have:

"level": "Macro" | "Meso" | "Micro"

Macro:
principles, domains, missions, goals, global structures.

Meso:
systems, disciplines, processes, innovations, subsystems.

Micro:
facts, instances, observations, concrete mechanisms and states.

============================================================
NODE METADATA
============================================================

Every node must contain:

id
label
shape
color
description
layer
level
semantic_type
state

============================================================
EDGE METADATA
============================================================

Every edge must contain:

id
source
target
rel_type
label
weight
direction

============================================================
INNOVATION REQUIREMENT
============================================================

Every diamond innovation node must explicitly identify three Mental Approaches
used in its synthesis.

Do not randomly attach three approaches.
Explain why the three approaches produce the transformation.

============================================================
SYSTEM STATES
============================================================

Where appropriate create state nodes representing:

initial state
problem state
transition state
target state
validated state

Connect them using operational relations.

============================================================
REPORT
============================================================

Produce:

### STRATEGIC KNOWLEDGE SYNTHESIS

Explain:
- core ontology
- polyhierarchy
- major semantic associations
- UML architecture
- operational transformations
- system states
- feedback
- innovations
- interdisciplinary implications

Then produce:

### SEMANTIC_GRAPH_JSON

The JSON must be the FINAL content of the response.

Do not write anything after the JSON.

============================================================
JSON
============================================================

Return valid JSON.

Do not put markdown inside the JSON.

Descriptions must be single-line strings.

No comments.

No trailing commas.

============================================================
KNOWLEDGE ARCHITECTURE REFERENCE
============================================================

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
        "Phase 1 Model — Knowledge Synthesis",
        GEMINI_MODEL_LABELS,
        index=1,
        key="p1_model_v230",
    )

    p1_model = GEMINI_MODEL_CATALOG[p1_label]

    p2_label = st.selectbox(
        "Phase 2 Model — Innovation Objective",
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
            "hierarchographic",
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
        help="Limits the number of displayed nodes while preserving the most structurally important nodes and their valid relations.",
    )

    st.caption(
        "Hierarchographic = polyhierarchy + semantic association + "
        "operational transformations + system states. "
        "Use the slider to control graph density."
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
structure: thesaurus, ontology, polyhierarchy, UML, hierarchical-associative
relations, operational logic, states, processes and evidence.

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

**8. Hierarchography**
The complete architecture is rendered as a multidimensional graph.
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
    "Select Mental / Ideation Frameworks",
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
        "🧠 PHASE 1 — KNOWLEDGE SYNTHESIS",
        placeholder=(
             "Enter the scientific, conceptual or systemic inquiry from which the "
            "system should synthesize a rich body of structured knowledge."
        ),
        height=230,
        key="user_query_v230",
    )


with col_inq2:

    idea_query = st.text_area(
        "💡 PHASE 2 — INNOVATION OBJECTIVE",
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
# EXECUTION
# =============================================================================

if st.button(
    "🚀 EXECUTE MULTI-DIMENSIONAL KNOWLEDGE SYNTHESIS",
    use_container_width=True,
    key="execute_v230",
):

    p1_is_hf = p1_model.startswith("hf:")
    p2_is_hf = p2_model.startswith("hf:")

    google_required = (
        not p1_is_hf
        or not p2_is_hf
    )

    hf_required = (
        p1_is_hf
        or p2_is_hf
    )

    if google_required and not google_api_key:

        st.error(
            "❌ Google AI API key is required for the selected Google model."
        )

        st.stop()

    if hf_required and not huggingface_api_key:

        st.error(
            "❌ Hugging Face API key is required for Qwen2.5-72B-Instruct."
        )

        st.stop()

    if not user_query.strip():

        st.warning(
            "⚠️ Phase 1 — Knowledge Synthesis inquiry is required."
        )

        st.stop()

    if not idea_query.strip():

        st.warning(
            "⚠️ Phase 2 — Innovation Objective is required."
        )

        st.stop()

    if not selected_sciences:

        st.warning(
            "⚠️ Select at least one science field."
        )

        st.stop()

    if not selected_techniques:

        st.warning(
            "⚠️ Select at least one transformation framework."
        )

        st.stop()

    try:

        # ---------------------------------------------------------------------
        # BUILD ARCHITECTURE CONTEXT
        # ---------------------------------------------------------------------

        architecture_context = build_knowledge_architecture_context(
            selected_sciences,
            selected_paradigms,
            selected_models,
            selected_techniques,
        )

        file_context = (
            "\n\nSOURCE FILE CONTEXT:\n"
            + file_content
            if file_content
            else ""
        )

        biblio_data = ""

        if target_authors:

            with st.spinner(
                "📚 Accessing ORCID bibliographic metadata..."
            ):
                biblio_data = fetch_author_bibliographies(
                    target_authors
                )

        biblio_context = (
            "\n\nAUTHOR RESEARCH BACKGROUND:\n"
            + biblio_data
            if biblio_data
            else ""
        )

        full_input = f"""
USER INQUIRY:
{user_query}

INNOVATION / TRANSFORMATION OBJECTIVE:
{idea_query}

EXPERTISE:
{expertise}

STRATEGIC GOAL:
{goal_context}

SELECTED SCIENCE FIELDS:
{", ".join(selected_sciences)}

SELECTED PARADIGMS:
{", ".join(selected_paradigms)}

SELECTED STRUCTURAL MODELS:
{", ".join(selected_models)}

SELECTED TRANSFORMATION FRAMEWORKS:
{", ".join(selected_techniques)}

{file_context}

{biblio_context}

ARCHITECTURAL REQUIREMENT:
Construct a rich knowledge system, not a stress model.
"""


        # ---------------------------------------------------------------------
        # GEMINI CLIENT
        # ---------------------------------------------------------------------

        gemini_client = None

        if google_required:
            gemini_client = genai.Client(
                api_key=google_api_key
            )


        # =====================================================================
        # PHASE 1 — KNOWLEDGE SYNTHESIS
        # =====================================================================

        p1_provider_name = (
            "Hugging Face / Qwen2.5-72B-Instruct"
            if p1_is_hf
            else f"Google / {p1_model}"
        )

        with st.spinner(
            f"PHASE 1 — Synthesizing knowledge with {p1_provider_name}..."
        ):

            phase1_system = build_phase1_system_prompt()

            phase1_input = (
                architecture_context
                + "\n\n"
                + full_input
            )

            phase1_result = gemini_generate(
                gemini_client,
                p1_model,
                phase1_system,
                phase1_input,
                temperature=0.35,
                top_p=0.85,
                huggingface_api_key=huggingface_api_key,
            )

            st.session_state.groq_synthesis = phase1_result


        # =====================================================================
        # PHASE 2 — INNOVATION OBJECTIVE
        # =====================================================================

        p2_provider_name = (
            "Hugging Face / Qwen2.5-72B-Instruct"
            if p2_is_hf
            else f"Google / {p2_model}"
        )

        with st.spinner(
            f"PHASE 2 — Executing Innovation Objective with {p2_provider_name}..."
        ):

            phase2_system = build_phase2_system_prompt(
                architecture_context
            )

            phase2_input = f"""
PHASE 1 KNOWLEDGE ARCHITECTURE
================================

{phase1_result}

================================
USER TRANSFORMATION OBJECTIVE
================================

{idea_query}

================================
ORIGINAL INQUIRY
================================

{user_query}

================================
ADDITIONAL SOURCE
================================

{file_context}
"""

            phase2_result = gemini_generate(
                gemini_client,
                p2_model,
                phase2_system,
                phase2_input,
                temperature=0.75,
                top_p=0.9,
                huggingface_api_key=huggingface_api_key,
            )

            st.session_state.gemini_innovation = phase2_result


        # =====================================================================
        # PARSE PHASE 2
        # =====================================================================

        graph_data = extract_json_object(
            phase2_result
        )

        if graph_data is None:

            st.warning(
                "⚠️ The model did not return valid graph JSON. "
                "A structural fallback graph will be created."
            )

            graph_data = {
                "nodes": [],
                "edges": [],
            }


        graph_data = enrich_graph_with_architecture(
            graph_data,
            selected_sciences,
        )

        graph_data = normalize_graph_data(
            graph_data
        )

        st.session_state.last_graph_data = graph_data
        st.session_state.final_graph_elements = graph_data
        st.session_state.report_ready = True


        # =====================================================================
        # REPORT
        # =====================================================================

        report_phase2 = phase2_result

        if "### SEMANTIC_GRAPH_JSON" in report_phase2:

            report_phase2 = report_phase2.split(
                "### SEMANTIC_GRAPH_JSON",
                1,
            )[0]

        report_phase2 = re.sub(
            r"```(?:json)?",
            "",
            report_phase2,
            flags=re.IGNORECASE,
        )

        full_report = f"""
## 🧠 PHASE 1 — KNOWLEDGE SYNTHESIS

{phase1_result}

---

## 💡 PHASE 2 — INNOVATION OBJECTIVE

{report_phase2}
"""


        # =====================================================================
        # REPORT NODE LINKING
        # =====================================================================

        interactive_report = full_report

        labels = sorted(
            [
                node["label"]
                for node in graph_data["nodes"]
                if len(node["label"]) > 3
            ],
            key=len,
            reverse=True,
        )

        replacements = 0

        for label in labels[:40]:

            if replacements >= 25:
                break

            query_url = urllib.parse.quote(
                label
            )

            safe_label = html.escape(
                label
            )

            link_html = (
                f'<a href="https://www.google.com/search?q={query_url}" '
                f'target="_blank" '
                f'class="semantic-node-highlight">'
                f'{safe_label} ↗'
                f"</a>"
            )

            pattern = re.compile(
                rf"(?<![\w>])"
                + re.escape(label)
                + r"(?![\w<])",
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


        # =====================================================================
        # MAIN REPORT DISPLAY
        # =====================================================================

        st.subheader(
            "🧱 INTEGRATED HIERARCHOLOGICAL KNOWLEDGE REPORT"
        )

        if biblio_data:

            with st.expander(
                "📚 EXTRACTED AUTHOR BACKGROUND",
                expanded=False,
            ):
                st.markdown(
                    biblio_data
                )

        st.markdown(
            interactive_report,
            unsafe_allow_html=True,
        )


        # =====================================================================
        # GRAPH STATISTICS
        # =====================================================================

        stats = graph_statistics(
            graph_data
        )

        st.divider()

        st.subheader(
            "📊 KNOWLEDGE ARCHITECTURE STATISTICS"
        )

        s1, s2, s3, s4 = st.columns(4)

        with s1:
            st.metric(
                "Nodes",
                stats["nodes"],
            )

        with s2:
            st.metric(
                "Relations",
                stats["edges"],
            )

        with s3:
            st.metric(
                "Macro / Meso / Micro",
                (
                    f"{stats['levels'].get('Macro', 0)} / "
                    f"{stats['levels'].get('Meso', 0)} / "
                    f"{stats['levels'].get('Micro', 0)}"
                ),
            )

        with s4:
            st.metric(
                "Relation Types",
                len(stats["relations"]),
            )


        # =====================================================================
        # POLYHIERARCHY / UML / OPERATIONAL TABLES
        # =====================================================================

        tabs = st.tabs(
            [
                "🌳 Polyhierarchy",
                "📐 UML",
                "⚙️ Operational Logic",
                "🔄 Feedback / States",
                "💠 Innovations",
            ]
        )

        with tabs[0]:

            st.markdown(
                "### Polyhierarchical Structure"
            )

            for hierarchy in POLYHIERARCHY["hierarchies"]:

                st.markdown(
                    f"""
**{hierarchy['id']} — {hierarchy['name']}**

Root: `{hierarchy['root']}`

Relations: {", ".join(hierarchy['relations'])}
"""
                )

            st.markdown(
                "### Detected hierarchical relations"
            )

            hierarchical_edges = [
                e
                for e in graph_data["edges"]
                if e["rel_type"]
                in {
                    "TT",
                    "BT",
                    "NT",
                    "IN",
                    "Generalization",
                    "Specialization",
                    "Composition",
                    "Aggregation",
                    "Containment",
                }
            ]

            for edge in hierarchical_edges[:100]:

                source = next(
                    (
                        n["label"]
                        for n in graph_data["nodes"]
                        if n["id"] == edge["source"]
                    ),
                    edge["source"],
                )

                target = next(
                    (
                        n["label"]
                        for n in graph_data["nodes"]
                        if n["id"] == edge["target"]
                    ),
                    edge["target"],
                )

                st.markdown(
                    f"**{source}** → "
                    f"`{edge['rel_type']}` → "
                    f"**{target}**"
                )


        with tabs[1]:

            st.markdown(
                "### UML / Metamodel Relations"
            )

            uml_edges = [
                e
                for e in graph_data["edges"]
                if e["rel_type"]
                in {
                    "Generalization",
                    "Specialization",
                    "Composition",
                    "Aggregation",
                    "Containment",
                    "Realization",
                    "Dependency",
                    "Conflict",
                }
            ]

            if uml_edges:

                for edge in uml_edges[:100]:

                    source = next(
                        (
                            n["label"]
                            for n in graph_data["nodes"]
                            if n["id"] == edge["source"]
                        ),
                        edge["source"],
                    )

                    target = next(
                        (
                            n["label"]
                            for n in graph_data["nodes"]
                            if n["id"] == edge["target"]
                        ),
                        edge["target"],
                    )

                    st.markdown(
                        f"**{source}** "
                        f"`{edge['rel_type']}` "
                        f"**{target}**"
                    )

            else:
                st.info(
                    "No explicit UML relation was generated."
                )


        with tabs[2]:

            st.markdown(
                "### Operational Transformations"
            )

            operational_edges = [
                e
                for e in graph_data["edges"]
                if e["rel_type"]
                in {
                    "CAUSES",
                    "ENABLES",
                    "TRANSFORMS",
                    "PRODUCES",
                    "CONSUMES",
                    "FEEDS",
                    "TRIGGERS",
                    "PRECEDES",
                    "CONSTRAINS",
                    "MEASURES",
                    "VALIDATES",
                    "IF-THEN",
                    "AND",
                    "OR",
                    "XOR",
                    "NOT",
                }
            ]

            if operational_edges:

                for edge in operational_edges[:120]:

                    source = next(
                        (
                            n["label"]
                            for n in graph_data["nodes"]
                            if n["id"] == edge["source"]
                        ),
                        edge["source"],
                    )

                    target = next(
                        (
                            n["label"]
                            for n in graph_data["nodes"]
                            if n["id"] == edge["target"]
                        ),
                        edge["target"],
                    )

                    st.markdown(
                        f"**{source}** "
                        f"`{edge['rel_type']}` "
                        f"**{target}**"
                    )

            else:
                st.info(
                    "No explicit operational relations were generated."
                )


        with tabs[3]:

            st.markdown(
                "### System States and Feedback"

            )

            states = [
                n
                for n in graph_data["nodes"]
                if n["layer"] == "state"
                or n["shape"] == "round-rectangle"
            ]

            feedback = [
                e
                for e in graph_data["edges"]
                if e["rel_type"]
                in {
                    "FEEDBACK",
                    "POSITIVE-FEEDBACK",
                    "NEGATIVE-FEEDBACK",
                }
            ]

            if states:

                for state in states:

                    st.markdown(
                        f"""
**{state['label']}**

Level: `{state['level']}`

State: `{state['state'] or 'unspecified'}`

{state['description']}
"""
                    )

            else:
                st.info(
                    "No explicit system-state nodes were generated."
                )

            if feedback:

                st.markdown(
                    "### Feedback loops"
                )

                for edge in feedback:

                    source = next(
                        (
                            n["label"]
                            for n in graph_data["nodes"]
                            if n["id"] == edge["source"]
                        ),
                        edge["source"],
                    )

                    target = next(
                        (
                            n["label"]
                            for n in graph_data["nodes"]
                            if n["id"] == edge["target"]
                        ),
                        edge["target"],
                    )

                    st.markdown(
                        f"**{source}** "
                        f"`{edge['rel_type']}` "
                        f"**{target}**"
                    )

            else:

                st.info(
                    "No explicit feedback loop was generated."
                )


        with tabs[4]:

            st.markdown(
                "### Strategic Knowledge Transformations"
            )

            innovations = [
                n
                for n in graph_data["nodes"]
                if n["shape"] == "diamond"
            ]

            if innovations:

                for innovation in innovations:

                    query_url = urllib.parse.quote(
                        innovation["label"]
                    )

                    st.markdown(
                        f"""
<div style="
background:#ffffff;
border-left:7px solid #f4a261;
padding:24px;
border-radius:15px;
border:1px solid #eeeeee;
margin-bottom:20px;
box-shadow:0 5px 15px rgba(0,0,0,.06);
">

<div style="
font-size:.75em;
font-weight:800;
color:#d97706;
text-transform:uppercase;
letter-spacing:1px;
">
HIERARCHOGRAPHIC INNOVATION
</div>

<h2 style="
color:#1d3557;
margin-bottom:12px;
">
{html.escape(innovation['label'])}
</h2>

<p>
{html.escape(innovation['description'])}
</p>

<p>
<b>Level:</b> {html.escape(innovation['level'])}
&nbsp;&nbsp;
<b>Layer:</b> {html.escape(innovation['layer'])}
</p>

<a href="https://www.google.com/search?q={query_url}"
target="_blank">
Technical semantic search ↗
</a>

</div>
""",
                        unsafe_allow_html=True,
                    )

            else:

                st.info(
                    "No diamond innovation nodes were generated."
                )


        # =====================================================================
        # LEGEND
        # =====================================================================

        st.markdown(
            """
<div class="graph-legend">

<b style="color:#1d3557;">
HIERARCHOGRAPHIC VISUAL LANGUAGE
</b>

<br><br>

<b>Geometry</b><br>
⭐ Goal / Vision &nbsp;|
⬢ Domain &nbsp;|
💠 Innovation &nbsp;|
△ Process &nbsp;|
⬣ Rule &nbsp;|
⬭ Entity &nbsp;|
▭ Fact / Concept &nbsp;|
▢ State

<br><br>

<b>Hierarchy</b><br>
TT = Top Term |
BT = Broader Term |
NT = Narrower Term |
IN = Instance

<br><br>

<b>Association</b><br>
RT = Related |
EQ = Equivalence |
AS = Associative

<br><br>

<b>UML</b><br>
Generalization |
Specialization |
Composition |
Aggregation |
Containment |
Realization |
Dependency |
Conflict

<br><br>

<b>Operation</b><br>
CAUSES |
ENABLES |
TRANSFORMS |
PRODUCES |
CONSUMES |
FEEDS |
TRIGGERS |
PRECEDES

<br><br>

<b>Logic</b><br>
AND |
OR |
XOR |
NOT |
IF-THEN

<br><br>

<b>System Dynamics</b><br>
FEEDBACK |
POSITIVE-FEEDBACK |
NEGATIVE-FEEDBACK

</div>
""",
            unsafe_allow_html=True,
        )


        # =====================================================================
        # PRIMARY HIERARCHOGRAPH
        # =====================================================================

        st.divider()

        st.subheader(
            "🕸️ PRIMARY HIERARCHOGRAPH"
        )

        st.caption(
            "The graph simultaneously represents semantic hierarchy, "
            "polyhierarchy, associative relations, UML structure, "
            "operational transformations, system states and feedback. "
            f"Displayed nodes: up to {graph_node_limit}."
        )

        render_cytoscape_network(
            graph_data,
            layout_type=graph_perspective,
            container_id=f"primary_{int(time.time() * 1000)}",
            max_nodes=graph_node_limit,
        )


    except Exception as exc:

        st.error(
            f"❌ Pipeline Failure: {type(exc).__name__}: {exc}"
        )

        st.exception(exc)


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
        "visual grammars. The data model remains identical."
    )

    gallery_tabs = st.tabs(
        [
            "🌳 HIERARCHOGRAPH",
            "🌲 HIERARCHICAL",
            "⚙️ OPERATIONAL",
            "🌐 ORGANIC",
            "🎯 CONCENTRIC",
            "⭕ CIRCULAR",
            "🔲 GRID",
        ]
    )

    gallery_views = [
        ("hierarchographic", "Polyhierarchical semantic architecture."),
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
                st.session_state.final_graph_elements,
                layout_type=view,
                container_id=f"gallery_{view}",
                max_nodes=graph_node_limit,
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
