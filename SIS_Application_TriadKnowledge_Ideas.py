import streamlit as st
import json
import base64
import requests
import urllib.parse
import re
import time
import io
import html
from datetime import datetime
from google import genai
from google.genai import types
import streamlit.components.v1 as components


# =============================================================================
# [NOVO] CRIME & STRESS PREVENTION MODULE (vgrajen; prej crime_stress_module.py)
# Vsebina izhaja iz: K. Petrič (2026), Hierarchology and Hierarchography (Short version),
# §4.5 stres, §4.8 intrige, §4.9 kriminaliteta, §7.2 intervencije in etika, §7.3 revščina.
# Modul je dodatek: ne spreminja obstoječih funkcij, promptov ali grafa.
# =============================================================================
# =============================================================================
# 1. KNOWLEDGE: STRESS (§4.5.1, §4.5.4, §4.6, §4.8)
# =============================================================================
STRESS_KNOWLEDGE = {
    "Stress as systemic indicator": "Stress is both an individual experience and a societal indicator of organizational/institutional dysfunction; the book compares it in significance to environmental degradation and structural unemployment.",
    "Eustress vs. distress": "Moderate stress (eustress) improves concentration, motivation and performance; the problem is stress that is excessive, chronic and hard to control.",
    "Person-environment interaction": "Stress emerges from the relation between environmental demands and an individual's capacity to respond; it is neither purely external nor purely internal.",
    "Biological-social mismatch": "Human physiology changes slowly while social change accelerates (urbanization, information load, consumer culture), producing an 'illusion of comfort': more physical convenience, more psychological burden.",
    "Dominant social stressors": "Fear, coercion, interpersonal conflict, uncertainty, excessive workload, poor communication, unequal treatment, workplace bullying, unrealistic expectations, lack of autonomy.",
    "Weak physical stressors": "In the book's empirical study noise, smell, temperature and lighting contributed relatively little compared with social and performance-related stressors.",
    "Institutional stress generators": "Rigid bureaucracy, excessive procedures, ineffective communication channels, inadequate leadership and authoritarian management suppress autonomy and cause frustration, alienation and exhaustion.",
    "Physiological consequences": "Headaches, cardiovascular disorders, digestive problems, sleep disturbance, chronic fatigue, weakened immunity.",
    "Psychological consequences": "Anxiety disorders, depression, emotional instability, helplessness, reduced motivation, lower life satisfaction.",
    "Social consequences": "Absenteeism, workplace conflict, burnout, substance abuse, family instability, weakened social cohesion.",
    "Stress -> deviance (hypothesis)": "Persistent distress MAY contribute to aggression, corruption, abuse of authority and unethical behaviour by reducing the capacity for rational and ethical decision-making. The book frames this as complex and multidimensional, not deterministic.",
    "Mental illness as process": "Vulnerability + prolonged pressure + weak support accumulate until a threshold is crossed; early signs are sleep disturbance, irritability, restlessness, emotional fatigue.",
    "Stigma": "Labeling, exclusion and devaluation of people in psychological distress; it deepens distress and blocks help-seeking.",
    "Intrigue": "Concealed, indirect influence in asymmetrical hierarchies; erodes trust, drains collective energy ('social waste') and is an adaptation to institutions rewarding image over substance.",
}

# =============================================================================
# 2. KNOWLEDGE: CRIME (§4.9, §7.2)
# =============================================================================
CRIME_KNOWLEDGE = {
    "Multidimensional causation": "Criminality emerges from interacting biological, psychological, sociological, economic, legal, technological, environmental and informational factors; no single discipline explains it.",
    "Three-Cosmos Model of Harm": "Microcosm = genes, neurons, hormones, microorganisms; Mesocosm = families, organizations, institutions, communities; Macrocosm = ecological, climatic, planetary influences.",
    "Mesocosmic bias": "Empirical finding: respondents from all disciplines focus mainly on mesocosmic (social/institutional) explanations; micro- and macrocosmic explanations are under-represented, likely due to measurement convenience rather than actual importance.",
    "Disciplinary divergence": "Applied sciences diverge most from the classical sociological view (predictive analytics, data mining, AI, complex networks); knowledge on crime stays fragmented across disciplines.",
    "Unified anomaly theory": "Crime externalizes disorder into the social environment; pollution externalizes it into nature. Both shift costs onto others and are diagnostic indicators of systemic imbalance.",
    "Legality vs. harm": "Legal definitions of crime do not always match the magnitude of harm; legal but harmful activity (e.g. large-scale pollution) may exceed criminal harm.",
    "Civilizational profiling": "Offender profiling (motives, needs, incentives) can be extended to institutions and industries; short-term reward orientation appears at individual and collective levels.",
    "Information pollution": "Disinformation, manipulative algorithms and attention-capturing technologies contaminate cognitive ecosystems and can indirectly amplify crime.",
    "Ecology of motivation": "Behaviour follows reward/punishment systems around survival, comfort, status, power, meaning and belonging; persistent harm is often motivational, not technological.",
    "Regeneration paradigm": "Shift from extraction to regeneration: resilience over short-term gain, cooperation over exploitation, systemic intelligence over isolated expertise.",
    "Poverty as high-entropy state": "Poverty framed as chronic biological stress (HPA axis, allostatic load) plus 'cognitive scarcity' that impairs decisions and entrenches deprivation cycles.",
}

# =============================================================================
# 3. INTERVENTION ARCHETYPES (§7.2.5, §7.3) - AI-generated HYPOTHESES, not validated
# =============================================================================
INTERVENTION_ARCHETYPES = {
    "Environmental entrainment therapy": {
        "desc": "Urban design that stabilizes collective circadian rhythm and cortisol regulation (light-dark cycles, natural soundscapes, thermal regulation, green infrastructure).",
        "stress_path": "environment -> neuroendocrine stress system -> lower arousal",
        "crime_path": "lower stress -> lower impulsivity/aggression -> fewer social conflicts",
        "caution": "Book's own data show physical stressors weaker than social ones: treat as hypothesis to be tested, not assumed.",
    },
    "Regenerative biotic city": {
        "desc": "Urban forests, algae-based purification, biophilic architecture as active contributors to mental health and social stability.",
        "stress_path": "green/biophilic exposure -> recovery from cognitive load",
        "crime_path": "social stability and cohesion -> lower crime opportunity/motivation",
        "caution": "Benefits may be unevenly distributed (green gentrification); monitor equity.",
    },
    "Neuro-empathy training": {
        "desc": "Non-invasive, consent-based empathy training in conflict simulations for police, rehabilitation and violence-prevention programs.",
        "stress_path": "emotion-regulation practice under simulated stress",
        "crime_path": "fewer escalations, better decisions under stress, higher public trust",
        "caution": "Consent, no coercive neuro-monitoring, human oversight.",
    },
    "Gut-brain axis intervention": {
        "desc": "Microbiome/nutrition-based regulation of serotonin precursors to lower aggression thresholds.",
        "stress_path": "gut-brain axis -> mood/stress reactivity",
        "crime_path": "lower aggression threshold (population-level, not individual prediction)",
        "caution": "Strong biological-reductionism risk; requires clinical validation and ethics review.",
    },
    "Quantum-inspired associative analytics": {
        "desc": "Associative reasoning systems detecting nonlinear links between stress markers and social outcomes.",
        "stress_path": "early detection of aggregate stress patterns",
        "crime_path": "proactive planning before escalation",
        "caution": "Algorithmic bias and surveillance risk; use only aggregated, privacy-preserving data.",
    },
    "NeuroPoverty Index (NPI)": {
        "desc": "Measures neurological stress load (cortisol, HRV) as an indicator of economic distress instead of income/GDP alone.",
        "stress_path": "biomarker-based community stress load",
        "crime_path": "targets prevention where structural deprivation drives risk",
        "caution": "Biomarker data are highly sensitive: on-device processing / differential privacy / aggregate-only reporting.",
    },
    "Poverty-Proofing Infrastructure (PPI / PRUP)": {
        "desc": "Poverty-resilient urban planning: green infrastructure, decentralized resources, biophilic design; identify 'criticality' tipping points.",
        "stress_path": "lower allostatic load through resource access",
        "crime_path": "fewer deprivation-driven offences via structural resilience",
        "caution": "Needs local participation and longitudinal evaluation.",
    },
}

# =============================================================================
# 4. ETHICAL SAFEGUARDS (§7.2.8) AND EVALUATION CRITERIA (§7.2.4)
# =============================================================================
ETHICAL_SAFEGUARDS = {
    "Privacy and surveillance": "Biosensors, neuro-monitoring and stress analytics threaten civil liberties: require democratic oversight, consent, data minimization.",
    "Algorithmic bias": "Crime-prediction systems can reproduce social inequality: require transparency, accountability, bias audits and human oversight.",
    "Biological reductionism": "Crime is never reducible to neurophysiology; it emerges from culture, inequality, trauma, institutions, history and environment.",
    "Dependence on AI": "AI is an assistive cognitive tool; ethical reasoning, empathy and democratic accountability remain human responsibilities.",
    "Technological limitations": "Hallucinations, contextual instability and incomplete causal understanding remain; ideas are hypotheses until empirically validated.",
}

EVALUATION_CRITERIA = [
    "Conceptual novelty",
    "Interdisciplinary integration",
    "System architecture quality",
    "Practical applicability",
    "Clarity and coherence",
]

# =============================================================================
# 5. CANONICAL RELATIONS (hints for the semantic graph; use ONLY if supported by text)
#    (source, target, rel_type, human-readable label)
# =============================================================================
STRESS_CRIME_PATHWAYS = [
    ("Social stressors", "Chronic distress", "IF-THEN", "generate"),
    ("Chronic distress", "Reduced ethical decision capacity", "IF-THEN", "weakens"),
    ("Reduced ethical decision capacity", "Aggression / deviance risk", "IF-THEN", "raises"),
    ("Bureaucratic hierarchy", "Social stressors", "IF-THEN", "amplifies"),
    ("Poverty", "Allostatic load", "IF-THEN", "increases"),
    ("Microcosm", "Three-Cosmos Model", "BT", "is part of"),
    ("Mesocosm", "Three-Cosmos Model", "BT", "is part of"),
    ("Macrocosm", "Three-Cosmos Model", "BT", "is part of"),
    ("Stress", "Crime", "AS", "associated with (hypothesis)"),
    ("Stigma", "Help-seeking", "IF-THEN", "reduces help-seeking"),
    ("Regenerative city", "Chronic distress", "IF-THEN", "mitigates chronic distress"),
]

# =============================================================================
# 6. EXTENSIONS OF EXISTING ONTOLOGIES (merge with .update(), nothing is removed)
# =============================================================================
# Science fields named in the book's 100-iteration crime/stress study (§7.2.4)
# that are missing in KNOWLEDGE_BASE["Science fields"].
EXTRA_SCIENCE_FIELDS = {
    "Urbanism": {
        "cat": "Applied/Social",
        "methods": ["Spatial Analysis", "Participatory Planning", "Environmental Design Evaluation", "Post-Occupancy Evaluation"],
        "tools": ["GIS", "Noise/Light Mapping", "Space Syntax", "Urban Digital Twins"],
        "facets": ["Green Infrastructure", "Biophilic Design", "Public Space", "Crime Prevention Through Environmental Design"],
    },
    "Environmental Science": {
        "cat": "Natural/Applied",
        "methods": ["Environmental Monitoring", "Exposure Assessment", "Life-Cycle Assessment", "Ecosystem Services Valuation"],
        "tools": ["Air/Water Sensors", "Remote Sensing", "Satellite Imagery", "Biosensors"],
        "facets": ["Pollution", "Environmental Health", "Ecosystem Resilience", "Climate Adaptation"],
    },
}

# Book's 100-iteration crime/stress field set (§7.2.4) - preset for the multiselect.
CRIME_STRESS_SCIENCE_PRESET = [
    "Criminology", "Sociology", "Neuroscience", "Psychology", "Psychiatry",
    "Medicine", "Biology", "Computer Science", "Library Science", "Engineering",
    "Urbanism", "Environmental Science", "Philosophy", "Economics",
    "Legal science", "Geography",
]

# Additional IMA metamodel nodes (same structure as HUMAN_THINKING_METAMODEL["nodes"])
CRIME_STRESS_METAMODEL_NODES = {
    "Stress (eustress/distress)": {"color": "#F4A261", "shape": "rectangle",
        "desc": "Person-environment strain: moderate stress mobilizes, chronic distress drains energy and degrades ethical decision-making; also a societal indicator."},
    "Allostatic load": {"color": "#E9C46A", "shape": "rectangle",
        "desc": "Cumulative physiological burden of persistent stressors (HPA axis); links poverty, stress and cognitive scarcity."},
    "Harmful behavior / crime": {"color": "#E76F51", "shape": "rectangle",
        "desc": "Multi-causal outcome across micro-, meso- and macrocosm; a diagnostic indicator of systemic imbalance rather than only an individual defect."},
    "Preventive intervention": {"color": "#2A9D8F", "shape": "rectangle",
        "desc": "Environmental, institutional or educational measure acting before escalation; evaluated by novelty, integration, architecture, applicability, clarity."},
    "Ethical safeguard": {"color": "#FFC000", "shape": "rectangle",
        "desc": "Concrete protection against surveillance, bias, reductionism and over-reliance on AI (consent, aggregation, audits, human oversight)."},
}

# =============================================================================
# 7. RELEVANCE DETECTION + PROMPT ADDENDA
# =============================================================================
_CS_PATTERN = re.compile(
    r"(crim|kriminal|violen|nasilj|delinq|offen[cs]|prestop|stres|stress|burnout|izgorel|"
    r"aggress|agresi|anxiet|tesnob|allostatic|mental health|dušev|duševn)",
    re.IGNORECASE | re.UNICODE,
)

CS_MODES = ["Auto (detect from inquiry)", "Always on", "Off"]


def crime_stress_should_activate(mode, *texts):
    """mode: one of CS_MODES. Returns True if the module should be injected."""
    if mode == "Always on":
        return True
    if mode == "Off":
        return False
    return any(t and _CS_PATTERN.search(t) for t in texts)


def _digest(d):
    return "\n".join(f"   • {k}: {v}" for k, v in d.items())


def build_phase1_addendum():
    """Text PREPENDED to the Phase 1 system prompt (so the output-format rules stay last). Adds NO new section headers."""
    return f"""

### CRIME & STRESS THEMATIC REINFORCEMENT (Phase 1)
Domain knowledge to use ONLY where relevant to the inquiry (source: Petrič 2026).
STRESS:
{_digest(STRESS_KNOWLEDGE)}
CRIME:
{_digest(CRIME_KNOWLEDGE)}

Rules for this domain (apply inside the existing seven sections; do not add headers):
- Treat stress and crime as MULTI-CAUSAL. In section 3 explicitly assign factors to
  microcosm (genes, neurons, hormones, microbiome), mesocosm (family, workplace,
  institutions, community) and macrocosm (ecology, climate, planetary). Explicitly
  check for MESOCOSMIC BIAS: state which micro/macro explanations were neglected.
- Separate eustress from distress, and individual stress from stress as a SYSTEMIC
  indicator of organizational dysfunction.
- Present stress -> crime/deviance links as plausible, non-deterministic HYPOTHESES.
  Never claim direct causation; put them on the interpretation side of section 6.
- In section 4 list cross-disciplinary tension points, including: (a) social vs.
  physical stressors (the source study found physical stressors weak), (b) biological
  vs. sociological explanations of crime, (c) legality vs. actual harm.
- In section 5 include the ethical constraints: privacy/surveillance, algorithmic
  bias, biological reductionism, dependence on AI, technological limitations.
- In section 7 state which stress pathway and which crime pathway Phase 2 must address.
"""


def build_phase2_addendum():
    """Text PREPENDED to the Phase 2 system prompt (so the JSON output rules stay last). Keeps the existing bullet structure."""
    interventions = "\n".join(
        f"   • {k}: {v['desc']} [stress: {v['stress_path']}; crime: {v['crime_path']}; caution: {v['caution']}]"
        for k, v in INTERVENTION_ARCHETYPES.items()
    )
    safeguards = _digest(ETHICAL_SAFEGUARDS)
    pathways = "\n".join(f"   • {s} --{r}--> {t}  ({l})" for s, t, r, l in STRESS_CRIME_PATHWAYS)
    criteria = ", ".join(EVALUATION_CRITERIA)
    return f"""

### CRIME & STRESS THEMATIC REINFORCEMENT (Phase 2)
Reference archetypes from prior work (AI-generated HYPOTHESES, not validated). Use
them only as inspiration; do NOT copy them. A valid innovation must be a genuine
transformation of the Phase 1 findings:
{interventions}

Domain rules (extend, do not replace, the innovation structure and output format given further below):
- Every innovation must state in "Expected effect" TWO separate lines: the STRESS-side
  effect and the CRIME/HARM-side effect, each with one measurable indicator and how it
  would be evaluated. If it addresses only one side, say so and justify.
- Name the level(s) it acts on (micro/meso/macro). At least one innovation must act
  on the macrocosm or microcosm, not only on the mesocosm, to counter mesocosmic bias.
- Prefer ENVIRONMENT-, INSTITUTION- and POLICY-level interventions and aggregated
  indicators over individual-level prediction or profiling of persons.
- Reject or reframe any idea that relies on individual-level crime prediction,
  covert biometric monitoring or coercive neuro-intervention.
- Whenever an idea touches health, biometric, behavioral or predictive data, the
  Safeguards bullet must name a concrete mechanism (on-device aggregation, differential
  privacy, informed consent, bias audit, human-in-the-loop) and address these risks:
{safeguards}
- Self-rate each innovation 1-10 on: {criteria}. Show the numbers in the
  "Expected effect" bullet only as a rough self-assessment, never as evidence.
- Graph guidance: if the inquiry names stress and/or crime, each MUST have its own
  star (goal/outcome) node, and innovations must connect to them with labels such as
  "mitigates", "prevents", "reduces". Keep micro/meso/macro in node descriptions.
  Canonical relations you MAY reuse ONLY when the report text supports them:
{pathways}
"""


# =============================================================================
# 9. STREAMLIT UI HELPERS (receive `st`; no streamlit import needed here)
# =============================================================================
def render_crime_stress_sidebar(st):
    """Call inside `with st.sidebar:` after the existing Knowledge Explorer expanders."""
    with st.expander("🛡️ Crime & Stress Prevention Ontology", expanded=False):
        st.markdown("**Stress (§4.5):**")
        for k, v in STRESS_KNOWLEDGE.items():
            st.markdown(f"• **{k}**: {v}")
        st.markdown("---")
        st.markdown("**Crime & harm (§4.9):**")
        for k, v in CRIME_KNOWLEDGE.items():
            st.markdown(f"• **{k}**: {v}")
        st.markdown("---")
        st.markdown("**Intervention archetypes (hypotheses, §7.2.5, §7.3):**")
        for k, d in INTERVENTION_ARCHETYPES.items():
            st.markdown(f"• **{k}**: {d['desc']} *Caution: {d['caution']}*")
        st.markdown("---")
        st.markdown("**Ethical safeguards (§7.2.8):**")
        for k, v in ETHICAL_SAFEGUARDS.items():
            st.markdown(f"• **{k}**: {v}")
        st.markdown("---")
        st.markdown("**Evaluation criteria:** " + ", ".join(EVALUATION_CRITERIA))
        st.markdown("**Science preset (§7.2.4):** " + ", ".join(CRIME_STRESS_SCIENCE_PRESET))


def render_crime_stress_mode(st):
    """Main-page selector. Returns one of CS_MODES."""
    return st.selectbox(
        "🛡️ Crime & Stress Prevention module:",
        CS_MODES,
        index=0,
        key="cs_module_mode_v2026",
        help="Auto: activates when the inquiry mentions crime, violence, stress, burnout... "
             "Adds domain knowledge, ethical safeguards and dual (stress + crime) outcome "
             "requirements to Phase 1 and Phase 2 prompts. Existing pipeline is unchanged.",
    )

# =============================================================================
# 0. GLOBAL CONFIGURATION & SESSION DATE (FEBRUARY 24, 2026)
# =============================================================================
SYSTEM_DATE = datetime.now().strftime("%B %d, %Y")
VERSION_CODE = "v24.8.0-GOOGLE-GEMINI-ONLY-SINGLE-GRAPH-DIVERSE"

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

    /* 6. REPORT OVERVIEW CARD (descriptive reporting) */
    .report-overview {
        background: #ffffff;
        border: 1px solid #e9ecef;
        border-left: 8px solid #1d3557;
        border-radius: 15px;
        padding: 20px 28px;
        margin-bottom: 25px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        color: #1d3557;
        line-height: 1.7;
    }
    .report-overview b { color: #1d3557; }
    .report-overview .ro-title {
        font-size: 0.8em; font-weight: 800; letter-spacing: 1px;
        text-transform: uppercase; color: #457b9d; margin-bottom: 8px;
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

# Three selectable views of ONE graph (switched client-side, no Streamlit rerun).
GRAPH_VIEWS = ["organic", "hierarchical", "circular"]
GRAPH_VIEW_LABELS = {"organic": "🌿 Organic view", "hierarchical": "🌲 Hierarchical view", "circular": "⭕ Circular view"}

LAYOUTS_JS = """{
    organic: {
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
    },
    hierarchical: {
        name: 'breadthfirst',
        directed: true,
        padding: 50,
        circle: false,
        spacingFactor: 1.75,
        maximal: true,
        fit: true
    },
    circular: {
        name: 'circle',
        padding: 50,
        radius: 400,
        spacingFactor: 0.8,
        fit: true
    }
}"""


def render_cytoscape_network(elements, layout_type="organic", container_id="cy_canvas"):
    """
    Single interactive graph with three switchable views (Organic / Hierarchical / Circular).
    The view switch runs in the browser, so the report is never re-generated.
    Includes UML, ISO Thesaurus, operational logic and NEG-FEEDBACK connectors.
    """
    initial_view = layout_type if layout_type in GRAPH_VIEWS else "organic"

    view_buttons = "".join(
        f'<button id="view_{v}_{container_id}" style="padding: 8px 11px; background: #6366f1; color: white; border: none; border-radius: 7px; cursor: pointer; font-weight: 800;">{GRAPH_VIEW_LABELS[v]}</button>'
        for v in GRAPH_VIEWS
    )

    cyto_html = f"""
    <div style="position: relative; width: 100%;">
        <div style="position: absolute; top: 15px; left: 15px; z-index: 1000; display: flex; gap: 6px; flex-wrap: wrap;">
            {view_buttons}
        </div>
        <div style="position: absolute; top: 15px; right: 15px; z-index: 1000; display: flex; gap: 6px; flex-wrap: wrap; justify-content: flex-end;">
            <button id="zoom_in_{container_id}" style="padding: 8px 11px; background: #1d3557; color: white; border: none; border-radius: 7px; cursor: pointer; font-weight: 800;">＋ Zoom In</button>
            <button id="zoom_out_{container_id}" style="padding: 8px 11px; background: #457b9d; color: white; border: none; border-radius: 7px; cursor: pointer; font-weight: 800;">− Zoom Out</button>
            <button id="zoom_fit_{container_id}" style="padding: 8px 11px; background: #2a9d8f; color: white; border: none; border-radius: 7px; cursor: pointer; font-weight: 800;">⛶ Fit</button>
            <button id="save_btn_{container_id}" style="padding: 8px 11px; background: #1d3557; color: white; border: none; border-radius: 7px; cursor: pointer; font-weight: 800;">💾 PNG</button>
        </div>
        <div id="{container_id}" style="width: 100%; height: 850px; background: #ffffff; border-radius: 20px; border: 1px solid #e0e0e0; box-shadow: 0 10px 40px rgba(0,0,0,0.08);"></div>
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.26.0/cytoscape.min.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            var layouts = {LAYOUTS_JS};
            var currentView = '{initial_view}';
            var viewNames = ['organic', 'hierarchical', 'circular'];

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
                            'label': 'data(label)',
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
                    
                    /* --- CONTROL / FEEDBACK --- */
                    {{ selector: 'edge[rel_type="NEG-FEEDBACK"]', style: {{ 'width': 5, 'line-color': '#6A4C93', 'target-arrow-color': '#6A4C93', 'target-arrow-shape': 'tee', 'line-style': 'dashed', 'curve-style': 'bezier' }} }},
                    {{ selector: 'edge[evidence="hypothesis"]', style: {{ 'line-style': 'dotted', 'opacity': 0.72 }} }},
                    {{ selector: 'edge[evidence="future-test"]', style: {{ 'line-style': 'dotted', 'opacity': 0.58 }} }},

                    /* --- LOGIČNI KONEKTORJI (Decision Logic) --- */
                    {{ selector: 'edge[rel_type="AND"]', style: {{ 'width': 5, 'line-color': '#00FF00', 'target-arrow-color': '#00FF00', 'target-arrow-shape': 'triangle' }} }},
                    {{ selector: 'edge[rel_type="OR"]', style: {{ 'width': 3, 'line-color': '#00BFFF', 'line-style': 'dashed', 'target-arrow-color': '#00BFFF', 'target-arrow-shape': 'vee' }} }},
                    {{ selector: 'edge[rel_type="XOR"]', style: {{ 'width': 4, 'line-color': '#FF8C00', 'line-style': 'double', 'target-arrow-color': '#FF8C00', 'target-arrow-shape': 'diamond' }} }},
                    {{ selector: 'edge[rel_type="NOT"]', style: {{ 'width': 4, 'line-color': '#FF0000', 'line-style': 'dashed', 'target-arrow-color': '#FF0000', 'target-arrow-shape': 'tee' }} }},
                    {{ selector: 'edge[rel_type="IF-THEN"]', style: {{ 'width': 4, 'line-color': '#FFD700', 'target-arrow-color': '#FFD700', 'target-arrow-shape': 'triangle', 'arrow-scale': 1.3 }} }},

                    /* Poudarek na zvezdah (Macro cilji) */
                    {{ selector: 'node[shape="star"]', style: {{ 'font-size': '16px', 'width': 130, 'height': 130, 'border-width': 5, 'border-color': '#FFD700' }} }}
                ],
                layout: layouts[currentView]
            }});

            function highlightActiveView() {{
                viewNames.forEach(function(v) {{
                    var b = document.getElementById('view_' + v + '_{container_id}');
                    if (!b) return;
                    b.style.opacity = (v === currentView) ? '1' : '0.55';
                    b.style.outline = (v === currentView) ? '3px solid #FFD700' : 'none';
                }});
            }}
            function switchView(v) {{
                currentView = v;
                highlightActiveView();
                cy.layout(layouts[v]).run();
            }}
            viewNames.forEach(function(v) {{
                document.getElementById('view_' + v + '_{container_id}').addEventListener('click', function() {{ switchView(v); }});
            }});
            highlightActiveView();

            document.getElementById('zoom_in_{container_id}').addEventListener('click', function() {{
                cy.zoom({{ level: Math.min(cy.zoom() * 1.25, 4), renderedPosition: {{ x: cy.width()/2, y: cy.height()/2 }} }});
            }});
            document.getElementById('zoom_out_{container_id}').addEventListener('click', function() {{
                cy.zoom({{ level: Math.max(cy.zoom() / 1.25, 0.15), renderedPosition: {{ x: cy.width()/2, y: cy.height()/2 }} }});
            }});
            document.getElementById('zoom_fit_{container_id}').addEventListener('click', function() {{
                cy.fit(undefined, 50);
            }});
            document.getElementById('save_btn_{container_id}').addEventListener('click', function() {{
                var png64 = cy.png({{full: true, bg: 'white', scale: 2}});
                var link = document.createElement('a');
                var timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
                link.href = png64;
                link.download = 'hierarchograph_' + currentView + '_' + timestamp + '.png';
                link.click();
            }});
        }});
    </script>
    """
    components.html(cyto_html, height=900)

import math # Move all imports to the top of your script if possible

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

# =============================================================================
# 3.2 RELATION-FAMILY CONSTANTS (shared by diagnostic + auto-rebalancer)
# =============================================================================
THESAURUS_TYPES = {"TT", "BT", "NT", "RT", "EQ", "AS", "IN"}
LOGIC_TYPES = {"AND", "OR", "XOR", "NOT", "IF-THEN"}
STRUCTURAL_TYPES = {"Generalization", "Specialization", "Containment",
                     "Realization", "Composition", "Aggregation",
                     "Dependency", "Conflict"}
# System-dynamics relation. This is deliberately distinct from logical NOT.
CONTROL_TYPES = {"NEG-FEEDBACK"}
ALL_RELATION_TYPES = THESAURUS_TYPES | LOGIC_TYPES | STRUCTURAL_TYPES | CONTROL_TYPES

RELATION_FAMILY = {
    **{r: "Thesaurus" for r in THESAURUS_TYPES},
    **{r: "Operational Logic" for r in LOGIC_TYPES},
    **{r: "Structural/UML" for r in STRUCTURAL_TYPES},
    **{r: "Control/Feedback" for r in CONTROL_TYPES},
}

RELATION_LABEL_DEFAULTS = {
    "TT": "top-level concept",
    "BT": "has broader term",
    "NT": "has narrower term",
    "RT": "is related to",
    "AS": "is associatively linked to",
    "EQ": "denotes the same concept as",
    "IN": "is an instance of",
    "AND": "is jointly required with",
    "OR": "provides an alternative to",
    "XOR": "excludes the alternative",
    "NOT": "negates or excludes",
    "IF-THEN": "enables / causes",
    "NEG-FEEDBACK": "counteracts / attenuates",
    "Generalization": "generalizes",
    "Specialization": "specializes",
    "Containment": "contains",
    "Realization": "realizes",
    "Composition": "is composed of",
    "Aggregation": "aggregates",
    "Dependency": "depends on",
    "Conflict": "conflicts with",
}


UML_RELATION_PRIORITY = {"Composition":10,"Aggregation":9,"Containment":8,"Generalization":8,"Specialization":8,"Realization":8,"Dependency":7,"Conflict":7}
UML_CUE_RULES = {
 "Composition": ("composed of","essential part","integral part","cannot exist independently","lifecycle depends on","made up of"),
 "Aggregation": ("consists of","aggregates","collection of","group of","independent component","independently exists"),
 "Containment": ("contains","contained in","within","inside","embedded in","includes a subsystem","hosts"),
 "Dependency": ("depends on","requires","uses","relies on","needs","dependent on","requires access to"),
 "Realization": ("implements","implementation of","realizes","realisation of","implements the specification","implements the method"),
 "Generalization": ("generalizes","is a general category","broader class","superclass","general concept"),
 "Specialization": ("specializes","special case of","subtype","subclass","specific implementation","specialized form"),
 "Conflict": ("conflicts with","contradicts","incompatible with","mutually incompatible","opposes","constraint conflict")
}
def _edge_semantic_text(edge):
 return " ".join(str(edge.get(k) or "") for k in ("label","description","relation","meaning","evidence")).lower()
def _uml_cue_score(rel, edge):
 return sum(1 for cue in UML_CUE_RULES.get(rel,()) if cue in _edge_semantic_text(edge))

def normalize_relation_type(value):
    raw = str(value or "").strip()
    aliases = {
        "IFTHEN": "IF-THEN",
        "IF_THEN": "IF-THEN",
        "IF THEN": "IF-THEN",
        "NEGATIVE-FEEDBACK": "NEG-FEEDBACK",
        "NEGATIVE_FEEDBACK": "NEG-FEEDBACK",
        "FEEDBACK-NEG": "NEG-FEEDBACK",
        "FEEDBACK": "NEG-FEEDBACK",
    }
    return aliases.get(raw.upper(), raw)


def lint_semantic_graph(g_data, max_nodes=30, max_edges=60):
    """Semantic validator between Gemini JSON and Cytoscape.

    The linter removes malformed or semantically unsupported edges, normalizes
    relation codes, records evidence status and diagnostics, but NEVER invents
    RT/other bridge edges merely to make the graph connected or to satisfy a
    diversity quota. Semantic validity has priority over numerical diversity.
    """
    warnings = []
    errors = []
    removed_edges = 0

    if not isinstance(g_data, dict):
        return {"nodes": [], "edges": [], "system_metrics": {}}, {
            "warnings": ["Graph root is not a JSON object."],
            "errors": [], "removed_edges": 0,
            "family_counts": {}, "components": 0
        }

    nodes = g_data.get("nodes", [])
    edges = g_data.get("edges", [])
    nodes = nodes if isinstance(nodes, list) else []
    edges = edges if isinstance(edges, list) else []

    valid_shapes = {"star", "hexagon", "diamond", "triangle", "octagon", "ellipse", "rectangle"}
    clean_nodes = []
    node_ids = set()

    for i, node in enumerate(nodes[:max_nodes]):
        if not isinstance(node, dict):
            continue
        node_id = str(node.get("id") or f"n{i+1}")
        label = str(node.get("label") or "").strip()
        if not label:
            warnings.append(f"Node {node_id} removed because it has no label.")
            continue
        if node_id in node_ids:
            warnings.append(f"Duplicate node removed: {node_id}")
            continue
        shape = str(node.get("shape") or "rectangle")
        if shape not in valid_shapes:
            warnings.append(f"Invalid shape for '{label}'; changed to rectangle.")
            shape = "rectangle"
        node_ids.add(node_id)
        clean_nodes.append({
            **node,
            "id": node_id,
            "label": label,
            "shape": shape,
            "description": str(node.get("description") or "")
        })

    clean_edges = []
    seen_pairs = set()

    for edge in edges:
        if not isinstance(edge, dict):
            removed_edges += 1
            continue
        source = str(edge.get("source") or "")
        target = str(edge.get("target") or "")
        rel = normalize_relation_type(edge.get("rel_type"))

        if source not in node_ids or target not in node_ids:
            removed_edges += 1
            warnings.append(f"Edge removed: unknown node {source!r} or {target!r}.")
            continue
        if rel not in ALL_RELATION_TYPES:
            removed_edges += 1
            warnings.append(f"Unsupported relation removed: {rel}")
            continue

        # Candidate edges are resolved after normalization so a generic RT/AS/IF-THEN
        # cannot hide a more informative UML relation for the same pair.
        pair = frozenset((source, target))

        evidence = str(edge.get("evidence") or "inferred").lower().strip()
        if evidence not in {"explicit", "inferred", "hypothesis", "future-test"}:
            evidence = "inferred"

        label = str(edge.get("label") or "").strip()
        if not label or label.upper() == rel.upper():
            label = RELATION_LABEL_DEFAULTS.get(rel, rel.lower())

        clean_edges.append({
            **edge,
            "source": source,
            "target": target,
            "rel_type": rel,
            "label": label,
            "evidence": evidence,
            "family": RELATION_FAMILY[rel]
        })

    # Resolve parallel candidates. Prefer an explicit UML relation when the
    # report actually describes structure/action; otherwise prefer evidence strength.
    grouped = {}
    for edge in clean_edges:
        grouped.setdefault(frozenset((edge["source"], edge["target"])), []).append(edge)
    resolved_edges = []
    ev_prio = {"explicit":4,"hypothesis":3,"future-test":2,"inferred":1}
    fam_prio = {"Control/Feedback":4,"Structural/UML":3,"Operational Logic":2,"Thesaurus":1}
    for pair, candidates in grouped.items():
        if len(candidates) == 1:
            resolved_edges.append(candidates[0]); continue
        def score(e):
            return (fam_prio.get(e["family"],0), UML_RELATION_PRIORITY.get(e["rel_type"],0)+_uml_cue_score(e["rel_type"],e), ev_prio.get(e["evidence"],1))
        winner=max(candidates,key=score); resolved_edges.append(winner)
        for loser in candidates:
            if loser is not winner:
                removed_edges += 1
                warnings.append(f"Parallel relation resolved for {loser['source']} ↔ {loser['target']}: kept {winner['rel_type']} over {loser['rel_type']}.")
    clean_edges = resolved_edges

    # Prefer explicit evidence, then hypotheses, then inferred links when an
    # unusually large graph has to be reduced.
    if len(clean_edges) > max_edges:
        priority = {"explicit": 3, "hypothesis": 2, "future-test": 2, "inferred": 1}
        clean_edges.sort(key=lambda e: priority.get(e.get("evidence"), 1), reverse=True)
        clean_edges = clean_edges[:max_edges]
        warnings.append(f"Graph reduced to maximum {max_edges} edges.")

    family_counts = {
        "Thesaurus": 0,
        "Operational Logic": 0,
        "Structural/UML": 0,
        "Control/Feedback": 0
    }
    for edge in clean_edges:
        family_counts[edge["family"]] += 1

    total = len(clean_edges)
    if total:
        for family in ("Thesaurus", "Operational Logic"):
            share = family_counts[family] / total
            if share < 0.25:
                warnings.append(
                    f"{family} diversity below 25% ({share:.0%}); no artificial edges were created."
                )

    # Basic semantic-direction checks. The linter flags suspicious directions
    # rather than silently reversing model output.
    node_labels = {n["id"]: n["label"] for n in clean_nodes}
    for edge in clean_edges:
        rel = edge["rel_type"]
        if rel in {"IF-THEN", "Dependency", "Realization", "AND", "OR"} and edge["source"] == edge["target"]:
            warnings.append(f"Self-loop is suspicious for {rel}: {node_labels.get(edge['source'], edge['source'])}.")
        if rel == "NEG-FEEDBACK" and edge["source"] == edge["target"]:
            warnings.append("NEG-FEEDBACK self-loop detected; verify that a genuine regulation mechanism exists.")

    # Connected-component diagnostic only. No artificial bridge is inserted.
    adjacency = {nid: set() for nid in node_ids}
    for edge in clean_edges:
        adjacency[edge["source"]].add(edge["target"])
        adjacency[edge["target"]].add(edge["source"])
    components = 0
    unseen = set(node_ids)
    while unseen:
        components += 1
        stack = [unseen.pop()]
        while stack:
            cur = stack.pop()
            for nxt in adjacency.get(cur, set()):
                if nxt in unseen:
                    unseen.remove(nxt)
                    stack.append(nxt)

    isolated = [nid for nid in node_ids if not adjacency[nid]]
    if isolated:
        warnings.append(
            "Isolated nodes remain; they were NOT artificially connected: " +
            ", ".join(node_labels.get(n, n) for n in isolated)
        )

    return {
        "nodes": clean_nodes,
        "edges": clean_edges,
        "system_metrics": g_data.get("system_metrics", {})
    }, {
        "warnings": warnings,
        "errors": errors,
        "removed_edges": removed_edges,
        "family_counts": family_counts,
        "components": components,
        "isolated": isolated
    }

# =============================================================================
# 3.2.1 [NOVO] GRAPH DIVERSITY GUARD — obvezna raznolikost relacij in oblik
# =============================================================================
# Težava: Gemini je proizvajal skoraj izključno IF-THEN povezave, tezaver
# (TT/BT/NT/RT/AS/EQ/IN) in UML povezave pa so bile redke ali odsotne.
# Ta mehanizem v treh plasteh zagotavlja grafe, kakršni so v priponki:
#   (1) Phase 2 prompt zahteva OBVEZNE kvote po družinah relacij;
#   (2) check_graph_diversity() po parsanju preveri, ali so kvote izpolnjene;
#   (3) če niso, en sam samodejni REPAIR klic ponovno proizvede JSON grafa
#       z izrecno zahtevo po manjkajočih družinah (vedno temelji na poročilu).
# =============================================================================
GRAPH_DIVERSITY_RULES = {
    "min_thesaurus_edges": 4,        # skupno št. tezaver-povezav
    "min_thesaurus_distinct": 3,    # različnih kod (TT/BT/NT/RT/AS/EQ/IN)
    "min_uml_edges": 4,              # skupno št. UML/strukturh povezav
    "min_uml_distinct": 3,           # različnih UML tipov
    "min_logic_edges": 2,            # AND/OR/XOR/NOT (IF-THEN se šteje ločeno)
    "max_ifthen_share": 0.40,        # IF-THEN največ 40 % vseh povezav
    "min_distinct_shapes": 5,        # raznolike geometrijske oblike vozlišč
}


def check_graph_diversity(g_data):
    """Preveri, ali graf izpolnjuje obvezne kvote raznolikosti relacij in oblik.

    Vrne (ok, metrics, failures):
      ok       - True, če so vse kvote izpolnjene
      metrics  - slovar števcev za prikaz/diagnostiko
      failures - seznam opisov manjkajočih zahtev (za repair prompt)
    """
    nodes = g_data.get("nodes") or []
    edges = g_data.get("edges") or []
    nodes = nodes if isinstance(nodes, list) else []
    edges = edges if isinstance(edges, list) else []

    rels = [normalize_relation_type(e.get("rel_type")) for e in edges
            if isinstance(e, dict) and normalize_relation_type(e.get("rel_type")) in ALL_RELATION_TYPES]
    shapes = {str(n.get("shape") or "rectangle") for n in nodes if isinstance(n, dict)}

    thes = [r for r in rels if r in THESAURUS_TYPES]
    uml = [r for r in rels if r in STRUCTURAL_TYPES]
    logic_non_ifthen = [r for r in rels if r in LOGIC_TYPES and r != "IF-THEN"]
    ifthen = [r for r in rels if r == "IF-THEN"]
    feedback = [r for r in rels if r in CONTROL_TYPES]

    total = len(rels)
    metrics = {
        "total_edges": total,
        "thesaurus_edges": len(thes),
        "thesaurus_distinct": sorted(set(thes)),
        "uml_edges": len(uml),
        "uml_distinct": sorted(set(uml)),
        "logic_non_ifthen": len(logic_non_ifthen),
        "ifthen_edges": len(ifthen),
        "ifthen_share": round(len(ifthen) / total, 2) if total else 0.0,
        "feedback_edges": len(feedback),
        "distinct_shapes": sorted(shapes),
    }

    failures = []
    R = GRAPH_DIVERSITY_RULES
    if total == 0:
        failures.append("The graph contains no valid edges at all.")
    if len(thes) < R["min_thesaurus_edges"]:
        failures.append(
            f"Thesaurus family (TT/BT/NT/RT/AS/EQ/IN) is under-represented: only {len(thes)} edge(s); "
            f"at least {R['min_thesaurus_edges']} are required, using at least {R['min_thesaurus_distinct']} "
            f"distinct codes."
        )
    if len(set(thes)) < R["min_thesaurus_distinct"]:
        failures.append(
            f"Only {len(set(thes))} distinct thesaurus code(s) in use; at least "
            f"{R['min_thesaurus_distinct']} different codes from TT, BT, NT, RT, AS, EQ, IN are required."
        )
    if len(uml) < R["min_uml_edges"]:
        failures.append(
            f"UML/Structural family (Composition, Aggregation, Containment, Dependency, Realization, "
            f"Generalization, Specialization, Conflict) is under-represented: only {len(uml)} edge(s); "
            f"at least {R['min_uml_edges']} are required, using at least {R['min_uml_distinct']} distinct types."
        )
    if len(set(uml)) < R["min_uml_distinct"]:
        failures.append(
            f"Only {len(set(uml))} distinct UML type(s) in use; at least {R['min_uml_distinct']} "
            f"different UML types are required."
        )
    if len(logic_non_ifthen) < R["min_logic_edges"]:
        failures.append(
            f"Operational Logic family (AND/OR/XOR/NOT) is under-represented: only "
            f"{len(logic_non_ifthen)} edge(s); at least {R['min_logic_edges']} are required."
        )
    if total and len(ifthen) / total > R["max_ifthen_share"]:
        failures.append(
            f"IF-THEN edges dominate the graph ({len(ifthen)}/{total} = "
            f"{len(ifthen)/total:.0%}). Reduce IF-THEN to at most "
            f"{R['max_ifthen_share']:.0%} of edges and express the other relations with their "
            f"proper types (thesaurus BT/NT/RT/AS/EQ/IN, UML Composition/Aggregation/Containment/"
            f"Dependency/Realization/Generalization/Specialization/Conflict, logic AND/OR/XOR/NOT, "
            f"control NEG-FEEDBACK)."
        )
    if len(shapes) < R["min_distinct_shapes"]:
        failures.append(
            f"Node geometry is too uniform: only {len(shapes)} distinct shape(s) "
            f"({', '.join(sorted(shapes))}); at least {R['min_distinct_shapes']} different shapes are "
            f"required (star=goal, hexagon=science field, diamond=innovation, triangle=process/method, "
            f"octagon=rule/contradiction, ellipse=human/biological entity, rectangle=fact/component)."
        )

    return (len(failures) == 0), metrics, failures


def parse_graph_json(text):
    """Robustno izlušči in parsaj JSON semantičnega grafa iz odgovora modela.

    Vrne (g_data_or_None, error_or_None).
    """
    if not text or not str(text).strip():
        return None, "Empty graph text."
    cleaned = str(text).strip()
    cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned, flags=re.I)
    cleaned = re.sub(r'\s*```$', '', cleaned)
    if "### SEMANTIC_GRAPH_JSON" in cleaned:
        cleaned = cleaned.split("### SEMANTIC_GRAPH_JSON", 1)[1]
    match = re.search(r'\{.*\}', cleaned, re.DOTALL)
    if not match:
        return None, "No JSON object found in the model output."
    cleaned = match.group(0)
    cleaned = re.sub(r',\s*([}\]])', r'\1', cleaned)
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed, None
        return None, "Parsed JSON is not an object."
    except Exception as exc:
        return None, str(exc)


def build_graph_repair_system_prompt(failures):
    """System prompt za samodejni REPAIR klic, ki graf naredi raznolikega.

    Ključno: popravljati je treba SAMO način KODIRANJA relacij (rel_type) in
    oblike vozlišč — ne vsebine poročila. Vse povezave morajo ostati
    utemeljene v istem besedilu poročila.
    """
    failure_text = "\n".join(f"- {f}" for f in failures)
    return f"""
You are the SIS Semantic Graph Auditor. A knowledge graph was generated from a
report, but it FAILED the relation-family and geometry diversity requirements.
Your ONLY task is to re-encode the SAME graph so that the relations are expressed
with their PROPER semantic types instead of collapsing everything into IF-THEN,
and so that node shapes follow the geometry code consistently.

AUDIT FINDINGS (what must be fixed):
{failure_text}

HOW TO REPAIR — RE-CLASSIFY, DO NOT INVENT:
- Keep the same node set (you may correct shapes to match the geometry code:
  star=actual goal/outcome, hexagon=science field, diamond=innovation,
  triangle=process/method/framework, octagon=rule/constraint/contradiction,
  ellipse=human/biological/social entity, rectangle=fact/finding/component).
- Re-examine EVERY edge against the report text. Most IF-THEN edges in such
  graphs are actually mis-encoded instances of proper relation types:
  * if the source is a narrower concept belonging to a broader concept -> BT
    (source narrower -> target broader);
  * if the source is a broader concept containing a narrower one -> NT
    (source broader -> target narrower);
  * if two concepts are closely associated in the text -> AS or RT;
  * if two labels denote the same concept -> EQ;
  * if a node is a concrete instance/example of a category -> IN;
  * if the report says an innovation is composed of / built from components
    -> Composition (essential) or Aggregation (independent components);
  * if a subsystem is embedded/contained in a system -> Containment;
  * if an innovation requires/uses a tool, resource or method -> Dependency;
  * if an innovation implements a methodology or specification -> Realization;
  * if a concept is a broad category of another -> Generalization;
  * if it is a special case/subtype -> Specialization;
  * if two requirements/mechanisms are explicitly incompatible -> Conflict;
  * if an intervention genuinely counteracts/regulates a state in a closed
    loop -> NEG-FEEDBACK;
  * only genuine cause/enabler -> effect relations remain IF-THEN;
  * real joint conditions -> AND; real alternatives -> OR; genuine exclusions
    -> XOR; genuine logical negation -> NOT.
- Do NOT invent facts that are absent from the report. If you cannot ground a
  relation in the report text, do not add it.
- Keep at most ONE edge between any pair of nodes.
- Fix the three most common systemic defects when present:
  (a) [Innovation] --"is a type of"--> [Science Field] is WRONG: re-encode as
      Dependency with label "grounded in" / "applies principles from";
      taxonomy (Specialization, "is a type of") only between concepts of the
      same kind (e.g. Allostatic Overload -> Physiological Exhaustion);
  (b) goal/outcome stars must be wired back into the system core through a
      closed NEG-FEEDBACK loop (restore -> stabilize -> feed back into the
      innovation or the measured state) when the report supports it;
  (c) innovations/methods described as operating together must have a lateral
      RT/AS edge labelled "works with" / "coordinates with".
- Every edge "label" must be a short human-readable verb phrase (never a bare
  code like "IN" or "BT").
- Keep evidence = explicit | inferred | hypothesis | future-test where known.
- Respect the direction conventions: BT source narrower -> target broader;
  NT source broader -> target narrower; IF-THEN source cause -> target effect.
- Keep the graph connected: every node must appear in at least one edge.
- Maximum 30 nodes and 45 edges.

OUTPUT FORMAT: output ONLY the corrected JSON object (no markdown, no
explanations), with exactly this structure:
{{
  "system_metrics": {{"f_pf": 0.70, "f_sf": 0.40, "f_pr": 0.30}},
  "nodes": [
    {{"id": "n1", "label": "Example", "shape": "diamond", "color": "#fd7e14",
      "description": "Short semantic description"}}
  ],
  "edges": [
    {{"source": "n1", "target": "n2", "rel_type": "Dependency", "label": "depends on", "evidence": "explicit"}}
  ]
}}
"""


# =============================================================================
# 3.3 [NOVO] CRIME & STRESS THEMATIC EXTENSION (samo dodaja; nič ne odstrani)
# =============================================================================
KNOWLEDGE_BASE["Science fields"].update(EXTRA_SCIENCE_FIELDS)
HUMAN_THINKING_METAMODEL["nodes"].update(CRIME_STRESS_METAMODEL_NODES)

# =============================================================================
# 4. KONČNI POPRAVLJEN SIDEBAR (Z SAMBANOVO IN UNIKATNIMI KLJUČI)
# =============================================================================
with st.sidebar:
    # 1. Original 3D Relief Logo
    st.markdown(f'<div class="sidebar-logo-container"><img src="data:image/svg+xml;base64,{get_svg_base64(SVG_3D_RELIEF)}" width="220"></div>', unsafe_allow_html=True)

    # 2. Date Badge
    st.markdown(f'<div class="date-badge">{SYSTEM_DATE.upper()}</div>', unsafe_allow_html=True)

    st.header("⚙️ SYSTEM CONTROL")

    # 3. GOOGLE GEMINI SYSTEM CONTROL
    st.header("⚙️ GOOGLE GEMINI SYSTEM CONTROL")
    google_api_key = st.text_input(
        "Google Gemini API Key:",
        type="password",
        key="side_google_gemini_v2026",
        help="Google AI Studio / Gemini API key."
    )

    # Google-only language-model catalog.  The list intentionally contains
    # current Gemini 3.x models plus the established Gemini 2.5 family and
    # Google's Gemma instruction-tuned models. No third-party provider is used.
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
    # [KLJUČNI POPRAVEK] Thinking level: "low" je povzročal plitve grafe in
    # šibka poročila. Privzeto "High" vrne kakovost, kakršno je imela starejša
    # različica (ocene 9,6–9,8 po petih merilih).
    thinking_level = st.selectbox(
        "🧠 Gemini 3.x Thinking Level:",
        ["High", "Medium", "Low", "Default (API)"],
        index=0,
        help="Stopnja notranjega razmišljanja za Gemini 3.x modele. 'Low' povzroči "
             "plitke povezave in revnejše grafe; 'High' daje najboljše rezultate.",
        key="side_thinking_level_v2026"
    )
    p1_model_label = st.selectbox(
        "Phase 1 Model (IMA Structure):",
        list(GOOGLE_MODELS.keys()), index=4,
        help="Recommended default: Gemini 3.5 Flash-Lite for efficient IMA synthesis."
    )
    p1_model = GOOGLE_MODELS[p1_model_label]
    p2_model_label = st.selectbox(
        "Phase 2 Model (MA Innovation):",
        list(GOOGLE_MODELS.keys()), index=5,
        help="Recommended default: Gemini 3.1 Flash-Lite; choose Gemini 3.7/3.8 for stronger innovation."
    )
    p2_model = GOOGLE_MODELS[p2_model_label]

    st.divider()

    # --- IZBIRA PERSPEKTIVE GRAFA (začetni pogled; v grafu samem je možno preklapljati) ---
    st.subheader("🎨 GRAPH PERSPECTIVE")
    graph_perspective = st.selectbox(
        "Initial Graph View:",
        options=["organic", "hierarchical", "circular"],
        index=0,
        format_func=lambda x: x.capitalize() + " View",
        help="Začetni pogled enega samega grafa. Med pogledi (Organic / Hierarchical / Circular) lahko preklapljate neposredno v grafu.",
        key="side_graph_layout_v2026"
    )

    graph_node_count = st.slider(
        "🔢 Number of Graph Nodes:",
        min_value=10,
        max_value=80,
        value=50,
        step=1,
        help="Set the maximum number of nodes displayed in the semantic graph."
    )

    # [NOVO] Stikalo za samodejni repair grafa, če raznolikost ni izpolnjena
    graph_auto_repair = st.toggle(
        "🛠️ Auto-repair graph diversity:",
        value=False,
        help="DIAGNOSTIKA: raznolikost relacij se vedno preveri in prikaže v "
             "expanderju 'Graph Diversity Audit'. Če vklopite to stikalo, bo "
             "sistem ob neizpolnjenih zahtevah zagnal en dodaten Gemini klic, ki "
             "prekodira relacije. Privzeto IZKLOPJENO: pri visokem thinking "
             "level Gemini sam proizvede raznolike povezave, repair pa lahko "
             "graf semantično osiromaši.",
        key="side_graph_auto_repair_v2026"
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
        st.markdown(", ".join(HIERARCHOLOGY_ONTOLOGY["hierarchography_tools"]))

    with st.expander("🏗️ Structural Model Context", expanded=False):
        for m, d in KNOWLEDGE_BASE["Structural models"].items(): 
            st.markdown(f"**{m}**: {d}")

    # --- [NOVO] Crime & Stress Prevention Ontology (expander) ---
    render_crime_stress_sidebar(st)

# =============================================================================
# 3.9 REPORT EXPORT HELPERS
# =============================================================================
def _report_plain_text(markdown_text):
    """Create readable plain text from the generated Markdown/HTML report."""
    cleaned = re.sub(r'<[^>]+>', '', markdown_text or '')
    cleaned = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', cleaned)
    cleaned = re.sub(r'[#*_`]', '', cleaned)
    return html.unescape(cleaned)

def build_html_report(report_text, graph_elements, perspective):
    """Build a self-contained HTML report with ONE interactive Cytoscape graph (3 switchable views)."""
    graph_json = json.dumps(graph_elements, ensure_ascii=False)
    report_html = report_text or ""
    initial_view = perspective if perspective in GRAPH_VIEWS else "organic"
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>SIS Universal Knowledge Synthesizer Report</title>
<style>
body{{font-family:Arial,Helvetica,sans-serif;margin:40px;color:#1d3557;line-height:1.6}}
.report{{max-width:1200px;margin:auto}}
.graph{{width:100%;height:850px;border:1px solid #ddd;border-radius:16px;margin-top:10px}}
.viewbar{{display:flex;gap:8px;margin-top:20px}}
.viewbar button{{padding:8px 14px;background:#6366f1;color:#fff;border:none;border-radius:7px;cursor:pointer;font-weight:800}}
h1,h2,h3{{color:#1d3557}}
</style></head><body><div class="report">
<h1>SIS Universal Knowledge Synthesizer Report</h1>
<div>{report_html}</div>
<h2>Hybrid Semantic System Map</h2>
<div class="viewbar">
  <button id="v_organic">🌿 Organic view</button>
  <button id="v_hierarchical">🌲 Hierarchical view</button>
  <button id="v_circular">⭕ Circular view</button>
</div>
<div id="cy" class="graph"></div>
</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.26.0/cytoscape.min.js"></script>
<script>
const elements = {graph_json};
const layouts = {LAYOUTS_JS};
let currentView = '{initial_view}';
const cy = cytoscape({{
 container: document.getElementById('cy'),
 elements: elements,
 style: [
 {{selector:'node',style:{{'label':'data(label)','text-valign':'center','text-halign':'center','color':'#1d3557','background-color':'data(color)','width':'data(size)','height':'data(size)','shape':'data(shape)','font-size':'12px','font-weight':'bold','text-wrap':'wrap','text-max-width':'80px','border-width':3,'border-color':'#fff','text-outline-color':'#fff','text-outline-width':2}}}},
 {{selector:'edge',style:{{'width':2,'line-color':'data(color)','label':'data(label)','font-size':'9px','font-weight':'bold','color':'#2a9d8f','curve-style':'unbundled-bezier','target-arrow-color':'data(color)','target-arrow-shape':'vee','text-background-opacity':1,'text-background-color':'#fff','text-background-padding':'3px'}}}},
 {{selector:'edge[rel_type="Generalization"]',style:{{'target-arrow-shape':'triangle','target-arrow-fill':'hollow','width':3}}}},
 {{selector:'edge[rel_type="Realization"]',style:{{'line-style':'dashed','target-arrow-shape':'triangle','target-arrow-fill':'hollow'}}}},
 {{selector:'edge[rel_type="Composition"]',style:{{'source-arrow-shape':'diamond','source-arrow-fill':'filled','width':4}}}},
 {{selector:'edge[rel_type="Aggregation"]',style:{{'source-arrow-shape':'diamond','source-arrow-fill':'hollow','width':3}}}},
 {{selector:'edge[rel_type="Dependency"]',style:{{'line-style':'dashed','target-arrow-shape':'vee'}}}},
 {{selector:'edge[rel_type="Conflict"]',style:{{'width':6,'line-color':'#b91d1d'}}}},
 {{selector:'edge[rel_type="Specialization"]',style:{{'line-style':'dashed','target-arrow-shape':'triangle'}}}},
 {{selector:'edge[rel_type="Containment"]',style:{{'target-arrow-shape':'circle','width':4}}}},
 {{selector:'edge[rel_type="TT"]',style:{{'width':6}}}},
 {{selector:'edge[rel_type="BT"]',style:{{'width':4}}}},
 {{selector:'edge[rel_type="NT"]',style:{{'width':4}}}},
 {{selector:'edge[rel_type="EQ"]',style:{{'width':5}}}},
 {{selector:'edge[rel_type="AND"]',style:{{'width':5}}}},
 {{selector:'edge[rel_type="OR"]',style:{{'width':3,'line-style':'dashed'}}}},
 {{selector:'edge[rel_type="XOR"]',style:{{'width':4,'line-style':'double'}}}},
 {{selector:'edge[rel_type="NOT"]',style:{{'width':4,'line-style':'dashed'}}}},
 {{selector:'edge[rel_type="IF-THEN"]',style:{{'width':4}}}},
 {{selector:'edge[rel_type="NEG-FEEDBACK"]',style:{{'width':5,'line-color':'#6A4C93','target-arrow-color':'#6A4C93','target-arrow-shape':'tee','line-style':'dashed'}}}},
 {{selector:'edge[evidence="hypothesis"]',style:{{'line-style':'dotted','opacity':0.72}}}},
 {{selector:'edge[evidence="future-test"]',style:{{'line-style':'dotted','opacity':0.58}}}}
 ],
 layout: layouts[currentView]
}});
['organic','hierarchical','circular'].forEach(function(v){{
  document.getElementById('v_'+v).addEventListener('click', function(){{
    currentView = v;
    cy.layout(layouts[v]).run();
  }});
}});
</script></body></html>"""

# --- MAIN PAGE CONTENT ---
st.markdown('<h1 class="main-header-gradient">🧱 SIS Universal Knowledge Synthesizer</h1>', unsafe_allow_html=True)
st.markdown(f"**Sequential Multi-Engine Pipeline** | Current Operating Date: **{SYSTEM_DATE}**")

if st.session_state.show_user_guide:
    st.info(f"""
    **Sequential Synergy Pipeline Workflow (Updated Feb 24, 2026):**
    1. **Key Input**: Enter your Google Gemini API key and select Google models for Phase 1 and Phase 2.
    2. **Research Foundation (Step 1)**: Google Gemini performs structural synthesis using Integrated Metamodel Architecture (IMA).
    3. **Innovation Prompt (Step 2)**: Google Gemini takes the Phase 1 foundation and generates useful innovative ideas using Mental Approaches (MA) logic.
    4. **Visualization**: One interactive graph maps structural facts against generative ideas; switch between Organic, Hierarchical and Circular view directly in the graph.
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
with r2c1: sel_paradigms = st.multiselect("4. Scientific Paradigms:", list(KNOWLEDGE_BASE["Scientific paradigms"].keys()), default=["Rationalism"])
with r2c2: sel_models = st.multiselect("5. Structural Models:", list(KNOWLEDGE_BASE["Structural models"].keys()), default=["Concepts"])
with r2c3: goal_context = st.selectbox("6. Strategic Project Goal:", ["Scientific Research", "Problem Solving", "Educational", "Policy Making"])

# --- METHODOLOGY & TOOLS UI (ACTIVATED BEFORE INNOVATION STRATEGY) ---
available_methods = sorted({
    method
    for science in sel_sciences
    for method in KNOWLEDGE_BASE["Science fields"].get(science, {}).get("methods", [])
})
available_tools = sorted({
    tool
    for science in sel_sciences
    for tool in KNOWLEDGE_BASE["Science fields"].get(science, {}).get("tools", [])
})

r3c1, r3c2 = st.columns(2)
with r3c1:
    sel_methods = st.multiselect(
        "7. Methodology:",
        available_methods,
        default=available_methods,
        help="Select the scientific methods relevant to the selected science fields."
    )
with r3c2:
    sel_tools = st.multiselect(
        "8. Tools:",
        available_tools,
        default=available_tools,
        help="Select the scientific tools relevant to the selected science fields."
    )

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

# --- [NOVO] CRIME & STRESS PREVENTION MODULE (samo izbirnik) ---
cs_mode = render_crime_stress_mode(st)
st.divider()

# DUAL INQUIRY INTERFACE
col_inq1, col_inq2, col_inq3 = st.columns([2, 2, 1])
with col_inq1:
    user_query = st.text_area("❓ STEP 1: Research Inquiry (for GOOGLE GEMINI):", placeholder="Fact-based Foundational Inquiry...", height=200)
with col_inq2:
    idea_query = st.text_area("💡 STEP 2: Innovation Prompt (for GOOGLE GEMINI):", placeholder="Targets for innovative idea production...", height=200)
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
# 5. SYNERGY EXECUTION ENGINE (GOOGLE GEMINI / GEMMA ONLY)
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
    # [KLJUČNI POPRAVEK] thinking_level ni več vsiljen kot "low".
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


if st.button("🚀 EXECUTE MULTI-DIMENSIONAL GOOGLE GEMINI PIPELINE", use_container_width=True, key="exec_pipeline_v2026"):
    if not google_api_key:
        st.error("❌ Google Gemini API key is required to proceed.")
    elif not user_query:
        st.warning("⚠️ Phase 1 Research Inquiry is required.")
    elif not selected_techniques:
        st.warning("⚠️ Please select at least one innovation technique for Phase 2.")
    else:
        try:
            # Clear any previous report so only the new one is shown.
            st.session_state.pop("report_data", None)

            ima_nodes_list = "\n".join(
                [f"   • {node.upper()}: {data['desc']}" for node, data in HUMAN_THINKING_METAMODEL["nodes"].items()]
            )
            hier_core = "\n".join(
                [f"   • {k}: {v}" for k, v in HIERARCHOLOGY_ONTOLOGY["core_definitions"].items()]
            )
            hier_levels = "\n".join(
                [f"   • {level}: {desc}" for level, desc in HIERARCHOLOGY_ONTOLOGY["hierarchical_levels"].items()]
            )
            hier_logic = (
                f"   • Internal (Inductive): {HIERARCHOLOGY_ONTOLOGY['operational_logic']['Internal Processes']}\n"
                f"   • External (Deductive): {HIERARCHOLOGY_ONTOLOGY['operational_logic']['External Functioning']}"
            )
            ma_definitions = "\n".join(
                [f"   • {ma}: {d['desc']}" for ma, d in MENTAL_APPROACHES_ONTOLOGY["nodes"].items()]
            )

            active_context = ""
            if "[ACTIVATE]" in user_query or ("[ACTIVATE]" in idea_query if idea_query else False):
                active_context = f"""
### MANDATORY SIS METAMODEL ACTIVATION
Analyze the inquiry through the following structures, but activate only elements
that are semantically relevant. Do not manufacture relationships merely to use
the ontology.

IMA NODES:
{ima_nodes_list}

HIERARCHOLOGY:
{hier_core}

HIERARCHICAL LEVELS:
{hier_levels}

OPERATIONAL LOGIC:
{hier_logic}

MENTAL APPROACHES:
{ma_definitions}

INTERFACE PARAMETERS:
- Target Science Fields: {', '.join(sel_sciences)}
- Scientific Paradigms: {', '.join(sel_paradigms)}
- Structural Models: {', '.join(sel_models)}
- Methodology: {', '.join(sel_methods)}
- Tools: {', '.join(sel_tools)}
- Innovation Frameworks: {', '.join(selected_techniques)}
- Expertise Level: {expertise}
- Strategic Goal: {goal_context}
"""

            # --- [NOVO] Ali je aktiven Crime & Stress Prevention modul? ---
            cs_active = crime_stress_should_activate(cs_mode, user_query, idea_query)

            with st.spinner('🔍 Accessing ORCID research background...'):
                biblio_data = fetch_author_bibliographies(target_authors) if target_authors else ""

            file_context_str = f"\n\n[FILE CONTEXT]:\n{file_content}" if file_content else ""
            biblio_context = f"\n\n[AUTHOR RESEARCH BACKGROUND]:\n{biblio_data}" if biblio_data else ""
            full_ai_input = f"{active_context}\nUSER RESEARCH INQUIRY:\n{user_query}{file_context_str}{biblio_context}"

            google_client = genai.Client(api_key=google_api_key)

            # ---------------- PHASE 1: IMA ----------------
            phase1_system_prompt = f"""
You are the SIS Lead Hierarchologist and Knowledge Architect.

Perform a rigorous Phase 1 IMA knowledge synthesis. Do not solve the innovation
problem yet. Build the factual and conceptual foundation for Phase 2.

Requirements:
1. Identify the actual problem, goal, relevant actors/concepts and constraints.
2. Map only relevant IMA elements; do not force all ontology nodes.
3. Distinguish Macro, Meso and Micro levels where the source supports them.
4. Identify important concepts, relations, dependencies and contradictions.
5. Distinguish source-supported information from interpretation.
6. Do not invent named theories, concepts, mechanisms or terminology absent from
   the supplied material unless clearly marked as interpretation.
7. Do not introduce 'Scientific Cage' unless the supplied material supports it.
8. Produce a structured foundation, not generic commentary.
9. For each key concept, explicitly note which selected science field(s) it belongs
   to or bridges, so Phase 2 can build genuine interdisciplinary connections.
10. Write in clear, well-labeled sections with short paragraphs (max 4-5 sentences)
    and bullet points where useful. Avoid dense, unreadable academic blocks.
11. Explicitly identify at least 2-3 cross-disciplinary tension points, contradictions
    or knowledge gaps between the selected science fields — these become the raw
    material for innovation in Phase 2.
12. DESCRIPTIVE REPORTING STYLE: write as a readable explanatory report, not as a
    list of fragments. Begin section 1 with a 2-3 sentence plain-language summary
    ("In brief: ...") of the problem and the goal. In every section, introduce the
    content with one connecting sentence, explain WHY each important point matters
    (not only WHAT it is), and use **bold** for the key concepts when first named.
    Bullets must be full, self-explanatory sentences.

Selected sciences: {', '.join(sel_sciences)}
Selected paradigms: {', '.join(sel_paradigms)}
Selected structural models: {', '.join(sel_models)}
Selected methodology: {', '.join(sel_methods)}
Selected tools: {', '.join(sel_tools)}
Expertise: {expertise}
Strategic goal: {goal_context}

Return, using these as literal markdown section headers, in this order:
### 1. IMA Problem Definition
### 2. Relevant Knowledge Structure
### 3. Macro–Meso–Micro Analysis
### 4. Cross-Disciplinary Bridge Points
(explicit tensions, gaps or complementarities between the selected science fields)
### 5. Constraints and Contradictions
### 6. Evidence / Interpretation Boundary
### 7. Key Findings for Phase 2

Do not generate innovations in Phase 1.
"""
            # --- [NOVO] Crime & Stress tematska okrepitev Faze 1 (prepended) ---
            if cs_active:
                phase1_system_prompt = build_phase1_addendum() + phase1_system_prompt

            with st.spinner(f'PHASE 1: IMA synthesis with {p1_model_label}...'):
                phase1_synthesis = google_generate(
                    google_client, p1_model, phase1_system_prompt,
                    full_ai_input, temperature=0.40, thinking_level=thinking_level
                )
                st.session_state.phase1_synthesis = phase1_synthesis

            # ---------------- PHASE 2: MA ----------------
            ma_list_for_ai = ", ".join(MENTAL_APPROACHES_ONTOLOGY["nodes"].keys())
            phase2_system_prompt = f"""
You are the SIS Lead Strategic Innovation Architect and Hierarchographist.

Transform the Phase 1 IMA foundation into traceable, PRACTICAL innovations using
Mental Approaches (MA). Do NOT produce generic brainstorming.

CORE TRANSFORMATION CHAIN:
IMA finding -> limitation/contradiction -> selected MA -> transformation
operation -> changed configuration -> innovation -> expected effect.

Use only genuinely useful MAs. You are NOT required to use all 20.

AVAILABLE MENTAL APPROACHES:
{ma_definitions}

AVAILABLE MA NAMES:
{ma_list_for_ai}

SELECTED IDEATION FRAMEWORKS:
{', '.join(selected_techniques)}

SELECTED METHODOLOGY:
{', '.join(sel_methods)}

SELECTED TOOLS:
{', '.join(sel_tools)}

DESCRIPTIVE REPORTING STYLE (the written report is the ONLY place where the
innovations are described, so it must be complete, explanatory and readable on
its own — there is no separate innovation catalog after the report):
- Write in full, connected sentences. Explain WHY each step of the chain follows
  from the previous one, not only WHAT it is. Use **bold** for key concepts when
  first named. Avoid fragments and keyword lists.

Start the report with a short "### Executive Synthesis" section (max 6 sentences)
naming the single most important interdisciplinary insight connecting the
selected science fields — this is the thread the rest of the report follows.

For each of 3–4 innovations, use this exact literal markdown structure so the
report stays clear and scannable:

#### Innovation N: <short, concrete, punchy name>
- **In plain words:** 3–5 sentences telling, in everyday language, what this
  innovation is, what problem it addresses, how it would work and why it is
  different from existing approaches (a short narrative a non-specialist could
  follow).
- **IMA finding:** ...
- **Limitation/contradiction:** ...
- **Mental Approach used:** ...
- **Transformation operation:** ...
- **New configuration:** ...
- **The innovation:** one clear, concrete, implementable idea — state what would
  actually be built, tested, measured, or changed. Avoid vague generalities.
- **Cross-disciplinary bridge:** name the ≥2 distinct science fields this
  innovation connects and what each field specifically contributes.
- **Practical next step:** one concrete, feasible first action a real team could
  take within a month (pilot, prototype, experiment, dataset, or policy step).
- **Safeguards (if the innovation touches personal/biometric/health/behavioral
  data):** specify a concrete Privacy-by-Design architecture, not a vague
  mention — e.g. on-device aggregation only, differential privacy (ε-noise
  addition) before any data leaves the device, so raw individual telemetry is
  never stored or transmitted, only noised aggregates. Name the actual
  mechanism, not just the word "privacy". Omit this bullet only if truly not
  applicable.
- **Expected effect:** ...

After the last innovation, and BEFORE the semantic graph JSON, write a closing
section "### Integrated Conclusion and Roadmap" containing three short labeled
paragraphs: **How the innovations fit together** (how they reinforce or
complement one another and which Phase 1 contradictions they jointly resolve),
**Suggested order of implementation** (what to do first, second, third and why),
and **Open questions and risks** (what remains uncertain and what must be
validated empirically).

Prioritize innovations that combine at least two of the selected science fields in
a non-obvious way over single-field extensions. Reject any innovation that is just
a restatement of a Phase 1 finding without a genuine transformation step.

Avoid unsupported claims and invented terminology.
Build a sparse semantic graph. Prefer meaningful relations over graph density.
At least 2 edges must connect nodes that belong to different science-field
clusters, so the graph visually demonstrates interdisciplinary integration.

GRAPH GROUNDING — THE GRAPH IS A DIAGRAM OF THE REPORT, NOT A SEPARATE TASK:
- Every node label MUST correspond to a concept, finding, science field, MA,
  contradiction, or innovation that you explicitly named in the Phase 1 or
  Phase 2 text above. Do not invent nodes that do not appear in the written
  report — if it is not in the text, it does not belong in the graph.
- Conversely, the most important items you wrote about (each innovation, each
  cross-disciplinary bridge point, each science field actually used, each MA
  actually used) MUST appear as a node. A graph that omits the innovations or
  the bridge points you just described is incomplete and INVALID.
- Every edge must reflect a relationship that is stated or clearly implied in
  the text (e.g. "Innovation 2 resolves the contradiction from finding X" ->
  an edge between those two nodes).

GEOMETRY IS A STRICT SEMANTIC CODE, NOT DECORATION — apply consistently to
every node of that category, with no exceptions:
- star = the actual, concrete problem/outcome goal named in the user's
  inquiry (e.g. "reduce crime", "reduce stress") — NEVER a methodology,
  framework, or theoretical approach (Hierarchology, IMA, MA, Six Thinking
  Hats, etc. are NOT goals; they go under triangle, see below). If the
  original inquiry names a target problem, it MUST have its own star node,
  and every innovation that addresses it must connect to that star.
- hexagon = Science Field (Physics, Sociology, Astronomy, etc.)
- diamond = Innovation (Phase 2 output)
- triangle = Process / Method / Methodology / Framework / Transformation
  operation (this includes Hierarchology, IMA, MA, and named ideation
  techniques — they are tools of analysis, not the goal itself)
- octagon = Rule / Constraint / Contradiction
- ellipse = Human, biological or social entity/actor
- rectangle = Fact, finding, or structural/data component (default only when
  nothing else fits)
Two nodes describing the same kind of thing must always share the same shape.
Never assign shapes arbitrarily for visual variety, and never let a method
node steal the star shape meant for the actual target problem.

NO REDUNDANT PARALLEL EDGES:
- Between any two given nodes, draw exactly ONE edge — the single relation
  type that best captures the relationship. If both a causal link (IF-THEN)
  and a thesaurus link (RT/AS) seem to apply to the same pair, pick the more
  informative one and drop the other. Two parallel edges between the same
  node pair (e.g. one IF-THEN and one RT) is a defect, not richness.

ISO 25964 DIRECTION CONVENTION FOR BT/NT (this is commonly drawn backwards —
follow it exactly):
- BT (Broader Term): source is the NARROWER/more specific concept, target is
  the BROADER concept it belongs to. Read as "source's Broader Term is target".
- NT (Narrower Term): source is the BROADER concept, target is the NARROWER,
  more specific concept it contains. Read as "source's Narrower Term is target".
- Example: [Sociology] --NT--> [Informal Power Structures] is CORRECT
  (Sociology is broad; Informal Power Structures is its narrower concept).
  [Sociology] --BT--> [Informal Power Structures] would be WRONG (backwards).

RELATION TYPES — build a genuinely heterogeneous semantic graph from four families.
Pick the family that actually fits the semantic meaning of each edge; never
default to UML/structural types just because they are familiar.

A) THESAURUS FAMILY (ISO 25964 style — use for conceptual/terminological links):
   - TT, BT, NT, EQ, RT, AS, IN

B) STRUCTURAL/UML FAMILY (use for architectural/action/compositional links):
   Generalization, Specialization, Containment, Realization, Composition,
   Aggregation, Dependency, Conflict

UML EXTRACTION PROTOCOL: inspect every important concept pair before choosing
RT/AS/IF-THEN. UML represents a different semantic dimension. Use Composition
for essential whole-part lifecycle structure; Aggregation for independently
existing components collected into a whole; Containment for inclusion/embedded
subsystems; Dependency when one element requires or uses another; Realization
when an implementation realizes a specification or method; Generalization for
a broad category/superclass; Specialization for a concrete subtype; Conflict
for explicitly incompatible requirements, mechanisms or constraints.
For Phase 2 innovations actively inspect these supported patterns:
innovation -> Dependency -> resource/tool/method; innovation -> Composition or
Aggregation -> component; innovation -> Realization -> methodology/specification;
innovation -> Containment -> subsystem; constraint -> Conflict -> innovation.
This is an extraction requirement, not a numerical quota: when supported by the
report, encode the UML relation rather than weakening it to RT/AS/IF-THEN. Never
invent a UML relation merely to increase diversity.

RELATION-SEMANTIC CORRECTNESS RULES (these specific errors cost the most
quality points — audit every edge against them):
- INNOVATION -> SCIENCE FIELD: an innovation is NOT a type of a discipline.
  Never encode [Innovation] --Generalization/Specialization/"is a type of"-->
  [Science Field]. The correct relation is Dependency with a human-readable
  label such as "grounded in" or "applies principles from" (source = the
  innovation, target = the field it draws on). Example:
  [NeuroPoverty Index] --Dependency, "grounded in"--> [Neuroscience].
- TAXONOMY (Generalization/Specialization, "is a type of") is reserved for
  genuine subtype-of relationships between CONCEPTS of the same kind, e.g.
  [Allostatic Overload] --Specialization, "is a type of"--> [Physiological
  Exhaustion]. If the two nodes are of different categories (innovation vs.
  field, method vs. fact), a taxonomy edge is wrong.
- CONCEPT -> DISCIPLINE links use IN ("is an instance of") or BT/NT only when
  the text genuinely places the concept inside the discipline's scope.

FEEDBACK-LOOP CLOSURE (systemic rigor — the graph must be a SYSTEM, not a
tree): goal/outcome star nodes must be wired BACK into the core of the system,
not left as terminal decorations. Look for the closed causal-regulatory cycle
described or implied in the report and encode it explicitly, e.g.:
[Innovation] --IF-THEN, "restores"--> [Executive Function] --IF-THEN,
"stabilizes"--> [Regulatory State] --NEG-FEEDBACK, "feeds back into"-->
[Innovation / Goal Star]. Aim for at least one genuine NEG-FEEDBACK cycle per
major outcome star when the report supports it (roughly a quarter of the
innovation-related edges should participate in closed loops). Do not fabricate
loops the report does not support.

LATERAL INTEGRATION ("works with"): when two innovations, methods or
components are described as operating TOGETHER (complementing, coordinating,
being combined in a pipeline), connect them laterally with an RT/AS edge
labelled "works with", "combined with" or "coordinates with" — do not leave
them connected only through a shared parent. Every innovation named in the
report should be semantically reachable from every other innovation through
at most one intermediary node.

C) OPERATIONAL LOGIC FAMILY (use for reasoning, conditions and causal structure):
   AND, OR, XOR, NOT, IF-THEN

D) CONTROL/FEEDBACK FAMILY:
   NEG-FEEDBACK = a genuine negative regulatory feedback relation that
   counteracts or attenuates the state that initiated the intervention.
   NEG-FEEDBACK is NOT logical NOT. Use it only when a closed regulatory
   mechanism is actually stated or clearly implied by the report.

SEMANTIC DIVERSITY TARGET (NOT A FABRICATION RULE):
Aim approximately for 25–35% Thesaurus relations and 25–35% Operational Logic
relations when the report genuinely supports them. The remaining relations may
be UML/Structural and Control/Feedback. These percentages are diagnostic
targets, NOT quotas. NEVER invent a relation merely to satisfy a percentage.
Scientific semantic correctness has priority over numerical diversity. The most
common defect is collapsing taxonomic links (BT/NT), component structure
(Composition/Aggregation), tool usage (Dependency) and conceptual association
(AS/RT) into IF-THEN — encode each relation with its PROPER type, and the
diversity follows naturally from a well-reasoned graph.

QUALITY BAR — SELF-EVALUATION BEFORE OUTPUT (do this silently first):
The final deliverable is scored 0.00–10.00 on five criteria:
(1) Conceptual novelty of the ideas,
(2) System architecture quality of the report AND the graph,
(3) Interdisciplinary integration of the selected science fields,
(4) Practical applicability of the ideas,
(5) Clarity and coherence of the report.
Internally draft, critique against these five criteria and improve the report
and graph until EVERY criterion would earn at least 9.5/10. Weak, generic or
fragmented output is unacceptable. Then, at the very end of the written report
(BEFORE ### SEMANTIC_GRAPH_JSON), add a short section
"### Quality Self-Assessment" listing each criterion with your 0.00–10.00
rating and one sentence of justification. Do not inflate the ratings: if a
criterion genuinely falls below 9.5, state honestly what is missing.

LOGICAL GATES:
When AND/OR/XOR/NOT represents a genuine multi-condition proposition, you may
create a dedicated octagon node labelled AND, OR, XOR or NOT as a logical gate.
Incoming edges represent operands/conditions and the outgoing IF-THEN edge
represents the consequence. Do not use an AND edge merely as decoration.

MEASUREMENT BRIDGE:
When the supplied material supports a physical, biological, environmental or
temporal parameter, represent it explicitly where useful: parameter name, symbol,
unit and measurement meaning. Examples include wavelength λ (nm), sound level
L_Aeq (dB), temperature T (°C), HRV RMSSD (ms), heart rate HR (bpm), or delay τ
(ms/s). NEVER invent numerical values. If a value is not supplied, mark the
parameter as a proposed future measurement.

EPISTEMIC STATUS:
Distinguish observed/reported fact, interpretation, hypothesis and future test.
Use edge field evidence = explicit | inferred | hypothesis | future-test.

CAUSAL DIRECTION DISCIPLINE (this is where most graphs break):
- For every IF-THEN edge: source = the cause/enabler/condition, target = the
  resulting effect/outcome. Read it aloud as "If <source> then <target>" — if
  that sentence does not make literal sense, the arrow is backwards. Example:
  [Computer Science] --IF-THEN--> [Innovation: Semantic Mediator] is correct
  (a field enables an innovation); the reverse is wrong.
- The same left-to-right cause→effect discipline applies to Dependency,
  Realization and AND/OR edges: source is the precondition, target is what
  depends on or results from it.

NEGATIVE-FEEDBACK CLOSURE:
When an innovation is described as reducing, buffering, attenuating, restoring or
otherwise counteracting a stress/problem state, look for an actual closed-loop
mechanism. If supported, represent the intervention → NEG-FEEDBACK → regulated
state cycle. Do not manufacture loops for visual richness.

PREDICATE LOGIC DISCIPLINE:
- IF-THEN: source = cause/enabler/condition; target = effect/outcome.
- AND/OR/XOR/NOT: use as genuine logical operators; if the proposition has more
  than two operands, prefer an explicit octagon gate node.
- NOT means logical negation/exclusion, never merely 'reduces', 'blocks' or
  'mitigates'. Use IF-THEN or NEG-FEEDBACK for those meanings when justified.

TARGET-OUTCOME TRACEABILITY (do not lose the original problem):
- Any concrete negative condition, risk, symptom, or problem named in the
  Phase 1 report (e.g. a named stressor, harm, inefficiency, or risk) must
  reappear in the graph as its own outcome node — do not let it silently
  disappear once you move to innovations.
- Connect each such outcome node to the specific innovation(s) that address it
  with a directional edge whose human-readable label states the effect
  precisely: "mitigates", "prevents", "resolves", "reduces" — not a generic
  "related to".

HUMAN-READABLE EDGE LABELS (rel_type is for styling only, label is for humans):
- "rel_type" must stay one of the codes listed above (for consistent visual
  styling). "label" must independently be a short, precise, human-readable
  verb phrase describing what the edge actually does — e.g. "operationalizes",
  "constrained by", "mitigates", "enables", "contradicts". NEVER leave "label"
  as a bare code like "IN", "BT", or "AND" — that tells a human nothing.

SENSITIVE-DOMAIN SAFEGUARDS:
- If an innovation involves personal, biometric, health, behavioral, or other
  sensitive data, its "innovation" and "practical next step" text must name a
  concrete technical or ethical safeguard (e.g. on-device processing,
  anonymization, differential privacy, explicit consent) — do not leave privacy
  or safety implicit.

SELF-CHECK BEFORE YOU OUTPUT THE JSON (do this silently, then output only the
corrected result): confirm (1) every important report entity is present as a
node, (2) no node is invented beyond the report, (3) no node is isolated,
(4) the thesaurus/logic edge-ratio rule is satisfied, (5) shapes are used
consistently as the semantic code above — the star belongs to the actual named
problem/goal, never to a methodology, (6) every IF-THEN / Dependency arrow
points cause→effect and reads correctly aloud, (7) every named problem/outcome
from Phase 1 has a corresponding outcome node linked to the innovation that
addresses it, (8) every edge "label" is a human-readable phrase, never a bare
code, (9) no two nodes are connected by more than one parallel edge,
(10) every BT/NT edge follows the direction convention above (BT: source is
narrower → target is broader; NT: source is broader → target is narrower),
(11) NO innovation-to-science-field edge uses a taxonomy relation — they are
Dependency ("grounded in"), (12) each goal star closes back into the system
via at least one NEG-FEEDBACK loop where the report supports it, and (13)
cooperating innovations are linked laterally ("works with").

GRAPH LIMITS:
- Maximum 30 nodes.
- Maximum 45 edges.
- Every edge must connect existing node IDs.
- No artificial bridge edges.
- No duplicate or semantically redundant edges.
- MANDATORY CONNECTIVITY: every single node must appear in at least one edge —
  zero isolated/orphan nodes are allowed. Before finishing, mentally verify that
  the node set and edge set together form ONE connected graph (no separate
  disconnected islands). If a node would otherwise be isolated, connect it with
  the most semantically honest relation available (thesaurus RT/AS is usually
  the safe default for a loose but real connection).

GEOMETRY:
star=Goals, hexagon=Science Fields, diamond=Innovations,
triangle=Processes, octagon=Rules, ellipse=Human/Biological entities,
rectangle=Facts/Components.

The graph must represent the same reasoning as the report.

At the end output:
### SEMANTIC_GRAPH_JSON

Then valid JSON only:
{{
  "system_metrics": {{"f_pf": 0.70, "f_sf": 0.40, "f_pr": 0.30}},
  "nodes": [
    {{
      "id": "n1",
      "label": "Example",
      "shape": "diamond",
      "color": "#fd7e14",
      "description": "Short semantic description"
    }}
  ],
  "edges": [
    {{"source": "n1", "target": "n2", "rel_type": "IF-THEN", "label": "enables"}}
  ]
}}

Use standard JSON with double quotes. Escape internal quotes correctly.
Do not place explanatory text after the JSON object.
"""
            # --- [NOVO] Crime & Stress tematska okrepitev Faze 2 (prepended) ---
            if cs_active:
                phase2_system_prompt = build_phase2_addendum() + phase2_system_prompt

            with st.spinner(f'PHASE 2: MA innovation with {p2_model_label}...'):
                phase2_user_content = (
                    f"PHASE 1 IMA FOUNDATION:\n{phase1_synthesis}\n\n"
                    f"USER INNOVATION OBJECTIVE:\n{idea_query}{file_context_str}"
                )
                google_innovation = google_generate(
                    google_client, p2_model, phase2_system_prompt,
                    phase2_user_content, temperature=0.85, thinking_level=thinking_level
                )

            # --- 4. PROCESS RESULTS ---
            # Always initialize these containers before any conditional JSON parsing.
            g_data = {"nodes": [], "edges": [], "system_metrics": {}}
            nodes_to_link = []
            final_elements = []

            if "### SEMANTIC_GRAPH_JSON" in google_innovation:
                parts = google_innovation.split("### SEMANTIC_GRAPH_JSON", 1)
                innovation_text = parts[0]
                json_raw = parts[1]
            else:
                innovation_text = google_innovation
                json_raw = ""

            innovation_text = re.sub(r'```json|```', '', innovation_text)

            # Parse the model-generated semantic graph.
            parsed_g, parse_err = parse_graph_json(json_raw)
            if parsed_g is not None:
                g_data = parsed_g
            elif json_raw.strip():
                # Keep the textual report usable even if the model emitted
                # malformed JSON. The graph simply remains empty.
                st.warning(f"⚠️ Semantic graph JSON could not be parsed; report retained. ({parse_err})")

            # Validate graph structure defensively.
            if not isinstance(g_data.get("nodes"), list):
                g_data["nodes"] = []
            if not isinstance(g_data.get("edges"), list):
                g_data["edges"] = []

            # --- [NOVO] DIVERSITY AUDIT + SAMODEJNI REPAIR KLIC ---
            # Preveri obvezne kvote raznolikosti relacij in oblik. Če graf
            # ne izpolnjuje zahtev (npr. preveč IF-THEN, premalo tezaver/UML),
            # en dodaten Gemini klic prekodira isti graf s pravimi tipi relacij.
            diversity_ok, diversity_metrics, diversity_failures = check_graph_diversity(g_data)

            if not diversity_ok and g_data.get("nodes") and graph_auto_repair:
                with st.spinner("🛠️ GRAPH DIVERSITY AUDIT: re-encoding relations (thesaurus / UML / logic)..."):
                    repair_system_prompt = build_graph_repair_system_prompt(diversity_failures)
                    repair_user_content = (
                        f"PHASE 2 REPORT (grounding for every relation — do not go beyond it):\n"
                        f"{innovation_text}\n\n"
                        f"CURRENT GRAPH JSON (same node set; re-encode relation types and shapes):\n"
                        f"{json.dumps(g_data, ensure_ascii=False)}"
                    )
                    try:
                        repair_output = google_generate(
                            google_client, p2_model, repair_system_prompt,
                            repair_user_content, temperature=0.40, thinking_level=thinking_level
                        )
                        repaired_g, repair_err = parse_graph_json(repair_output)
                        if repaired_g is not None and isinstance(repaired_g.get("nodes"), list):
                            # Preveri, da je popravljen graf res boljši.
                            ok2, metrics2, failures2 = check_graph_diversity(repaired_g)
                            if ok2 or len(failures2) < len(diversity_failures):
                                g_data = repaired_g
                                diversity_ok, diversity_metrics, diversity_failures = ok2, metrics2, failures2
                                st.success("✅ Graph diversity repair applied (proper relation types re-encoded).")
                            else:
                                st.warning("⚠️ Diversity repair did not improve the graph; original graph retained.")
                        else:
                            st.warning(f"⚠️ Diversity repair output could not be parsed; original graph retained. ({repair_err})")
                    except Exception as repair_exc:
                        st.warning(f"⚠️ Diversity repair call failed; original graph retained. ({repair_exc})")
            elif not diversity_ok and g_data.get("nodes"):
                st.warning(
                    "⚠️ Graph diversity requirements are not met (see Graph Semantic Validation), "
                    "and auto-repair is disabled in the sidebar."
                )

            full_report = (
                f"## 📚 Phase 1: IMA Structural Foundation (Google {p1_model_label})\n\n"
                f"{phase1_synthesis}\n\n---\n"
                f"## 💡 Phase 2: MA Strategic Innovations (Google {p2_model_label})\n\n"
                f"{innovation_text}"
            )

            # --- SEMANTIC LINTER + GRAPH MATERIALIZATION ---
            # The linter sits between Gemini and Cytoscape. It validates the
            # graph, normalizes relation types and records epistemic status.
            # It NEVER invents bridge edges merely to improve visual density.
            max_graph_nodes = max(10, int(graph_node_count))
            max_graph_edges = max(45, min(120, max_graph_nodes * 2))
            g_data, graph_lint = lint_semantic_graph(
                g_data,
                max_nodes=max_graph_nodes,
                max_edges=max_graph_edges
            )

            nodes_to_link = []
            final_elements = []

            # --- MATERIALIZE NODES ---
            for n in g_data.get("nodes", []):
                lbl = n.get("label", "Node")
                nid = str(n.get("id", f"n{len(nodes_to_link)+1}"))
                n_color = n.get("color", "#DDEBF7")
                n_shape = n.get("shape", "rectangle")

                if n_shape == 'star': n_size = 125
                elif n_shape == 'diamond': n_size = 110
                elif n_shape == 'octagon': n_size = 105
                elif n_shape == 'hexagon': n_size = 100
                elif n_shape == 'triangle': n_size = 95
                elif n_shape == 'ellipse': n_size = 90
                else: n_size = 85

                nodes_to_link.append({"id": nid, "label": lbl})
                final_elements.append({
                    "data": {
                        "id": nid,
                        "label": lbl,
                        "color": n_color,
                        "shape": n_shape,
                        "size": n_size,
                        "description": n.get("description", "Detail breakdown in report.")
                    }
                })

            # --- MATERIALIZE EDGES ---
            edge_colors = {
                "Conflict": "#B91D1D",
                "Specialization": "#8E44AD",
                "Containment": "#1D3557",
                "Generalization": "#8E44AD",
                "Realization": "#E63946",
                "Composition": "#1D3557",
                "Aggregation": "#457B9D",
                "Dependency": "#6C757D",
                "BT": "#1D3557", "NT": "#1D3557", "TT": "#1D3557",
                "IN": "#0077B6", "AS": "#7B2CB1", "EQ": "#F1C40F",
                "RT": "#2A9D8F",
                "AND": "#00A651", "OR": "#00BFFF",
                "XOR": "#FF8C00", "NOT": "#D00000",
                "IF-THEN": "#C9A227",
                "NEG-FEEDBACK": "#6A4C93",
            }

            for e in g_data.get("edges", []):
                rel = normalize_relation_type(e.get("rel_type", "RT"))
                final_elements.append({
                    "data": {
                        "id": e.get("id", f"e{len(final_elements)}"),
                        "source": e.get("source"),
                        "target": e.get("target"),
                        "rel_type": rel,
                        "family": RELATION_FAMILY.get(rel, "Unknown"),
                        "evidence": e.get("evidence", "inferred"),
                        "color": edge_colors.get(rel, "#ADB5BD"),
                        "weight": e.get("weight", 1.0),
                        "label": e.get("label") or RELATION_LABEL_DEFAULTS.get(rel, rel)
                    }
                })

            # --- RELATION-FAMILY DIAGNOSTIC ---
            edge_rel_types = [
                el["data"]["rel_type"]
                for el in final_elements
                if "source" in el.get("data", {})
            ]
            n_thesaurus = sum(1 for r in edge_rel_types if r in THESAURUS_TYPES)
            n_logic = sum(1 for r in edge_rel_types if r in LOGIC_TYPES)
            n_structural = sum(1 for r in edge_rel_types if r in STRUCTURAL_TYPES)
            n_feedback = sum(1 for r in edge_rel_types if r in CONTROL_TYPES)

            rel_caption = ""
            rel_warning = False
            if edge_rel_types:
                total_edges = len(edge_rel_types)
                rel_caption = (
                    f"🔗 Relation mix ({total_edges} edges) — "
                    f"Thesaurus: {n_thesaurus} ({n_thesaurus/total_edges:.0%}) | "
                    f"UML: {n_structural} ({n_structural/total_edges:.0%}) | "
                    f"Logic: {n_logic} ({n_logic/total_edges:.0%}) | "
                    f"Feedback: {n_feedback} ({n_feedback/total_edges:.0%})"
                )
                # Warning is diagnostic, never a reason to fabricate edges.
                rel_warning = (
                    n_thesaurus / total_edges < 0.25 or
                    n_logic / total_edges < 0.25
                )

            lint_warning_text = "\n".join(
                f"• {w}" for w in graph_lint.get("warnings", [])[:12]
            )

            # --- GLOBAL SEMANTIC HIGHLIGHTER (Regex Highlighter) ---
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

            # --- REPORT OVERVIEW CARD (descriptive header of the report) ---
            def _esc_join(items):
                return html.escape(", ".join(items)) if items else "—"

            overview_html = (
                '<div class="report-overview">'
                '<div class="ro-title">Report overview</div>'
                f'<b>Date:</b> {html.escape(SYSTEM_DATE)} &nbsp;|&nbsp; '
                f'<b>Strategic goal:</b> {html.escape(goal_context)} &nbsp;|&nbsp; '
                f'<b>Expertise:</b> {html.escape(expertise)}<br>'
                f'<b>Science fields:</b> {_esc_join(sel_sciences)}<br>'
                f'<b>Paradigms:</b> {_esc_join(sel_paradigms)} &nbsp;|&nbsp; '
                f'<b>Structural models:</b> {_esc_join(sel_models)}<br>'
                f'<b>Ideation frameworks:</b> {_esc_join(selected_techniques)}<br>'
                f'<b>Models:</b> Phase 1 — {html.escape(p1_model_label)}; Phase 2 — {html.escape(p2_model_label)}'
                + ('<br><b>Domain module:</b> Crime &amp; Stress Prevention (active)' if cs_active else '')
                + '</div>'
            )

            # --- Persist everything so the report survives Streamlit reruns ---
            # (e.g. clicking the download button). Rendering happens below.
            st.session_state.report_data = {
                "report_html": final_interactive_report,
                "overview_html": overview_html,
                "biblio": biblio_data,
                "elements": final_elements,
                "rel_caption": rel_caption,
                "rel_warning": rel_warning,
                "graph_lint": graph_lint,
                "diversity_metrics": diversity_metrics,
                "diversity_failures": diversity_failures,
                "perspective": graph_perspective,
                "run_id": int(time.time()),
            }

        except Exception as e:
            st.error(f"❌ Pipeline Failure: {str(e)}")

# =============================================================================
# 6. REPORT + SINGLE GRAPH (rendered once, from session state)
# =============================================================================
_rd = st.session_state.get("report_data")
if _rd:
    st.subheader("🧱 INTEGRATED HIERARCHOLOGICAL REPORT")
    st.markdown(_rd["overview_html"], unsafe_allow_html=True)

    if _rd["biblio"]:
        with st.expander("📚 EXTRACTED AUTHOR BACKGROUND", expanded=False):
            st.markdown(_rd["biblio"])

    if _rd["rel_caption"]:
        st.caption(_rd["rel_caption"])
        if _rd["rel_warning"]:
            st.warning(
                "⚠️ Relation-family diversity is below the 25% diagnostic target for "
                "Thesaurus and/or Operational Logic. The system does NOT fabricate edges "
                "to satisfy the target; semantic validity has priority."
            )

    # Full linked report (Phase 1 + Phase 2): the single place where findings and innovations are described.
    st.markdown(_rd["report_html"], unsafe_allow_html=True)

    # --- SEMANTIC LINTER DIAGNOSTIC ---
    _lint = _rd.get("graph_lint", {})
    if _lint.get("warnings") or _lint.get("removed_edges", 0):
        with st.expander("🧪 GRAPH SEMANTIC VALIDATION", expanded=False):
            fc = _lint.get("family_counts", {})
            st.markdown(
                f"**Components:** {_lint.get('components', 0)}  |  "
                f"**Removed invalid/redundant edges:** {_lint.get('removed_edges', 0)}  |  "
                f"**Thesaurus:** {fc.get('Thesaurus', 0)}  |  "
                f"**Logic:** {fc.get('Operational Logic', 0)}  |  "
                f"**UML:** {fc.get('Structural/UML', 0)}  |  "
                f"**Feedback:** {fc.get('Control/Feedback', 0)}"
            )
            if _lint.get("warnings"):
                st.markdown("\n".join(f"- {w}" for w in _lint["warnings"][:15]))

    # --- [NOVO] DIVERSITY AUDIT DIAGNOSTIC ---
    _div = _rd.get("diversity_metrics") or {}
    if _div:
        with st.expander("🛠️ GRAPH DIVERSITY AUDIT", expanded=False):
            st.markdown(
                f"**Total edges:** {_div.get('total_edges', 0)}  |  "
                f"**Thesaurus:** {_div.get('thesaurus_edges', 0)} "
                f"({', '.join(_div.get('thesaurus_distinct', [])) or '—'})  |  "
                f"**UML:** {_div.get('uml_edges', 0)} "
                f"({', '.join(_div.get('uml_distinct', [])) or '—'})  |  "
                f"**Logic (AND/OR/XOR/NOT):** {_div.get('logic_non_ifthen', 0)}  |  "
                f"**IF-THEN:** {_div.get('ifthen_edges', 0)} ({_div.get('ifthen_share', 0):.0%})  |  "
                f"**NEG-FEEDBACK:** {_div.get('feedback_edges', 0)}"
            )
            st.markdown(
                "**Distinct shapes:** " + (", ".join(_div.get("distinct_shapes", [])) or "—")
            )
            _failures = _rd.get("diversity_failures") or []
            if _failures:
                st.markdown("**Unmet requirements (repair may already have been applied):**")
                st.markdown("\n".join(f"- {f}" for f in _failures))
            else:
                st.success("✅ All relation-family and geometry diversity requirements are satisfied.")

    if _rd["elements"]:
        st.divider()

        # MINIMALIST SYSTEM LEGEND
        st.markdown("""
        <div style="font-size: 0.78em; color: #444; background: #ffffff; padding: 15px 25px; border-radius: 15px; border: 1px solid #e9ecef; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.03);">
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
                    <span style="color:#f1c40f;">⬤ Equivalence</span> |
        <span style="color:#6a4c93;">⬤ Negative feedback</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # THE ONE AND ONLY GRAPH (Organic / Hierarchical / Circular switch inside the graph)
        st.subheader("🕸️ HYBRID SEMANTIC SYSTEM MAP")
        st.caption("Preklapljajte med pogledi Organic, Hierarchical in Circular z gumbi v zgornjem levem kotu grafa.")
        render_cytoscape_network(
            _rd["elements"],
            layout_type=_rd["perspective"],
            container_id=f"cy_{_rd['run_id']}"
        )

        # --- REPORT EXPORT: COMPLETE REPORT + GRAPH (HTML only) ---
        export_html = build_html_report(_rd["report_html"], _rd["elements"], _rd["perspective"])
        st.download_button(
            "🌐 EXPORT COMPLETE REPORT + GRAPH (HTML)",
            data=export_html,
            file_name=f"SIS_Universal_Knowledge_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
            mime="text/html",
            use_container_width=True,
            key="export_complete_html"
        )

# =============================================================================
# 7. FOOTER
# =============================================================================
st.divider()
st.caption(f"SIS Universal Knowledge Synthesizer | {VERSION_CODE} | {SYSTEM_DATE}")
