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
import math

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
    ("Stigma", "Help-seeking", "NOT", "blocks"),
    ("Regenerative city", "Chronic distress", "NOT", "mitigates"),
]

# =============================================================================
# 6. EXTENSIONS OF EXISTING ONTOLOGIES (merge with .update(), nothing is removed)
# =============================================================================
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

CRIME_STRESS_SCIENCE_PRESET = [
    "Criminology", "Sociology", "Neuroscience", "Psychology", "Psychiatry",
    "Medicine", "Biology", "Computer Science", "Library Science", "Engineering",
    "Urbanism", "Environmental Science", "Philosophy", "Economics",
    "Legal science", "Geography",
]

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
    """Text PREPENDED to the Phase 1 system prompt."""
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
    """Text PREPENDED to the Phase 2 system prompt."""
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


def render_stress_metrics(st, model_metrics, calc_stress, calc_energy, initial_energy=2500):
    """
    Show model-estimated stress metrics after the pipeline (illustrative only).
    """
    try:
        m = model_metrics or {}
        pf, sf, pr = float(m["f_pf"]), float(m["f_sf"]), float(m["f_pr"])
    except (KeyError, TypeError, ValueError):
        return
    deg = calc_stress(pf, sf, pr)
    eff, pct = calc_energy(deg, initial_energy)
    st.caption(
        f"⚠️ Model-estimated (illustrative, NOT empirical) stress intensity: {deg:.2f} °S; "
        f"effective energy {eff:.0f} kcal ({pct:.1f}%)."
    )


# =============================================================================
# NOVO: Klasifikacija inquiryja po principih članka 2014 (CU + IU)
# =============================================================================
CU_CATEGORIES = {
    1: "Sociological systems, organisations, departments",
    2: "Persons (names, gender, functions, status)",
    3: "Intellectual cultural work (books, systems, databases, innovations)",
    4: "Items, materials, prices, flats",
    5: "Sciences, arts, professions, sports",
    6: "Activities, processes, procedures, events, states",
    7: "Questions (how-to, procedures, membership, publishing)",
}

IU_CATEGORIES = [
    "General information",
    "Access to web pages / resources",
    "Information of resources (books, journals, bibliographies, databases)",
    "Factual knowledge",
    "Accurate / exact information",
    "Professional information (standards, reports)",
    "Special information (polls, warrants, births, deaths)",
    "Empirical knowledge (analysis, statistics, research)",
    "Non-factual knowledge (tricks, new methods, useful ideas, intuitive knowledge)",
]


def classify_query_cu_iu(text: str) -> dict:
    """
    Lightweight rule-based classifier inspired by the 2014 article (CU 1-7 + IU).
    Returns a dict usable for injection into Phase 1.
    """
    if not text:
        return {"cu": 0, "cu_label": "Unclassified", "iu": "General information", "confidence": "low"}

    t = text.lower()

    # CU detection (priority order)
    cu = 0
    if any(w in t for w in ["how to", "kako", "postopek", "navodilo", "članstvo", "objaviti", "vprašanje"]):
        cu = 7
    elif any(w in t for w in ["proces", "postopek", "aktivnost", "dogodek", "stanje", "event", "procedure"]):
        cu = 6
    elif any(w in t for w in ["znanost", "science", "umetnost", "profesija", "šport", "discipline"]):
        cu = 5
    elif any(w in t for w in ["cena", "material", "stanovanje", "item", "price", "flat"]):
        cu = 4
    elif any(w in t for w in ["knjiga", "book", "baza", "database", "sistem", "inovacija", "publikacija", "journal"]):
        cu = 3
    elif any(w in t for w in ["oseba", "person", "ime", "priimek", "funkcija", "status", "minister", "direktor"]):
        cu = 2
    elif any(w in t for w in ["organizacija", "ministrstvo", "oddelek", "department", "služba", "institucija"]):
        cu = 1
    else:
        cu = 1  # default fallback

    # IU detection
    iu = "General information"
    if any(w in t for w in ["ideja", "idea", "nova metoda", "trik", "intuitiv"]):
        iu = "Non-factual knowledge (tricks, new methods, useful ideas, intuitive knowledge)"
    elif any(w in t for w in ["analiza", "statistika", "raziskava", "empirical", "research"]):
        iu = "Empirical knowledge (analysis, statistics, research)"
    elif any(w in t for w in ["standard", "poročilo", "report", "profesional"]):
        iu = "Professional information (standards, reports)"
    elif any(w in t for w in ["natančen", "exact", "točen", "precise", "člen", "zakon"]):
        iu = "Accurate / exact information"
    elif any(w in t for w in ["dejstvo", "faktual", "crime", "forensics", "terorizem"]):
        iu = "Factual knowledge"
    elif any(w in t for w in ["knjiga", "revija", "bibliografija", "baza podatkov", "resource"]):
        iu = "Information of resources (books, journals, bibliographies, databases)"
    elif any(w in t for w in ["stran", "page", "povezava", "url", "dostop"]):
        iu = "Access to web pages / resources"

    return {
        "cu": cu,
        "cu_label": CU_CATEGORIES.get(cu, "Unclassified"),
        "iu": iu,
        "confidence": "medium" if cu > 0 else "low"
    }


def build_dynamic_thesaurus(concepts: list, base_weights: dict = None) -> dict:
    """
    Simple dynamic thesaurus builder inspired by the 2014 article.
    concepts: list of strings extracted from Phase 1 or selected sciences.
    Returns a dict with TT/BT/NT/RT structure and weights 1-5.
    """
    if not concepts:
        return {}

    thesaurus = {}
    weights = base_weights or {}

    # Very lightweight grouping by keyword similarity
    for c in concepts:
        c_clean = c.strip()
        if not c_clean:
            continue
        w = weights.get(c_clean, 3)
        thesaurus[c_clean] = {
            "W": w,
            "TT": None,
            "BT": [],
            "NT": [],
            "RT": []
        }

    # Simple related-term linking (shared tokens)
    keys = list(thesaurus.keys())
    for i, k1 in enumerate(keys):
        tokens1 = set(k1.lower().split())
        for k2 in keys[i+1:]:
            tokens2 = set(k2.lower().split())
            if tokens1 & tokens2:
                thesaurus[k1]["RT"].append(k2)
                thesaurus[k2]["RT"].append(k1)

    return thesaurus


def group_and_evaluate_innovations(innovations: list) -> dict:
    """
    Groups innovations into 4 thematic groups (inspired by the 2014 mind map)
    and produces a simple evaluation matrix (social / semantic-cognitive / IT).
    """
    groups = {
        "Business Intelligence & Decision Support": [],
        "Digital Library / Knowledge Resources": [],
        "Simple IT / Semantic Solutions": [],
        "Specific e-Services & Interventions": []
    }

    for inv in innovations:
        label = (inv.get("label") or "").lower()
        desc = (inv.get("description") or "").lower()
        text = label + " " + desc

        if any(w in text for w in ["dashboard", "monitoring", "analytics", "expert system", "decision", "business process"]):
            groups["Business Intelligence & Decision Support"].append(inv)
        elif any(w in text for w in ["library", "digital", "bibliography", "repository", "archive", "knowledge base"]):
            groups["Digital Library / Knowledge Resources"].append(inv)
        elif any(w in text for w in ["portal", "database", "network", "visualization", "semantic", "query", "matrix"]):
            groups["Simple IT / Semantic Solutions"].append(inv)
        else:
            groups["Specific e-Services & Interventions"].append(inv)

    # Simple domain scoring (1-3)
    matrix = {
        "social": 0,
        "semantic_cognitive": 0,
        "IT": 0
    }
    for inv in innovations:
        text = ((inv.get("label") or "") + " " + (inv.get("description") or "")).lower()
        if any(w in text for w in ["social", "group", "network", "community", "trust", "cohesion", "organization"]):
            matrix["social"] += 2
        if any(w in text for w in ["semantic", "knowledge", "ontology", "thesaurus", "classification", "concept"]):
            matrix["semantic_cognitive"] += 2
        if any(w in text for w in ["system", "platform", "software", "ai", "algorithm", "dashboard", "portal", "database"]):
            matrix["IT"] += 2

    return {"groups": groups, "matrix": matrix}


# =============================================================================
# 0. GLOBAL CONFIGURATION & SESSION DATE
# =============================================================================
SYSTEM_DATE = datetime.now().strftime("%B %d, %Y")
VERSION_CODE = "v24.7.0-GOOGLE-GEMINI-ARTICLE-ENHANCED"

if 'show_user_guide' not in st.session_state:
    st.session_state.show_user_guide = False

if 'phase1_synthesis' not in st.session_state:
    st.session_state.phase1_synthesis = ""

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

    [data-testid="stSidebar"] {
        background-color: #fcfcfc !important;
        border-right: 2px solid #e9ecef !important;
        min-width: 380px !important;
    }

    [data-testid="stSidebar"] .stMarkdown p, 
    [data-testid="stSidebar"] .stMarkdown li,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stExpander p,
    [data-testid="stSidebar"] .stExpander li,
    [data-testid="stSidebar"] .stMarkdown span,
    [data-testid="stSidebar"] .stMarkdown div {
        color: #ffffff !important;
        font-size: 0.98em !important;
        font-weight: 500 !important;
        line-height: 1.6 !important;
        opacity: 1 !important;
    }

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
    return base64.b64encode(svg_str.encode('utf-8')).decode('utf-8')

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

def render_cytoscape_network(elements, layout_type="hierarchical", container_id="cy_canvas"):
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

    selected_layout = layout_configs.get(layout_type, layout_configs["hierarchical"])

    cyto_html = f"""
    <div style="position: relative; width: 100%;">
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
                    {{ selector: 'edge[rel_type="Generalization"]', style: {{ 'target-arrow-shape': 'triangle', 'target-arrow-fill': 'hollow', 'width': 3 }} }},
                    {{ selector: 'edge[rel_type="Realization"]', style: {{ 'line-style': 'dashed', 'target-arrow-shape': 'triangle', 'target-arrow-fill': 'hollow' }} }},
                    {{ selector: 'edge[rel_type="Composition"]', style: {{ 'source-arrow-shape': 'diamond', 'source-arrow-fill': 'filled', 'width': 4 }} }},
                    {{ selector: 'edge[rel_type="Aggregation"]', style: {{ 'source-arrow-shape': 'diamond', 'source-arrow-fill': 'hollow', 'width': 3 }} }},
                    {{ selector: 'edge[rel_type="Dependency"]', style: {{ 'line-style': 'dashed', 'target-arrow-shape': 'vee' }} }},
                    {{ selector: 'edge[rel_type="Conflict"]', style: {{ 'width': 6, 'line-color': '#b91d1d', 'line-style': 'solid', 'target-arrow-color': '#b91d1d', 'target-arrow-shape': 'triangle-cross', 'source-arrow-shape': 'triangle-cross', 'source-arrow-color': '#b91d1d' }} }},
                    {{ selector: 'edge[rel_type="Specialization"]', style: {{ 'line-style': 'dashed', 'line-color': '#000000', 'target-arrow-shape': 'triangle', 'target-arrow-fill': 'filled', 'target-arrow-color': '#000000', 'width': 2 }} }},
                    {{ selector: 'edge[rel_type="Containment"]', style: {{ 'line-color': '#1d3557', 'target-arrow-shape': 'circle', 'target-arrow-color': '#1d3557', 'target-arrow-fill': 'hollow', 'width': 4 }} }},
                    {{ selector: 'edge[rel_type="TT"]', style: {{ 'width': 6, 'line-color': '#1d3557' }} }},
                    {{ selector: 'edge[rel_type="BT"]', style: {{ 'width': 4, 'line-color': '#1d3557' }} }},
                    {{ selector: 'edge[rel_type="NT"]', style: {{ 'width': 4, 'line-color': '#1d3557' }} }},
                    {{ selector: 'edge[rel_type="EQ"]', style: {{ 'line-style': 'double', 'width': 5, 'line-color': '#f1c40f' }} }},
                    {{ selector: 'edge[rel_type="RT"]', style: {{ 'line-style': 'dotted', 'width': 2, 'line-color': '#2a9d8f', 'target-arrow-shape': 'none' }} }},
                    {{ selector: 'edge[rel_type="AS"]', style: {{ 'line-style': 'dashed', 'width': 2, 'line-color': '#7b2cb1' }} }},
                    {{ selector: 'edge[rel_type="IN"]', style: {{ 'line-style': 'dotted', 'width': 3, 'line-color': '#0077b6', 'target-arrow-shape': 'triangle' }} }},
                    {{ selector: 'edge[rel_type="AND"]', style: {{ 'width': 5, 'line-color': '#00FF00', 'target-arrow-color': '#00FF00', 'target-arrow-shape': 'triangle' }} }},
                    {{ selector: 'edge[rel_type="OR"]', style: {{ 'width': 3, 'line-color': '#00BFFF', 'line-style': 'dashed', 'target-arrow-color': '#00BFFF', 'target-arrow-shape': 'vee' }} }},
                    {{ selector: 'edge[rel_type="XOR"]', style: {{ 'width': 4, 'line-color': '#FF8C00', 'line-style': 'double', 'target-arrow-color': '#FF8C00', 'target-arrow-shape': 'diamond' }} }},
                    {{ selector: 'edge[rel_type="NOT"]', style: {{ 'width': 4, 'line-color': '#FF0000', 'line-style': 'dashed', 'target-arrow-color': '#FF0000', 'target-arrow-shape': 'tee' }} }},
                    {{ selector: 'edge[rel_type="IF-THEN"]', style: {{ 'width': 4, 'line-color': '#FFD700', 'target-arrow-color': '#FFD700', 'target-arrow-shape': 'triangle', 'arrow-scale': 1.3 }} }},
                    {{ selector: 'node[shape="star"]', style: {{ 'font-size': '16px', 'width': 130, 'height': 130, 'border-width': 5, 'border-color': '#FFD700' }} }}
                ],
                layout: {selected_layout}
            }});

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


def calculate_systemic_stress(f_pf, f_sf, f_pr):
    try:
        pf = float(f_pf)
        sf = float(f_sf)
        pr = float(f_pr)
        if pf <= 0: pf = 0.001 
        ratio = (sf * pr) / pf
        clamped_ratio = max(0.0, min(ratio, 1.0))
        stress_rad = math.asin(math.sqrt(clamped_ratio))
        return math.degrees(stress_rad)
    except Exception:
        return 0.0


def calculate_effective_energy(stress_intensity, initial_potential=2500):
    try:
        max_stress = 90.0
        loss_ratio = stress_intensity / max_stress
        loss_ratio = max(0.0, min(loss_ratio, 1.0))
        effective_energy = initial_potential - (initial_potential * loss_ratio)
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
            "color": "#FF69B4", "shape": "diamond",
            "desc": "Forces that pull concepts or actors together."
        },
        "Repulsion": {
            "color": "#FF4500", "shape": "diamond",
            "desc": "Forces that push concepts or actors apart."
        },
        "Induction": {
            "color": "#87CEEB", "shape": "diamond",
            "desc": "Moving from specific observations to general principles."
        },
        "Deduction": {
            "color": "#4682B4", "shape": "diamond",
            "desc": "Moving from general principles to specific cases."
        },
        "Abduction": {
            "color": "#9370DB", "shape": "diamond",
            "desc": "Inferring the best explanation for observations."
        },
        "Dialectics": {
            "color": "#DC143C", "shape": "diamond",
            "desc": "Thesis-antithesis-synthesis tension resolution."
        },
        "Analogy": {
            "color": "#32CD32", "shape": "diamond",
            "desc": "Mapping structure from a known domain to a new one."
        },
        "Abstraction": {
            "color": "#A9A9A9", "shape": "diamond",
            "desc": "Removing detail to reveal higher-order patterns."
        },
        "Concretization": {
            "color": "#CD853F", "shape": "diamond",
            "desc": "Adding concrete detail to an abstract idea."
        },
        "Inversion": {
            "color": "#FF1493", "shape": "diamond",
            "desc": "Reversing assumptions or causal direction."
        },
        "Combination": {
            "color": "#00CED1", "shape": "diamond",
            "desc": "Merging previously separate elements."
        },
        "Decomposition": {
            "color": "#B8860B", "shape": "diamond",
            "desc": "Breaking a whole into constituent parts."
        },
        "Generalization": {
            "color": "#6A5ACD", "shape": "diamond",
            "desc": "Extending a finding beyond its original scope."
        },
        "Specialization": {
            "color": "#20B2AA", "shape": "diamond",
            "desc": "Narrowing a finding to a precise subdomain."
        },
        "Temporal shifting": {
            "color": "#FF6347", "shape": "diamond",
            "desc": "Moving the problem forward or backward in time."
        },
        "Scale shifting": {
            "color": "#4169E1", "shape": "diamond",
            "desc": "Changing the level of analysis (micro ↔ macro)."
        },
        "Value reorientation": {
            "color": "#FFD700", "shape": "diamond",
            "desc": "Changing the ethical or preference weighting of outcomes."
        }
    }
}

# Minimal placeholders for the rest of the knowledge base (extend as needed)
KNOWLEDGE_BASE = {
    "User profiles": {
        "Researcher": {"description": "Academic or applied researcher seeking rigorous synthesis."},
        "Policy maker": {"description": "Decision-maker needing actionable, multi-level insights."},
        "Practitioner": {"description": "Professional applying knowledge in organizational settings."},
    },
    "Science fields": {
        "Physics": {"methods": ["Experiment", "Modelling"], "tools": ["Simulation", "Measurement"]},
        "Psychology": {"methods": ["Experiment", "Survey"], "tools": ["Psychometrics", "Observation"]},
        "Sociology": {"methods": ["Survey", "Network analysis"], "tools": ["Statistics", "Qualitative coding"]},
        "Computer Science": {"methods": ["Algorithm design", "Data mining"], "tools": ["Python", "Graph databases"]},
        "Criminology": {"methods": ["Case study", "Statistical analysis"], "tools": ["GIS", "Predictive models"]},
        "Library Science": {"methods": ["Classification", "Thesaurus construction"], "tools": ["Cataloguing systems", "Metadata"]},
    },
    "Scientific paradigms": {
        "Rationalism": "Reason and logical deduction as primary sources of knowledge.",
        "Empiricism": "Observation and sensory experience as the foundation of knowledge.",
        "Pragmatism": "Truth judged by practical consequences and usefulness.",
    },
    "Structural models": {
        "Concepts": "Basic building blocks of knowledge representation.",
        "Networks": "Relational structures among entities.",
        "Hierarchies": "Ordered levels of abstraction or authority.",
    }
}

# Merge extra science fields
KNOWLEDGE_BASE["Science fields"].update(EXTRA_SCIENCE_FIELDS)

HIERARCHOLOGY_ONTOLOGY = {
    "core_definitions": {
        "Hierarchology": "The study of hierarchical structures and processes across natural and social systems.",
        "Hierarchography": "The mapping and visualization of hierarchical relations using formal and visual languages.",
    },
    "hierarchical_levels": {
        "Macro": "Large-scale systemic patterns and planetary/ecological influences.",
        "Meso": "Organizational, institutional and community-level structures.",
        "Micro": "Individual, biological and cognitive-level processes.",
    },
    "operational_logic": {
        "Internal Processes": "Inductive movement from concrete observations toward general principles.",
        "External Functioning": "Deductive application of general principles to specific cases.",
    },
    "hierarchography_tools": ["Semantic graphs", "Thesauri", "Mind maps", "Network analysis", "Cytoscape layouts"]
}

IDEATION_TECHNIQUES = {
    "Six Thinking Hats": "Parallel thinking in six modes (facts, emotions, caution, benefits, creativity, process).",
    "SCAMPER": "Substitute, Combine, Adapt, Modify, Put to other uses, Eliminate, Reverse.",
    "TRIZ": "Theory of inventive problem solving using contradiction matrix and inventive principles.",
    "Design Thinking": "Empathize, Define, Ideate, Prototype, Test.",
    "Morphological Analysis": "Systematic exploration of all possible combinations of parameters.",
}


# =============================================================================
# SIDEBAR
# =============================================================================
with st.sidebar:
    st.markdown('<div class="sidebar-logo-container">' + 
                f'<img src="data:image/svg+xml;base64,{get_svg_base64(SVG_3D_RELIEF)}" width="180">' + 
                '</div>', unsafe_allow_html=True)
    
    st.markdown(f'<div class="date-badge">{SYSTEM_DATE}</div>', unsafe_allow_html=True)
    
    google_api_key = st.text_input("🔑 Google Gemini API Key", type="password", key="google_api_key")
    
    p1_model = st.selectbox("Phase 1 Model (IMA)", ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-2.5-pro"], index=0)
    p1_model_label = p1_model
    p2_model = st.selectbox("Phase 2 Model (MA)", ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-2.5-pro"], index=1)
    p2_model_label = p2_model
    
    graph_perspective = st.selectbox("Default Graph Perspective", ["hierarchical", "organic", "concentric", "circular", "grid"], index=0)
    graph_node_count = st.slider("Max nodes in graph", 10, 80, 35)
    
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
        st.markdown("• ⬛ ┄ ➤ **Specialization**: Deduktivna izpeljava iz splošnega zakona v specifičen primer.")
        st.markdown("• 🟦 — ◯ **Containment**: Močna strukturna vsebovanost.")

    with st.expander("🔬 Science Taxonomy & Levels", expanded=False):
        st.markdown("**Field Domains:**")
        for s in sorted(KNOWLEDGE_BASE["Science fields"].keys()): 
            st.markdown(f"• **{s}**")
        st.markdown("---")
        st.markdown("**Hierarchical Levelsape/3.26.0/cytoscape.min.js"></script>
<script>
const elements = {graph_json};
const cy = cytoscape({{
 container: document.getElementById('cy'),
 elements: elements,
 style: [
 {{selector:'node',style:{{'label':'data(label)','text-valign':'center','text-halign':'center','color':'#1d3557','background-color':'data(color)','width':'data(size)','height':'data(size)','shape':'data(shape)','font-size':'12px','font-weight':'bold','text-wrap':'wrap','text-max-width':'80px','border-width':3,'border-color':'#fff','text-outline-color':'#fff','text-outline-width':2}}}},
 {{selector:'edge',style:{{'width':2,'line-color':'data(color)','label':'data(rel_type)','font-size':'9px','font-weight':'bold','color':'#2a9d8f','curve-style':'unbundled-bezier','target-arrow-color':'data(color)','target-arrow-shape':'vee','text-background-opacity':1,'text-background-color':'#fff','text-background-padding':'3px'}}}},
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
 {{selector:'edge[rel_type="IF-THEN"]',style:{{'width':4}}}}
 ],
 layout: {json.dumps({"name":"cose","fit":True,"padding":50})}
}});
</script></body></html>"""


# --- MAIN PAGE CONTENT ---
st.markdown('<h1 class="main-header-gradient">🧱 SIS Universal Knowledge Synthesizer</h1>', unsafe_allow_html=True)
st.markdown(f"**Sequential Multi-Engine Pipeline** | Current Operating Date: **{SYSTEM_DATE}** | Version: **{VERSION_CODE}**")

if st.session_state.show_user_guide:
    st.info(f"""
    **Sequential Synergy Pipeline Workflow:**
    1. **Key Input**: Enter your Google Gemini API key and select Google models for Phase 1 and Phase 2.
    2. **Research Foundation (Step 1)**: Google Gemini performs structural synthesis using Integrated Metamodel Architecture (IMA).
    3. **Innovation Prompt (Step 2)**: Google Gemini takes the Phase 1 foundation and generates useful innovative ideas using Mental Approaches (MA) logic.
    4. **Visualization**: The interactive graph maps structural facts against generative ideas.
    5. **Article 2014 enhancements**: CU/IU classification, dynamic thesaurus, innovation grouping + evaluation matrix.
    """)

col_ref1, col_ref2 = st.columns(2)
with col_ref1:
    st.markdown("""<div class="metamodel-box"><b>🏛️ Phase 1: Google Gemini (IMA Architecture)</b><br>Structural reasoning building the factual foundation. Focus: Identity, Mission, Problem. </div>""", unsafe_allow_html=True)
with col_ref2:
    st.markdown("""<div class="mental-approach-box"><b>🧠 Phase 2: Google Gemini (MA Architecture)</b><br>Cognitive transformation generating innovative solutions. Focus: Dialectics, Perspective, Induction.</div>""", unsafe_allow_html=True)

st.markdown("### 🛠️ CONFIGURE SYNERGY PIPELINE")

r1c1, r1c2, r1c3 = st.columns([1.5, 2, 1])
with r1c1: target_authors = st.text_input("👤 Authors for ORCID Analysis:", placeholder="Karl Petrič, Samo Kralj, Teodor Petrič")
with r1c2: sel_sciences = st.multiselect("2. Select Science Fields:", sorted(list(KNOWLEDGE_BASE["Science fields"].keys())), default=["Physics", "Psychology", "Sociology"])
with r1c3: expertise = st.select_slider("3. Expertise Level:", ["Novice", "Intermediate", "Expert"], value="Expert")

r2c1, r2c2, r2c3 = st.columns(3)
with r2c1: sel_paradigms = st.multiselect("4. Scientific Paradigms:", list(KNOWLEDGE_BASE["Scientific paradigms"].keys()), default=["Rationalism"])
with r2c2: sel_models = st.multiselect("5. Structural Models:", list(KNOWLEDGE_BASE["Structural models"].keys()), default=["Concepts"])
with r2c3: goal_context = st.selectbox("6. Strategic Project Goal:", ["Scientific Research", "Problem Solving", "Educational", "Policy Making"])

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
    combined_desc = " | ".join([f"**{t}**: {IDEATION_TECHNIQUES[t]}" for t in selected_techniques])
    st.info(f"**Active Hybrid Strategy:** {combined_desc}")
st.divider()

# Crime & Stress mode (calculator removed)
cs_mode = render_crime_stress_mode(st)
st.divider()

# DUAL INQUIRY INTERFACE
col_inq1, col_inq2, col_inq3 = st.columns([2, 2, 1])
with col_inq1:
    user_query = st.text_area("❓ STEP 1: Research Inquiry (for GOOGLE GEMINI):", placeholder="Fact-based Foundational Inquiry...", height=200)
with col_inq2:
    idea_query = st.text_area("💡 STEP 2: Innovation Prompt (for GOOGLE GEMINI):", placeholder="Targets for innovative idea production...", height=200)
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
# 5. SYNERGY EXECUTION ENGINE (GOOGLE GEMINI / GEMMA ONLY)
# =============================================================================

def google_generate(client, model_id, system_prompt, user_content, temperature, max_retries=4):
    if client is None:
        raise RuntimeError("Google Gemini client is not initialized.")

    config_kwargs = {
        "system_instruction": system_prompt,
        "temperature": temperature,
    }
    if model_id.startswith("gemini-3"):
        try:
            config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_level="low")
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
                wait_time = (2 ** attempt) + 1
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

            cs_active = crime_stress_should_activate(cs_mode, user_query, idea_query)

            # --- NOVO: CU/IU klasifikacija (članek 2014) ---
            cu_iu = classify_query_cu_iu(user_query)
            cu_iu_note = (
                f"\n\n[CU/IU CLASSIFICATION – inspired by Petrič et al. 2014]\n"
                f"CU category: {cu_iu['cu']} – {cu_iu['cu_label']}\n"
                f"Assumed user intention (IU): {cu_iu['iu']}\n"
                f"Confidence: {cu_iu['confidence']}\n"
                f"Use this classification to better structure the problem definition and to prioritise relevant knowledge domains."
            )

            with st.spinner('🔍 Accessing ORCID research background...'):
                biblio_data = fetch_author_bibliographies(target_authors) if target_authors else ""

            file_context_str = f"\n\n[FILE CONTEXT]:\n{file_content}" if file_content else ""
            biblio_context = f"\n\n[AUTHOR RESEARCH BACKGROUND]:\n{biblio_data}" if biblio_data else ""
            full_ai_input = f"{active_context}\nUSER RESEARCH INQUIRY:\n{user_query}{file_context_str}{biblio_context}{cu_iu_note}"

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
12. Take into account the CU/IU classification provided in the input: use the CU
    category to focus the relevant entity types and the IU to prioritise the kind
    of knowledge the user is seeking.

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
            if cs_active:
                phase1_system_prompt = build_phase1_addendum() + phase1_system_prompt

            with st.spinner(f'PHASE 1: IMA synthesis with {p1_model_label}...'):
                phase1_synthesis = google_generate(
                    google_client, p1_model, phase1_system_prompt,
                    full_ai_input, temperature=0.40
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

Start the report with a short "### Executive Synthesis" section (max 6 sentences)
naming the single most important interdisciplinary insight connecting the
selected science fields — this is the thread the rest of the report follows.

For each of 3–4 innovations, use this exact literal markdown structure so the
report stays clear and scannable:

#### Innovation N: <short, concrete, punchy name>
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

RELATION TYPES — you MUST draw from all three families below, not just UML.
Pick the family that actually fits the semantic meaning of each edge; never
default to UML/structural types just because they are familiar.

A) THESAURUS FAMILY (ISO 25964 style — use for conceptual/terminological links):
   - TT (Top Term) / BT (Broader Term) / NT (Narrower Term): taxonomic level jumps
   - EQ (Equivalence): two labels denote the same concept
   - RT (Related Term): loosely associated concepts, no hierarchy
   - AS (Associative): non-taxonomic thematic association
   - IN (Instance-of): a concrete case of a general class

B) STRUCTURAL/UML FAMILY (use for architectural or compositional links):
   Generalization, Specialization, Containment, Realization, Composition,
   Aggregation, Dependency, Conflict

C) OPERATIONAL LOGIC FAMILY (use for decision/causal/conditional links —
   especially between an IMA finding, a contradiction, an MA, and an innovation):
   AND (joint necessary conditions), OR (alternative sufficient paths),
   XOR (mutually exclusive choices), NOT (negation/exclusion),
   IF-THEN (conditional/causal trigger)

MANDATORY DIVERSITY RULE (quantitative, not optional): of the total edges,
AT LEAST 25% must be Thesaurus-family and AT LEAST 25% must be Operational
Logic-family. The remainder may be Structural/UML. For example, in a graph
with 20 edges, at least 5 must be thesaurus and at least 5 must be logic type.
A graph that fails this ratio is INVALID and must be corrected before output.

CAUSAL DIRECTION DISCIPLINE (this is where most graphs break):
- For every IF-THEN edge: source = the cause/enabler/condition, target = the
  resulting effect/outcome. Read it aloud as "If <source> then <target>" — if
  that sentence does not make literal sense, the arrow is backwards. Example:
  [Computer Science] --IF-THEN--> [Innovation: Semantic Mediator] is correct
  (a field enables an innovation); the reverse is wrong.
- The same left-to-right cause→effect discipline applies to Dependency,
  Realization and AND/OR edges: source is the precondition, target is what
  depends on or results from it.

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
narrower → target is broader; NT: source is broader → target is narrower).

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
            if cs_active:
                phase2_system_prompt = build_phase2_addendum() + phase2_system_prompt

            with st.spinner(f'PHASE 2: MA innovation with {p2_model_label}...'):
                phase2_user_content = (
                    f"PHASE 1 IMA FOUNDATION:\n{phase1_synthesis}\n\n"
                    f"USER INNOVATION OBJECTIVE:\n{idea_query}{file_context_str}"
                )
                google_innovation = google_generate(
                    google_client, p2_model, phase2_system_prompt,
                    phase2_user_content, temperature=0.85
                )

            # --- 4. PROCESS RESULTS ---
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

            if json_raw.strip():
                try:
                    cleaned_json = json_raw.strip()
                    cleaned_json = re.sub(r'^```(?:json)?\s*', '', cleaned_json, flags=re.I)
                    cleaned_json = re.sub(r'\s*```$', '', cleaned_json)
                    match = re.search(r'\{.*\}', cleaned_json, re.DOTALL)
                    if match:
                        cleaned_json = match.group(0)
                    cleaned_json = re.sub(r',\s*([}\]])', r'\1', cleaned_json)
                    parsed = json.loads(cleaned_json)
                    if isinstance(parsed, dict):
                        g_data = parsed
                except Exception as parse_exc:
                    st.warning(f"⚠️ Semantic graph JSON could not be parsed; report retained. ({parse_exc})")

            if not isinstance(g_data.get("nodes"), list):
                g_data["nodes"] = []
            if not isinstance(g_data.get("edges"), list):
                g_data["edges"] = []

            full_report = (
                f"## 📚 Phase 1: IMA Structural Foundation (Google {p1_model_label})\n\n"
                f"{phase1_synthesis}\n\n---\n"
                f"## 💡 Phase 2: MA Strategic Innovations (Google {p2_model_label})\n\n"
                f"{innovation_text}"
            )

            if isinstance(g_data.get("nodes"), list):
                g_data["nodes"] = g_data["nodes"][:graph_node_count]
                valid_node_ids = {
                    str(n.get("id", f"n{i}"))
                    for i, n in enumerate(g_data["nodes"])
                }
                g_data["edges"] = [
                    e for e in g_data.get("edges", [])
                    if str(e.get("source")) in valid_node_ids
                    and str(e.get("target")) in valid_node_ids
                ]

            if g_data.get("nodes"):
                for n in g_data.get("nodes", []):
                    lbl = n.get("label", "Node")
                    nid = n.get("id", f"n{lbl}")
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
                        "data": {"id": nid, "label": lbl, "color": n_color, "shape": n_shape, "size": n_size, "description": n.get("description", "Detail breakdown in report.")}
                    })

                for e in g_data.get("edges", []):
                    rel = e.get("rel_type", "Association")

                    if rel in ["Generalization", "Realization", "Composition", "Aggregation", "Dependency", "Specialization", "Containment", "Conflict"]:
                        if rel == "Conflict":
                            e_color = "#b91d1d"
                        elif rel == "Specialization":
                            e_color = "#000000"
                        elif rel == "Containment":
                            e_color = "#1D3557"
                        else:
                            e_color = "#E63946"
                    elif rel in ["BT", "NT", "TT"]:
                        e_color = "#1D3557"
                    elif rel == "IN":
                        e_color = "#0077B6"
                    elif rel == "AS":
                        e_color = "#7B2CB1"
                    elif rel == "EQ":
                        e_color = "#F1C40F"
                    elif rel == "RT":
                        e_color = "#2A9D8F"
                    elif rel == "AND":
                        e_color = "#00FF00"
                    elif rel == "OR":
                        e_color = "#00BFFF"
                    elif rel == "XOR":
                        e_color = "#FF8C00"
                    elif rel == "NOT":
                        e_color = "#FF0000"
                    elif rel == "IF-THEN":
                        e_color = "#FFD700"
                    else:
                        e_color = "#ADB5BD"

                    final_elements.append({
                        "data": {
                            "id": e.get("id", f"e{len(final_elements)}"),
                            "source": e.get("source"),
                            "target": e.get("target"),
                            "rel_type": rel,
                            "color": e_color,
                            "weight": e.get("weight", 1.0),
                            "label": e.get("label", rel)
                        }
                    })

            # Dedup parallel edges
            seen_pairs = set()
            deduped_elements = []
            for el in final_elements:
                d = el.get("data", {})
                if "source" in d:
                    pair_key = frozenset({d.get("source"), d.get("target")})
                    if pair_key in seen_pairs:
                        continue
                    seen_pairs.add(pair_key)
                deduped_elements.append(el)
            final_elements = deduped_elements

            # Connectivity safety net
            all_node_ids = [item["id"] for item in nodes_to_link]
            connected_ids = set()
            for el in final_elements:
                d = el.get("data", {})
                if "source" in d:
                    connected_ids.add(d.get("source"))
                    connected_ids.add(d.get("target"))
            prev_id = None
            for nid in all_node_ids:
                if nid not in connected_ids and prev_id is not None:
                    final_elements.append({
                        "data": {
                            "id": f"auto_link_{nid}",
                            "source": prev_id,
                            "target": nid,
                            "rel_type": "RT",
                            "color": "#2A9D8F",
                            "weight": 1.0,
                            "label": "RT"
                        }
                    })
                    connected_ids.add(nid)
                prev_id = nid

            # Relation-family diagnostic
            THESAURUS_TYPES = {"TT", "BT", "NT", "RT", "EQ", "AS", "IN"}
            LOGIC_TYPES = {"AND", "OR", "XOR", "NOT", "IF-THEN"}
            STRUCTURAL_TYPES = {"Generalization", "Specialization", "Containment",
                                 "Realization", "Composition", "Aggregation",
                                 "Dependency", "Conflict"}
            edge_rel_types = [el["data"]["rel_type"] for el in final_elements if "source" in el.get("data", {})]
            n_thesaurus = sum(1 for r in edge_rel_types if r in THESAURUS_TYPES)
            n_logic = sum(1 for r in edge_rel_types if r in LOGIC_TYPES)
            n_structural = sum(1 for r in edge_rel_types if r in STRUCTURAL_TYPES)
            if edge_rel_types:
                total_edges = len(edge_rel_types)
                st.caption(
                    f"🔗 Relation mix in graph ({total_edges} edges) — "
                    f"Thesaurus: {n_thesaurus} ({n_thesaurus/total_edges:.0%}) | "
                    f"Structural/UML: {n_structural} ({n_structural/total_edges:.0%}) | "
                    f"Operational Logic: {n_logic} ({n_logic/total_edges:.0%})"
                )
                if n_thesaurus / total_edges < 0.20 or n_logic / total_edges < 0.20:
                    st.warning(
                        "⚠️ The generated graph leans too heavily on structural/UML relations "
                        "(target: ≥25% thesaurus, ≥25% operational logic). Try re-running Phase 2, "
                        "or nudge the Innovation Prompt to explicitly request thesaurus (BT/NT/RT/EQ) "
                        "and logic (AND/OR/IF-THEN) connections."
                    )

            if cs_active:
                render_stress_metrics(st, g_data.get("system_metrics"), calculate_systemic_stress, calculate_effective_energy)

            # --- 5. FINAL DISPLAY ---
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

            st.subheader("🧱 INTEGRATED HIERARCHOLOGICAL REPORT")
            if biblio_data:
                with st.expander("📚 EXTRACTED AUTHOR BACKGROUND", expanded=False):
                    st.markdown(biblio_data)

            # Show CU/IU classification result
            st.info(f"**CU/IU Classification (2014 article principle):** CU {cu_iu['cu']} – {cu_iu['cu_label']} | IU: {cu_iu['iu']} (confidence: {cu_iu['confidence']})")

            st.markdown(final_interactive_report, unsafe_allow_html=True)

            # Innovation deep-dive + grouping (2014 mind-map principle)
            if final_elements:
                st.divider()
                st.markdown("### 🚀 STRATEGIC INNOVATION DEEP-DIVE")
                st.info("The following strategic breakthroughs have been synthesized from the multi-dimensional analysis above.")

                innovations = [n['data'] for n in final_elements if n['data'].get('shape') == 'diamond']

                if innovations:
                    # Grouping + evaluation matrix (article 2014)
                    eval_result = group_and_evaluate_innovations(innovations)
                    
                    st.markdown("#### 📊 Innovation Groups (inspired by 2014 mind map)")
                    for group_name, items in eval_result["groups"].items():
                        if items:
                            with st.expander(f"{group_name} ({len(items)})", expanded=False):
                                for inv in items:
                                    st.markdown(f"- **{inv['label']}**: {inv.get('description', '')[:200]}...")

                    st.markdown("#### 🧮 Simple Evaluation Matrix (social / semantic-cognitive / IT)")
                    matrix = eval_result["matrix"]
                    st.write(f"- Social domain score: **{matrix['social']}**")
                    st.write(f"- Semantic-cognitive domain score: **{matrix['semantic_cognitive']}**")
                    st.write(f"- IT domain score: **{matrix['IT']}**")

                    for inv in innovations:
                        g_url = urllib.parse.quote(inv['label'])
                        detailed_desc = inv.get('description', "Detailed strategic analysis is available in the integrated report above.")
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

                st.subheader(f"🕸️ HYBRID SEMANTIC SYSTEM MAP ({graph_perspective.upper()} VIEW)")
                render_cytoscape_network(
                    final_elements, 
                    layout_type=graph_perspective, 
                    container_id=f"cy_{int(time.time())}"
                )

                export_html = build_html_report(final_interactive_report, final_elements, graph_perspective)
                st.download_button(
                    "🌐 EXPORT COMPLETE REPORT + GRAPH (HTML)",
                    data=export_html,
                    file_name=f"SIS_Universal_Knowledge_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                    mime="text/html",
                    use_container_width=True,
                    key="export_complete_html"
                )

                st.session_state.final_graph_elements = final_elements
                st.session_state.report_ready = True

        except Exception as e:
            st.error(f"❌ Pipeline Failure: {str(e)}")


# =============================================================================
# 6. MULTI-PERSPECTIVE GALLERY
# =============================================================================

if st.session_state.get('report_ready') and 'final_graph_elements' in st.session_state:
    st.divider()
    st.markdown('<h2 style="color: #1d3557; text-align: center;">🖼️ MULTI-PERSPECTIVE GRAPH GALLERY</h2>', unsafe_allow_html=True)
    st.info("💡 **SEQUENTIAL SAVING INSTRUCTIONS:** Below are tabs featuring different visual perspectives of the same knowledge synthesis. Please open each tab individually and click the **EXPORT PNG** button to save all 5 architectural versions to your local drive.")

    tab0, tab1, tab2, tab3, tab4 = st.tabs([
        "🌿 ORGANIC", "🌲 HIERARCHICAL", "🎯 CONCENTRIC", "⭕ CIRCULAR", "🔲 GRID"
    ])

    with tab0:
        st.markdown("**Organic View:** Force-directed natural clustering — related concepts gravitate together, ideal for spotting emergent interdisciplinary clusters.")
        render_cytoscape_network(st.session_state.final_graph_elements, layout_type="organic", container_id="gal_organic")

    with tab1:
        st.markdown("**Hierarchical View:** Primary IMA → MA structure and semantic dependencies.")
        render_cytoscape_network(st.session_state.final_graph_elements, layout_type="hierarchical", container_id="gal_hierarchical")

    with tab2:
        st.markdown("**Concentric View:** Macro–Meso–Micro systemic organization.")
        render_cytoscape_network(st.session_state.final_graph_elements, layout_type="concentric", container_id="gal_concentric")

    with tab3:
        st.markdown("**Circular View:** Relational interdependence without an organic force layout.")
        render_cytoscape_network(st.session_state.final_graph_elements, layout_type="circular", container_id="gal_circular")

    with tab4:
        st.markdown("**Grid View:** Structured inspection of the same semantic architecture.")
        render_cytoscape_network(st.session_state.final_graph_elements, layout_type="grid", container_id="gal_grid")


# =============================================================================
# 7. FOOTER
# =============================================================================
st.divider()
st.caption(f"SIS Universal Knowledge Synthesizer | {VERSION_CODE} | {SYSTEM_DATE}")


