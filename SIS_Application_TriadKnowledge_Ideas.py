import streamlit as st
import json
import base64
import requests
import urllib.parse
import re
import time
from datetime import datetime
from google import genai
from google.genai import types as genai_types
import streamlit.components.v1 as components


# =============================================================================
# SIS UNIVERSAL KNOWLEDGE SYNTHESIZER
# Qwen2.5-72B-Instruct + Google Gemini/Gemma
# VERSION: v22.8.1-QWEN72B-STABLE
# =============================================================================

SYSTEM_DATE = datetime.now().strftime("%B %d, %Y")
VERSION_CODE = "v22.8.1-QWEN72B-STABLE"

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

HF_MODEL_ID = "Qwen/Qwen2.5-72B-Instruct"
HF_ROUTER_URL = "https://router.huggingface.co/v1/chat/completions"


# =============================================================================
# HUGGING FACE QWEN ENGINE
# =============================================================================

def huggingface_generate(
    api_key,
    model_id,
    system_prompt,
    user_content,
    temperature=0.5,
    top_p=None,
    max_tokens=8192
):
    """
    Stable Hugging Face Inference Providers implementation.

    Qwen2.5-72B-Instruct is called through the OpenAI-compatible
    Hugging Face router.

    IMPORTANT:
    The HF token must have permission to call Inference Providers.
    """

    if not api_key or not api_key.strip():
        raise RuntimeError(
            "Hugging Face API key is missing. "
            "Create/use a token with permission to make calls to "
            "Inference Providers."
        )

    clean_model_id = str(model_id).strip()

    if clean_model_id.startswith("hf:"):
        clean_model_id = clean_model_id[3:]

    headers = {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    messages = []

    if system_prompt:
        messages.append({
            "role": "system",
            "content": system_prompt
        })

    messages.append({
        "role": "user",
        "content": user_content
    })

    payload = {
        "model": clean_model_id,
        "messages": messages,
        "temperature": float(temperature),
        "stream": False,
        "max_tokens": int(max_tokens),
    }

    if top_p is not None:
        payload["top_p"] = float(top_p)

    try:
        response = requests.post(
            HF_ROUTER_URL,
            headers=headers,
            json=payload,
            timeout=300
        )
    except requests.exceptions.Timeout as e:
        raise RuntimeError(
            "Hugging Face request timed out after 300 seconds."
        ) from e
    except requests.exceptions.RequestException as e:
        raise RuntimeError(
            f"Hugging Face network error: {str(e)}"
        ) from e

    if response.status_code != 200:

        try:
            error_data = response.json()
        except Exception:
            error_data = {}

        error_message = (
            error_data.get("error")
            or error_data.get("message")
            or response.text
            or "Unknown Hugging Face API error."
        )

        if response.status_code == 401:
            raise RuntimeError(
                "Hugging Face authentication failed (401). "
                "Check that the token is valid and has not expired."
            )

        if response.status_code == 403:
            raise RuntimeError(
                "Hugging Face authorization failed (403). "
                "The token does not have sufficient permission to call "
                "Inference Providers. In Hugging Face token settings, "
                "enable the permission 'Make calls to Inference Providers'. "
                f"Original HF message: {error_message}"
            )

        if response.status_code == 404:
            raise RuntimeError(
                f"Hugging Face model/provider route not found (404): "
                f"{error_message}"
            )

        if response.status_code == 429:
            raise RuntimeError(
                f"Hugging Face rate limit reached (429): {error_message}"
            )

        raise RuntimeError(
            f"Hugging Face API error ({response.status_code}): "
            f"{error_message}"
        )

    try:
        result = response.json()
    except Exception as e:
        raise RuntimeError(
            "Hugging Face returned a non-JSON response."
        ) from e

    try:
        content = result["choices"][0]["message"]["content"]

        if isinstance(content, list):
            content = "".join(
                item.get("text", "")
                for item in content
                if isinstance(item, dict)
            )

        if not content:
            raise ValueError("Empty model response.")

        return str(content)

    except Exception as e:
        raise RuntimeError(
            "Unexpected Hugging Face response format: "
            + json.dumps(
                result,
                ensure_ascii=False
            )[:4000]
        ) from e


# =============================================================================
# UNIFIED AI GENERATION ENGINE
# =============================================================================

def gemini_generate(
    client,
    model_id,
    system_prompt,
    user_content,
    temperature=0.5,
    top_p=None,
    huggingface_api_key=None
):
    """
    Unified model interface.

    Google:
        Gemini / Gemma through google-genai.

    Hugging Face:
        Qwen2.5-72B-Instruct through HF Inference Providers.
    """

    if not model_id:
        raise RuntimeError("No AI model has been selected.")

    # -------------------------------------------------------------------------
    # HUGGING FACE / QWEN
    # -------------------------------------------------------------------------

    if str(model_id).startswith("hf:"):

        return huggingface_generate(
            api_key=huggingface_api_key,
            model_id=model_id,
            system_prompt=system_prompt,
            user_content=user_content,
            temperature=temperature,
            top_p=top_p,
            max_tokens=8192
        )

    # -------------------------------------------------------------------------
    # GOOGLE GEMINI / GEMMA
    # -------------------------------------------------------------------------

    if client is None:
        raise RuntimeError(
            "Google GenAI client is not initialized."
        )

    is_gemma = str(model_id).startswith("gemma")

    config_kwargs = {
        "temperature": float(temperature)
    }

    if top_p is not None:
        config_kwargs["top_p"] = float(top_p)

    if is_gemma:

        combined_input = (
            "### SYSTEM INSTRUCTIONS ###\n"
            f"{system_prompt}\n\n"
            "### USER INPUT ###\n"
            f"{user_content}"
        )

        config = genai_types.GenerateContentConfig(
            **config_kwargs
        )

        response = client.models.generate_content(
            model=model_id,
            contents=combined_input,
            config=config
        )

    else:

        config_kwargs["system_instruction"] = system_prompt

        config = genai_types.GenerateContentConfig(
            **config_kwargs
        )

        response = client.models.generate_content(
            model=model_id,
            contents=user_content,
            config=config
        )

    if not response:
        raise RuntimeError(
            f"Model {model_id} returned no response."
        )

    text = getattr(response, "text", None)

    if not text:
        raise RuntimeError(
            f"Model {model_id} returned an empty response."
        )

    return text


# =============================================================================
# INITIAL SESSION STATE
# =============================================================================

if "show_user_guide" not in st.session_state:
    st.session_state.show_user_guide = False

if "groq_synthesis" not in st.session_state:
    st.session_state.groq_synthesis = ""

if "report_ready" not in st.session_state:
    st.session_state.report_ready = False

if "final_graph_elements" not in st.session_state:
    st.session_state.final_graph_elements = []


# =============================================================================
# PAGE CONFIGURATION
# =============================================================================

st.set_page_config(
    page_title=f"SIS Universal Knowledge Synthesizer - {SYSTEM_DATE}",
    page_icon="🌳",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =============================================================================
# CSS
# =============================================================================

st.markdown(
    """
<style>

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
    text-decoration: none !important;
}

.semantic-node-highlight:hover {
    background-color: #ccfbf1;
    color: #264653;
}

.google-icon {
    font-size: 0.75em;
    vertical-align: super;
    margin-left: 2px;
    color: #457b9d;
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
}

.mental-approach-box {
    padding: 25px;
    border-radius: 15px;
    background-color: #f0f7ff;
    border-left: 8px solid #6366f1;
    margin-bottom: 30px;
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
}

.sidebar-logo-container {
    display: flex;
    justify-content: center;
    padding: 10px 0;
    margin-bottom: 5px;
}

.stButton > button {
    width: 100%;
    border-radius: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
}

</style>
""",
    unsafe_allow_html=True
)


# =============================================================================
# LOGO
# =============================================================================

def get_svg_base64(svg_str):
    return base64.b64encode(
        svg_str.encode("utf-8")
    ).decode("utf-8")


SVG_3D_RELIEF = """
<svg width="240" height="240" viewBox="0 0 240 240"
xmlns="http://www.w3.org/2000/svg">

<defs>

<filter id="reliefShadow"
x="-20%" y="-20%" width="150%" height="150%">

<feDropShadow
dx="4"
dy="4"
stdDeviation="3"
flood-color="#000"
flood-opacity="0.4"/>

</filter>

<linearGradient
id="pyramidSide"
x1="0%"
y1="0%"
x2="100%"
y2="100%">

<stop offset="0%"
style="stop-color:#e0e0e0;stop-opacity:1"/>

<stop offset="100%"
style="stop-color:#bdbdbd;stop-opacity:1"/>

</linearGradient>

<linearGradient
id="treeGrad"
x1="0%"
y1="0%"
x2="0%"
y2="100%">

<stop offset="0%"
style="stop-color:#66bb6a;stop-opacity:1"/>

<stop offset="100%"
style="stop-color:#2e7d32;stop-opacity:1"/>

</linearGradient>

</defs>

<circle
cx="120"
cy="120"
r="100"
fill="#f0f0f0"
stroke="#000000"
stroke-width="4"
filter="url(#reliefShadow)" />

<path
d="M120 40 L50 180 L120 200 Z"
fill="url(#pyramidSide)" />

<path
d="M120 40 L190 180 L120 200 Z"
fill="#9e9e9e" />

<rect
x="116"
y="110"
width="8"
height="70"
rx="2"
fill="#5d4037" />

<circle
cx="120"
cy="85"
r="30"
fill="url(#treeGrad)"
filter="url(#reliefShadow)" />

<circle
cx="95"
cy="125"
r="22"
fill="#43a047"
filter="url(#reliefShadow)" />

<circle
cx="145"
cy="125"
r="22"
fill="#43a047"
filter="url(#reliefShadow)" />

<rect
x="70"
y="170"
width="20"
height="12"
rx="2"
fill="#1565c0"
filter="url(#reliefShadow)" />

<rect
x="150"
y="170"
width="20"
height="12"
rx="2"
fill="#c62828"
filter="url(#reliefShadow)" />

<rect
x="110"
y="185"
width="20"
height="12"
rx="2"
fill="#f9a825"
filter="url(#reliefShadow)" />

</svg>
"""


# =============================================================================
# CYTOSCAPE ENGINE
# =============================================================================

def render_cytoscape_network(
    elements,
    layout_type="organic",
    container_id="cy_canvas"
):

    layout_configs = {

        "organic": """
        {
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
        }
        """,

        "hierarchical": """
        {
            name: 'breadthfirst',
            directed: true,
            padding: 50,
            circle: false,
            spacingFactor: 1.75,
            maximal: true
        }
        """,

        "circular": """
        {
            name: 'circle',
            padding: 50,
            radius: 400,
            spacingFactor: 0.8
        }
        """,

        "concentric": """
        {
            name: 'concentric',
            minNodeSpacing: 60,
            concentric: function(node){
                return node.data('size');
            },
            levelWidth: function(nodes){
                return 10;
            },
            padding: 50
        }
        """,

        "grid": """
        {
            name: 'grid',
            rows: 5,
            padding: 50,
            spacingFactor: 1.2
        }
        """
    }

    selected_layout = layout_configs.get(
        layout_type,
        layout_configs["organic"]
    )

    safe_elements = json.dumps(
        elements,
        ensure_ascii=False
    )

    cyto_html = f"""
<div style="position:relative;width:100%;">

<button id="save_btn_{container_id}"
style="
position:absolute;
top:15px;
right:15px;
z-index:1000;
padding:10px 15px;
background:#1d3557;
color:white;
border:none;
border-radius:8px;
cursor:pointer;
font-family:sans-serif;
font-size:12px;
font-weight:800;">
💾 EXPORT {layout_type.upper()} PNG
</button>

<div id="{container_id}"
style="
width:100%;
height:850px;
background:#ffffff;
border-radius:20px;
border:1px solid #e0e0e0;">
</div>

</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.26.0/cytoscape.min.js"></script>

<script>

document.addEventListener(
'DOMContentLoaded',
function() {{

var container =
document.getElementById('{container_id}');

if (!container) return;

var cy = cytoscape({{

container: container,

elements: {safe_elements},

style: [

{{
selector:'node',
style:{{
'label':'data(label)',
'text-valign':'center',
'text-halign':'center',
'color':'#1d3557',
'background-color':'data(color)',
'width':'data(size)',
'height':'data(size)',
'shape':'data(shape)',
'font-size':'12px',
'font-weight':'bold',
'text-wrap':'wrap',
'text-max-width':'80px',
'border-width':3,
'border-color':'#ffffff',
'text-outline-color':'#ffffff',
'text-outline-width':2
}}
}},

{{
selector:'edge',
style:{{
'width':2,
'line-color':'data(color)',
'label':'data(rel_type)',
'font-size':'9px',
'font-weight':'bold',
'color':'#2a9d8f',
'curve-style':'unbundled-bezier',
'control-point-step-size':40,
'target-arrow-color':'data(color)',
'target-arrow-shape':'vee',
'text-background-opacity':1,
'text-background-color':'#ffffff',
'text-background-padding':'3px',
'opacity':0.8
}}
}},

{{
selector:'edge[rel_type="Generalization"]',
style:{{
'target-arrow-shape':'triangle',
'target-arrow-fill':'hollow',
'width':3
}}
}},

{{
selector:'edge[rel_type="Realization"]',
style:{{
'line-style':'dashed',
'target-arrow-shape':'triangle',
'target-arrow-fill':'hollow'
}}
}},

{{
selector:'edge[rel_type="Composition"]',
style:{{
'source-arrow-shape':'diamond',
'source-arrow-fill':'filled',
'width':4
}}
}},

{{
selector:'edge[rel_type="Aggregation"]',
style:{{
'source-arrow-shape':'diamond',
'source-arrow-fill':'hollow',
'width':3
}}
}},

{{
selector:'edge[rel_type="Dependency"]',
style:{{
'line-style':'dashed',
'target-arrow-shape':'vee'
}}
}},

{{
selector:'edge[rel_type="Conflict"]',
style:{{
'width':6,
'line-color':'#b91d1d',
'target-arrow-color':'#b91d1d',
'target-arrow-shape':'triangle-cross',
'source-arrow-shape':'triangle-cross'
}}
}},

{{
selector:'edge[rel_type="Specialization"]',
style:{{
'line-style':'dashed',
'line-color':'#000000',
'target-arrow-shape':'triangle',
'target-arrow-color':'#000000'
}}
}},

{{
selector:'edge[rel_type="Containment"]',
style:{{
'line-color':'#1d3557',
'target-arrow-shape':'circle',
'target-arrow-color':'#1d3557',
'target-arrow-fill':'hollow',
'width':4
}}
}},

{{
selector:'edge[rel_type="TT"]',
style:{{
'width':6,
'line-color':'#1d3557'
}}
}},

{{
selector:'edge[rel_type="BT"]',
style:{{
'width':4,
'line-color':'#1d3557'
}}
}},

{{
selector:'edge[rel_type="NT"]',
style:{{
'width':4,
'line-color':'#1d3557'
}}
}},

{{
selector:'edge[rel_type="EQ"]',
style:{{
'width':5,
'line-color':'#f1c40f'
}}
}},

{{
selector:'edge[rel_type="RT"]',
style:{{
'line-style':'dotted',
'width':2,
'line-color':'#2a9d8f',
'target-arrow-shape':'none'
}}
}},

{{
selector:'edge[rel_type="AS"]',
style:{{
'line-style':'dashed',
'width':2,
'line-color':'#7b2cb1'
}}
}},

{{
selector:'edge[rel_type="IN"]',
style:{{
'line-style':'dotted',
'width':3,
'line-color':'#0077b6',
'target-arrow-shape':'triangle'
}}
}},

{{
selector:'edge[rel_type="AND"]',
style:{{
'width':5,
'line-color':'#00FF00',
'target-arrow-color':'#00FF00',
'target-arrow-shape':'triangle'
}}
}},

{{
selector:'edge[rel_type="OR"]',
style:{{
'width':3,
'line-color':'#00BFFF',
'line-style':'dashed',
'target-arrow-color':'#00BFFF',
'target-arrow-shape':'vee'
}}
}},

{{
selector:'edge[rel_type="XOR"]',
style:{{
'width':4,
'line-color':'#FF8C00',
'line-style':'double',
'target-arrow-color':'#FF8C00',
'target-arrow-shape':'diamond'
}}
}},

{{
selector:'edge[rel_type="NOT"]',
style:{{
'width':4,
'line-color':'#FF0000',
'line-style':'dashed',
'target-arrow-color':'#FF0000',
'target-arrow-shape':'tee'
}}
}},

{{
selector:'edge[rel_type="IF-THEN"]',
style:{{
'width':4,
'line-color':'#FFD700',
'target-arrow-color':'#FFD700',
'target-arrow-shape':'triangle',
'arrow-scale':1.3
}}
}},

{{
selector:'node[shape="star"]',
style:{{
'font-size':'16px',
'width':130,
'height':130,
'border-width':5,
'border-color':'#FFD700'
}}
}}

],

layout:{selected_layout}

}});

var saveButton =
document.getElementById(
'save_btn_{container_id}'
);

if (saveButton) {{

saveButton.addEventListener(
'click',
function() {{

var png64 = cy.png({{
full:true,
bg:'white',
scale:2
}});

var link =
document.createElement('a');

var timestamp =
new Date()
.toISOString()
.replace(/[:.]/g,'-')
.slice(0,19);

link.href = png64;

link.download =
'hierarchograph_{layout_type}_'
+ timestamp
+ '.png';

link.click();

}}
);

}}

}}
);

</script>
"""

    components.html(
        cyto_html,
        height=900
    )


# =============================================================================
# ORCID
# =============================================================================

def fetch_author_bibliographies(author_input):

    if not author_input:
        return ""

    author_list = [
        a.strip()
        for a in author_input.split(",")
        if a.strip()
    ]

    comprehensive_biblio = ""

    headers = {
        "Accept": "application/json"
    }

    for auth in author_list:

        try:

            search_url = (
                "https://pub.orcid.org/v3.0/search/?q="
                + urllib.parse.quote(auth)
            )

            s_res = requests.get(
                search_url,
                headers=headers,
                timeout=10
            ).json()

            if not s_res.get("result"):
                continue

            orcid_id = (
                s_res["result"][0]
                ["orcid-identifier"]
                ["path"]
            )

            record_url = (
                f"https://pub.orcid.org/v3.0/"
                f"{orcid_id}/record"
            )

            r_res = requests.get(
                record_url,
                headers=headers,
                timeout=10
            ).json()

            works = (
                r_res
                .get("activities-summary", {})
                .get("works", {})
                .get("group", [])
            )

            comprehensive_biblio += (
                f"#### 🆔 ORCID: {auth.upper()} "
                f"({orcid_id})\n"
            )

            for work in works[:12]:

                summary = work.get(
                    "work-summary",
                    [{}]
                )[0]

                title = (
                    summary
                    .get("title", {})
                    .get("title", {})
                    .get("value", "Unknown Title")
                )

                pub_date = summary.get(
                    "publication-date"
                )

                year = (
                    pub_date
                    .get("year", {})
                    .get("value", "n.d.")
                    if pub_date
                    else "n.d."
                )

                comprehensive_biblio += (
                    f"- **{year}**: {title}\n"
                )

            comprehensive_biblio += "\n---\n"

        except Exception:
            continue

    return comprehensive_biblio


# =============================================================================
# HUMAN THINKING METAMODEL
# =============================================================================

HUMAN_THINKING_METAMODEL = {

    "nodes": {

        "Human mental concentration": {
            "color": "#ADB5BD",
            "shape": "rectangle",
            "desc": "The foundational state of cognitive focus required for interdisciplinary synthesis and logical rigor."
        },

        "Identity": {
            "color": "#C6EFCE",
            "shape": "rectangle",
            "desc": "The subjective core of the researcher or agent."
        },

        "Autobiographical memory": {
            "color": "#C6EFCE",
            "shape": "rectangle",
            "desc": "The historical database of past cycles influencing current logic."
        },

        "Mission": {
            "color": "#92D050",
            "shape": "rectangle",
            "desc": "The high-level imperative driving inquiry."
        },

        "Vision": {
            "color": "#FFFF00",
            "shape": "rectangle",
            "desc": "Mental simulation of a desired future outcome."
        },

        "Goal": {
            "color": "#00B0F0",
            "shape": "rectangle",
            "desc": "Quantifiable milestone materializing the mission."
        },

        "Problem": {
            "color": "#F2DCDB",
            "shape": "rectangle",
            "desc": "Obstruction preventing goal realization."
        },

        "Ethics/moral": {
            "color": "#FFC000",
            "shape": "rectangle",
            "desc": "Value system filtering solution validity."
        },

        "Hierarchy of interests": {
            "color": "#F8CBAD",
            "shape": "rectangle",
            "desc": "Ordering of needs dictating resource allocation."
        },

        "Rule": {
            "color": "#F2F2F2",
            "shape": "rectangle",
            "desc": "Structural, logical, and legal constraints."
        },

        "Decision-making": {
            "color": "#FFFF99",
            "shape": "rectangle",
            "desc": "Choosing efficient selection pathways."
        },

        "Problem solving": {
            "color": "#D9D9D9",
            "shape": "rectangle",
            "desc": "Algorithmic process removing obstructions."
        },

        "Conflict situation": {
            "color": "#00FF00",
            "shape": "rectangle",
            "desc": "State where goals or rules clash."
        },

        "Knowledge": {
            "color": "#DDEBF7",
            "shape": "rectangle",
            "desc": "Internalized facts and theoretical models."
        },

        "Tool": {
            "color": "#00B050",
            "shape": "rectangle",
            "desc": "External instrument leveraged to interact with the domain."
        },

        "Experience": {
            "color": "#00B050",
            "shape": "rectangle",
            "desc": "Wisdom gained through direct application of knowledge."
        },

        "Classification": {
            "color": "#CCC0DA",
            "shape": "rectangle",
            "desc": "Taxonomic act reducing cognitive load."
        },

        "Psychological aspect": {
            "color": "#F8CBAD",
            "shape": "rectangle",
            "desc": "Internal outcomes on individual mental states."
        },

        "Sociological aspect": {
            "color": "#00FFFF",
            "shape": "rectangle",
            "desc": "External collective impact and social changes."
        },

        "Hierarchical Associative System": {
            "color": "#fd7e14",
            "shape": "ellipse",
            "desc": "Primary cognitive framework defined by hierarchology."
        },

        "Scientific Cage": {
            "color": "#6c757d",
            "shape": "rectangle",
            "desc": "Boundary of human mental perspective."
        },

        "Hierarchography": {
            "color": "#e63946",
            "shape": "diamond",
            "desc": "Visual description of hierarchical structures."
        }
    },

    "relations": [
        ("Human mental concentration", "Identity", "has"),
        ("Identity", "Autobiographical memory", "possesses"),
        ("Mission", "Vision", "defines"),
        ("Vision", "Goal", "leads to"),
        ("Problem", "Identity", "challenges"),
        ("Rule", "Decision-making", "constrains"),
        ("Knowledge", "Classification", "organizes"),
        ("Experience", "Psychological aspect", "forms"),
        ("Conflict situation", "Sociological aspect", "triggers")
    ]
}


# =============================================================================
# MENTAL APPROACHES
# =============================================================================

MENTAL_APPROACHES_ONTOLOGY = {

    "nodes": {

        "Perspective shifting": {
            "color": "#00FF00",
            "shape": "diamond",
            "desc": "Rotating problem space through disparate stakeholders."
        },

        "Similarity and difference": {
            "color": "#FFFF00",
            "shape": "diamond",
            "desc": "Pattern recognition identifying similarities and anomalies."
        },

        "Core": {
            "color": "#FFC000",
            "shape": "diamond",
            "desc": "Distillation of a problem into fundamental essence."
        },

        "Attraction": {
            "color": "#F2A6A2",
            "shape": "diamond",
            "desc": "Force drawing disparate concepts into synthesis."
        },

        "Repulsion": {
            "color": "#D9D9D9",
            "shape": "diamond",
            "desc": "Isolation of incompatible solutions or noise."
        },

        "Condensation": {
            "color": "#CCC0DA",
            "shape": "diamond",
            "desc": "Reduction of complexity into strategic insight."
        },

        "Framework and foundation": {
            "color": "#F8CBAD",
            "shape": "diamond",
            "desc": "Establishing boundaries for innovation logic."
        },

        "Bipolarity and dialectics": {
            "color": "#DDEBF7",
            "shape": "diamond",
            "desc": "Synthesis through opposing tension."
        },

        "Constant": {
            "color": "#E1C1D1",
            "shape": "diamond",
            "desc": "Identifying stable system invariants."
        },

        "Associativity": {
            "color": "#E1C1D1",
            "shape": "diamond",
            "desc": "Non-linear lateral knowledge linking."
        },

        "Induction": {
            "color": "#B4C6E7",
            "shape": "diamond",
            "desc": "Building broad theory from observations."
        },

        "Whole and part": {
            "color": "#00FF00",
            "shape": "diamond",
            "desc": "Holistic versus granular navigation."
        },

        "Mini-max": {
            "color": "#00FF00",
            "shape": "diamond",
            "desc": "Maximum utility with minimum friction."
        },

        "Addition and composition": {
            "color": "#FF00FF",
            "shape": "diamond",
            "desc": "Building complexity through layering."
        },

        "Hierarchy": {
            "color": "#C6EFCE",
            "shape": "diamond",
            "desc": "Vertical taxonomic ranking."
        },

        "Balance": {
            "color": "#00B0F0",
            "shape": "diamond",
            "desc": "Search for dynamic equilibrium."
        },

        "Deduction": {
            "color": "#92D050",
            "shape": "diamond",
            "desc": "Applying broad laws to specifics."
        },

        "Abstraction and elimination": {
            "color": "#00B0F0",
            "shape": "diamond",
            "desc": "Removing noise to reach a generic model."
        },

        "Pleasure and displeasure": {
            "color": "#00FF00",
            "shape": "diamond",
            "desc": "Evaluative feedback on solution elegance."
        },

        "Openness and closedness": {
            "color": "#FFC000",
            "shape": "diamond",
            "desc": "System boundary state governing external data."
        }
    }
}


# =============================================================================
# HIERARCHOLOGY
# =============================================================================

HIERARCHOLOGY_ONTOLOGY = {

    "core_definitions": {

        "Hierarchology":
            "Interdisciplinary science studying hierarchical associative systems (Micro, Meso, Macro).",

        "Hierarchography":
            "Descriptive outlining of systems using workflows, tree maps, and structural diagrams.",

        "Scientific Cage":
            "Cognitive limitations preventing thought beyond established paradigms."
    },

    "hierarchical_levels": {

        "Micro-hierarchology":
            "Internal individual thinking and neural inductive communication.",

        "Meso-hierarchology":
            "Intermediate social groups and organizational associative structures.",

        "Macro-hierarchology":
            "Fundamental social laws and universal natural hierarchies."
    },

    "operational_logic": {

        "Internal Processes":
            "Inductive (building from specific neural/local signals to patterns).",

        "External Functioning":
            "Deductive & Dialectical (applying general laws to specific social behaviors)."
    },

    "hierarchography_tools": [
        "Workflow Mapping",
        "Tree Maps",
        "Oligographs",
        "UML Modeling",
        "Mind Mapping",
        "Cognitive Modeling"
    ]
}


# =============================================================================
# KNOWLEDGE BASE
# =============================================================================

KNOWLEDGE_BASE = {

    "User profiles": {

        "Adventurers": {
            "description":
                "Explorers of hidden interdisciplinary patterns and high-risk hypotheses."
        },

        "Applicators": {
            "description":
                "Focused on practical efficiency and rapid deployment."
        },

        "Know-it-alls": {
            "description":
                "Seekers of systemic clarity, taxonomy, and complete data."
        },

        "Observers": {
            "description":
                "Passive monitors of systemic dynamics and trend watchers."
        }
    },

    "Scientific paradigms": {

        "Empiricism":
            "Focus on sensory experience, experimental evidence, and observation-driven data.",

        "Rationalism":
            "Reliance on deductive logic, a priori reasoning, and mathematical certainty.",

        "Constructivism":
            "Knowledge as a social and cognitive build.",

        "Positivism":
            "Strict adherence to verifiable facts.",

        "Pragmatism":
            "Evaluation based on utility and real-world application.",

        "Reductionism":
            "Explaining complex phenomena through simpler fundamental parts.",

        "Holism":
            "Systems should be viewed as wholes.",

        "Systems Theory":
            "Interdisciplinary study of systems and relationships.",

        "Phenomenology":
            "Study of structures of consciousness.",

        "Falsificationism":
            "Scientific theories must be testable and refutable.",

        "Critical Theory":
            "Theory oriented toward critiquing and changing society.",

        "Hermeneutics":
            "Theory and methodology of interpretation.",

        "Relativism":
            "Truth and values depend on social and historical contexts.",

        "Structuralism":
            "Elements understood through relationships to broader systems.",

        "Post-Structuralism":
            "Emphasis on instability of meaning and systems."
    },

    "Structural models": {

        "Causal Connections":
            "Chains of cause and effect mapping systemic causality.",

        "Principles & Relations":
            "Fundamental laws and inter-relations between entities.",

        "Episodes & Sequences":
            "Temporal flow and event ordering.",

        "Facts & Characteristics":
            "Raw data properties and attributes.",

        "Generalizations":
            "Broad theoretical models.",

        "Glossary":
            "Precise definitions and terminology.",

        "Concepts":
            "Abstract constructs and conceptual building blocks."
    },

    "Science fields": {

        "Physics": {
            "cat": "Natural",
            "methods": ["Quantum Modeling", "Particle Tracking", "Simulation"],
            "tools": ["Spectrometer", "Oscilloscope"],
            "facets": ["Relativity", "Quantum Mechanics", "Thermodynamics"]
        },

        "Psychology": {
            "cat": "Social",
            "methods": ["Psychometrics", "Longitudinal Studies", "Behavioral Analysis"],
            "tools": ["Standardized Tests", "Surveys", "Biofeedback"],
            "facets": ["Behavioral", "Clinical", "Cognitive Psychology"]
        },

        "Sociology": {
            "cat": "Social",
            "methods": ["Ethnography", "Network Analysis", "Survey Design"],
            "tools": ["NVivo", "SPSS", "Social Graphs"],
            "facets": ["Demography", "Stratification", "Dynamics"]
        },

        "Mathematics": {
            "cat": "Formal",
            "methods": ["Axiomatization", "Formal Proof", "Stochastic Modeling"],
            "tools": ["MATLAB", "LaTeX"],
            "facets": ["Algebra", "Analysis", "Calculus"]
        },

        "Biology": {
            "cat": "Natural",
            "methods": ["Gene Sequencing", "Cell Culture", "In-vivo observation"],
            "tools": ["Electron Microscope", "PCR Machine"],
            "facets": ["Genetics", "Microbiology", "Ecology"]
        },

        "Neuroscience": {
            "cat": "Natural",
            "methods": ["Neuroimaging", "Behavioral Mapping", "Electrophysiology"],
            "tools": ["fMRI", "EEG"],
            "facets": ["Cognitive Neuroscience", "Neural Plasticity"]
        },

        "Computer Science": {
            "cat": "Formal",
            "methods": ["Algorithm Design", "Verification", "Complexity Analysis"],
            "tools": ["GPU Clusters", "Docker", "Compilers"],
            "facets": ["AI", "Cybersecurity", "Cloud Computing"]
        },

        "Medicine": {
            "cat": "Applied",
            "methods": ["Clinical Trials", "Epidemiology", "Radiology"],
            "tools": ["MRI", "CT Scanner", "Ultrasound"],
            "facets": ["Genomics", "Immunology", "Oncology"]
        },

        "Philosophy": {
            "cat": "Humanities",
            "methods": ["Socratic Method", "Dialectics", "Phenomenology"],
            "tools": ["Logic Mapping", "Primary Texts"],
            "facets": ["Epistemology", "Ethics", "Metaphysics"]
        },

        "Linguistics": {
            "cat": "Humanities",
            "methods": ["Corpus Analysis", "Syntactic Parsing"],
            "tools": ["Praat", "NLTK", "WordNet"],
            "facets": ["Semantics", "Phonology", "Sociolinguistics"]
        },

        "Library Science": {
            "cat": "Applied",
            "methods": ["Taxonomy", "Archival Appraisal", "Retrieval Logic"],
            "tools": ["OPAC", "Metadata Systems", "Thesauri"],
            "facets": ["Knowledge Organization", "Information Retrieval"]
        },

        "Economics": {
            "cat": "Social",
            "methods": ["Econometrics", "Game Theory", "Forecasting"],
            "tools": ["Stata", "R", "Python Pandas"],
            "facets": ["Finance", "Behavioral Economics", "Macroeconomics"]
        },

        "History": {
            "cat": "Humanities",
            "methods": ["Archival Research", "Historiography", "Oral History"],
            "tools": ["Digital Archives", "Microfilm"],
            "facets": ["Military History", "Diplomacy", "Social History"]
        },

        "Engineering": {
            "cat": "Applied",
            "methods": ["FEA Analysis", "Prototyping", "Systems Integration"],
            "tools": ["CAD", "3D Printers", "Simulation SW"],
            "facets": ["Robotics", "Nanotechnology", "Civil Engineering"]
        }
    }
}


# =============================================================================
# IDEATION TECHNIQUES
# =============================================================================

IDEATION_TECHNIQUES = {

    "Six Thinking Hats":
        "White Data, Red Emotion, Black Risk, Yellow Value, Green Creativity, Blue Control.",

    "SCAMPER":
        "Substitute, Combine, Adapt, Modify, Put to another use, Eliminate, Reverse.",

    "First Principles":
        "Deconstruct the problem into fundamental truths and rebuild from the ground up.",

    "TRIZ (Simplified)":
        "Identify contradictions and apply inventive principles.",

    "Lateral Thinking":
        "Use provocation and movement to escape established patterns.",

    "Blue Ocean Strategy":
        "Eliminate-Reduce-Raise-Create logic for new value spaces.",

    "Synectics":
        "Use direct, personal, and symbolic analogies."
}


# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:

    st.markdown(
        f"""
        <div class="sidebar-logo-container">
            <img
                src="data:image/svg+xml;base64,{get_svg_base64(SVG_3D_RELIEF)}"
                width="220">
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        f'<div class="date-badge">{SYSTEM_DATE.upper()}</div>',
        unsafe_allow_html=True
    )

    st.header("⚙️ SYSTEM CONTROL")

    st.header("⚙️ GOOGLE GEMINI SYSTEM CONTROL")

    google_api_key = st.text_input(
        "Google AI (Gemini) API Key:",
        type="password",
        key="side_google_v2026",
        help="Google AI Studio API key."
    )

    st.header("🤗 HUGGING FACE SYSTEM CONTROL")

    huggingface_api_key = st.text_input(
        "Hugging Face API Key:",
        type="password",
        key="side_huggingface_v2026",
        help=(
            "Fine-grained token with "
            "'Make calls to Inference Providers' permission."
        )
    )

    st.caption(
        "🤗 Qwen2.5-72B-Instruct → Hugging Face Inference Providers"
    )

    st.subheader("🤖 Sequential Model Selection")

    p1_label = st.selectbox(
        "Phase 1 Model (Structure):",
        GEMINI_MODEL_LABELS,
        index=1,
        key="p1_model_selector"
    )

    p1_model = GEMINI_MODEL_CATALOG[p1_label]

    p2_label = st.selectbox(
        "Phase 2 Model (Innovation):",
        GEMINI_MODEL_LABELS,
        index=0,
        key="p2_model_selector"
    )

    p2_model = GEMINI_MODEL_CATALOG[p2_label]

    st.divider()

    st.subheader("🎨 GRAPH PERSPECTIVE")

    graph_perspective = st.selectbox(
        "Select Visual Layout Engine:",
        [
            "organic",
            "hierarchical",
            "circular",
            "concentric",
            "grid"
        ],
        index=0,
        format_func=lambda x:
            x.capitalize() + " View",
        key="side_graph_layout_v2026"
    )

    st.divider()

    col_res, col_gui = st.columns(2)

    with col_res:

        if st.button(
            "♻️ RESET",
            key="sidebar_reset_btn_unique"
        ):

            st.session_state.clear()
            st.rerun()

    with col_gui:

        if st.button(
            "📖 GUIDE",
            key="sidebar_guide_btn_unique"
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
        key="side_git_link"
    )

    st.link_button(
        "🆔 ORCID Registry",
        "https://orcid.org/",
        use_container_width=True,
        key="side_orcid_link"
    )

    st.link_button(
        "🎓 Google Scholar",
        "https://scholar.google.com/",
        use_container_width=True,
        key="side_scholar_link"
    )

    st.divider()

    st.subheader("📚 KNOWLEDGE EXPLORER")

    with st.expander(
        "👤 User Profile Ontologies",
        expanded=False
    ):

        for p, d in KNOWLEDGE_BASE[
            "User profiles"
        ].items():

            st.markdown(
                f"**{p}**: {d['description']}"
            )

    with st.expander(
        "🧠 Mental Approach (MA) Map",
        expanded=False
    ):

        for m, d in MENTAL_APPROACHES_ONTOLOGY[
            "nodes"
        ].items():

            st.markdown(
                f"• **{m}**: {d['desc']}"
            )

    with st.expander(
        "🏛️ Metamodel (IMA) Structures",
        expanded=False
    ):

        for n, d in HUMAN_THINKING_METAMODEL[
            "nodes"
        ].items():

            st.markdown(
                f"• **{n}**: {d['desc']}"
            )

    with st.expander(
        "📐 Hierarchology & Hierarchography",
        expanded=False
    ):

        st.markdown("**Core Concepts:**")

        for key, val in HIERARCHOLOGY_ONTOLOGY[
            "core_definitions"
        ].items():

            st.markdown(
                f"• **{key}**: {val}"
            )

        st.markdown("---")

        st.markdown(
            "• ⬛ ┄ ➤ **Specialization**: "
            "Deductive derivation from general to specific."
        )

        st.markdown(
            "• 🟦 — ◯ **Containment**: "
            "Strong structural inclusion."
        )

    with st.expander(
        "🔬 Science Taxonomy & Levels",
        expanded=False
    ):

        st.markdown("**Field Domains:**")

        for s in sorted(
            KNOWLEDGE_BASE["Science fields"].keys()
        ):

            st.markdown(
                f"• **{s}**"
            )

        st.markdown("---")

        st.markdown("**Hierarchical Levels:**")

        for level, desc in HIERARCHOLOGY_ONTOLOGY[
            "hierarchical_levels"
        ].items():

            st.markdown(
                f"• **{level}**: {desc}"
            )

    with st.expander(
        "🏗️ Structural Model Context",
        expanded=False
    ):

        for m, d in KNOWLEDGE_BASE[
            "Structural models"
        ].items():

            st.markdown(
                f"**{m}**: {d}"
            )


# =============================================================================
# MAIN PAGE
# =============================================================================

st.markdown(
    '<h1 class="main-header-gradient">'
    '🧱 SIS Universal Knowledge Synthesizer'
    '</h1>',
    unsafe_allow_html=True
)

st.markdown(
    f"**Sequential Multi-Engine Pipeline** | "
    f"Current Operating Date: **{SYSTEM_DATE}**"
)


if st.session_state.show_user_guide:

    st.info(
        """
        **Sequential Synergy Pipeline**

        1. Enter Google and/or Hugging Face API keys.
        2. Select a Phase 1 structural model.
        3. Select a Phase 2 innovation model.
        4. Submit the research inquiry.
        5. Phase 1 builds the structural foundation.
        6. Phase 2 generates strategic innovations.
        7. The final semantic graph is rendered in five layouts.
        """
    )


# =============================================================================
# ARCHITECTURE BOXES
# =============================================================================

col_ref1, col_ref2 = st.columns(2)

with col_ref1:

    st.markdown(
        """
        <div class="metamodel-box">
        <b>🏛️ Phase 1: IMA Architecture</b><br>
        Structural reasoning building the factual foundation.
        Focus: Identity, Mission, Problem and hierarchy.
        </div>
        """,
        unsafe_allow_html=True
    )

with col_ref2:

    st.markdown(
        """
        <div class="mental-approach-box">
        <b>🧠 Phase 2: MA Architecture</b><br>
        Cognitive transformation generating innovative solutions.
        Focus: Dialectics, Perspective, Induction and synthesis.
        </div>
        """,
        unsafe_allow_html=True
    )


# =============================================================================
# CONFIGURATION
# =============================================================================

st.markdown(
    "### 🛠️ CONFIGURE SYNERGY PIPELINE"
)

r1c1, r1c2, r1c3 = st.columns(
    [1.5, 2, 1]
)

with r1c1:

    target_authors = st.text_input(
        "👤 Authors for ORCID Analysis:",
        placeholder=(
            "Karl Petrič, Samo Kralj, Teodor Petrič"
        )
    )

with r1c2:

    sel_sciences = st.multiselect(
        "2. Select Science Fields:",
        sorted(
            KNOWLEDGE_BASE[
                "Science fields"
            ].keys()
        ),
        default=[
            "Physics",
            "Psychology",
            "Sociology"
        ]
    )

with r1c3:

    expertise = st.select_slider(
        "3. Expertise Level:",
        [
            "Novice",
            "Intermediate",
            "Expert"
        ],
        value="Expert"
    )


r2c1, r2c2, r2c3 = st.columns(3)

with r2c1:

    sel_paradigms = st.multiselect(
        "4. Scientific Paradigms:",
        list(
            KNOWLEDGE_BASE[
                "Scientific paradigms"
            ].keys()
        ),
        default=["Rationalism"]
    )

with r2c2:

    sel_models = st.multiselect(
        "5. Structural Models:",
        list(
            KNOWLEDGE_BASE[
                "Structural models"
            ].keys()
        ),
        default=["Concepts"]
    )

with r2c3:

    goal_context = st.selectbox(
        "6. Strategic Project Goal:",
        [
            "Scientific Research",
            "Problem Solving",
            "Educational",
            "Policy Making"
        ]
    )


st.divider()


# =============================================================================
# INNOVATION STRATEGY
# =============================================================================

st.markdown(
    "### 🧬 INNOVATION STRATEGY"
)

selected_techniques = st.multiselect(
    "Select Strategic Ideation Frameworks:",
    options=list(
        IDEATION_TECHNIQUES.keys()
    ),
    default=["Six Thinking Hats"]
)

if not selected_techniques:

    st.warning(
        "⚠️ Please select at least one technique."
    )

else:

    combined_desc = " | ".join(
        [
            f"**{t}**: {IDEATION_TECHNIQUES[t]}"
            for t in selected_techniques
        ]
    )

    st.info(
        f"**Active Hybrid Strategy:** {combined_desc}"
    )


st.divider()


# =============================================================================
# USER INPUT
# =============================================================================

col_inq1, col_inq2, col_inq3 = st.columns(
    [2, 2, 1]
)

with col_inq1:

    user_query = st.text_area(
        "❓ STEP 1: Research Inquiry:",
        placeholder=(
            "Fact-based foundational inquiry..."
        ),
        height=200
    )

with col_inq2:

    idea_query = st.text_area(
        "💡 STEP 2: Innovation Prompt:",
        placeholder=(
            "Targets for innovative idea production..."
        ),
        height=200
    )

with col_inq3:

    uploaded_file = st.file_uploader(
        "📂 ATTACH DATA (.txt only):",
        type=["txt"],
        key="final_file_uploader_v2"
    )

    file_content = ""

    if uploaded_file is not None:

        try:

            file_content = (
                uploaded_file
                .read()
                .decode("utf-8")
            )

            st.success(
                f"📎 {uploaded_file.name} uploaded!"
            )

            with st.expander(
                "File Preview"
            ):

                st.text(
                    file_content[:300]
                    + (
                        "..."
                        if len(file_content) > 300
                        else ""
                    )
                )

        except Exception as e:

            st.error(
                f"Error reading file: {e}"
            )


# =============================================================================
# EXECUTION ENGINE
# =============================================================================

if st.button(
    "🚀 EXECUTE MULTI-DIMENSIONAL "
    "SEQUENTIAL SYNERGY PIPELINE",
    use_container_width=True,
    key="exec_pipeline_v2026"
):

    p1_is_hf = p1_model.startswith("hf:")
    p2_is_hf = p2_model.startswith("hf:")

    google_required = (
        not p1_is_hf
        or not p2_is_hf
    )

    huggingface_required = (
        p1_is_hf
        or p2_is_hf
    )

    if google_required and not google_api_key:

        st.error(
            "❌ Google AI API key is required "
            "because a Google model is selected."
        )

        st.stop()

    if huggingface_required and not huggingface_api_key:

        st.error(
            "❌ Hugging Face API key is required "
            "because Qwen2.5-72B-Instruct is selected."
        )

        st.stop()

    if not user_query.strip():

        st.warning(
            "⚠️ Phase 1 Research Inquiry is required."
        )

        st.stop()

    if not selected_techniques:

        st.warning(
            "⚠️ Select at least one innovation technique."
        )

        st.stop()

    try:

        # =====================================================================
        # ONTOLOGICAL CONTEXT
        # =====================================================================

        ima_nodes_list = "\n".join(
            [
                f"• {node.upper()}: {data['desc']}"
                for node, data
                in HUMAN_THINKING_METAMODEL[
                    "nodes"
                ].items()
            ]
        )

        hier_core = "\n".join(
            [
                f"• {k}: {v}"
                for k, v
                in HIERARCHOLOGY_ONTOLOGY[
                    "core_definitions"
                ].items()
            ]
        )

        hier_levels = "\n".join(
            [
                f"• {level}: {desc}"
                for level, desc
                in HIERARCHOLOGY_ONTOLOGY[
                    "hierarchical_levels"
                ].items()
            ]
        )

        hier_logic = (
            "• Internal (Inductive): "
            + HIERARCHOLOGY_ONTOLOGY[
                "operational_logic"
            ]["Internal Processes"]
            + "\n"
            + "• External (Deductive/Dialectical): "
            + HIERARCHOLOGY_ONTOLOGY[
                "operational_logic"
            ]["External Functioning"]
        )

        ma_definitions = "\n".join(
            [
                f"• {ma}: {d['desc']}"
                for ma, d
                in MENTAL_APPROACHES_ONTOLOGY[
                    "nodes"
                ].items()
            ]
        )

        ma_list_for_ai = ", ".join(
            MENTAL_APPROACHES_ONTOLOGY[
                "nodes"
            ].keys()
        )

        # =====================================================================
        # ACTIVATION
        # =====================================================================

        active_context = ""

        if (
            "[ACTIVATE]" in user_query
            or (
                idea_query
                and "[ACTIVATE]" in idea_query
            )
        ):

            active_context = f"""

### FULL ONTOLOGICAL ACTIVATION

Analyze the inquiry through:

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

PARAMETERS:

Science Fields:
{", ".join(sel_sciences)}

Scientific Paradigms:
{", ".join(sel_paradigms)}

Structural Models:
{", ".join(sel_models)}

Innovation Frameworks:
{", ".join(selected_techniques)}

Expertise:
{expertise}

Goal:
{goal_context}

"""

        # =====================================================================
        # ORCID
        # =====================================================================

        with st.spinner(
            "🔍 Accessing ORCID databases..."
        ):

            biblio_data = (
                fetch_author_bibliographies(
                    target_authors
                )
                if target_authors
                else ""
            )

        file_context_str = (
            "\n\n[FILE CONTEXT]\n"
            + file_content
            if file_content
            else ""
        )

        biblio_context = (
            "\n\n[AUTHOR RESEARCH BACKGROUND]\n"
            + biblio_data
            if biblio_data
            else ""
        )

        full_ai_input = (
            active_context
            + "\n\nRESEARCH INQUIRY:\n"
            + user_query
            + file_context_str
            + biblio_context
        )

        # =====================================================================
        # GOOGLE CLIENT
        # =====================================================================

        gemini_client = None

        if google_required:

            gemini_client = genai.Client(
                api_key=google_api_key.strip()
            )

        # =====================================================================
        # PHASE 1
        # =====================================================================

        phase1_provider_name = (
            "Hugging Face / Qwen2.5-72B-Instruct"
            if p1_is_hf
            else f"Google / {p1_model}"
        )

        with st.spinner(
            f"PHASE 1: Building Architecture "
            f"with {phase1_provider_name}..."
        ):

            p1_system_prompt = """

You are the SIS Lead Hierarchologist and
Knowledge Architect.

Perform a deep structural analysis of the user's
research inquiry using the Integrated Metamodel
Architecture (IMA).

Build a rigorous factual foundation.

Identify:

1. Identity
2. Mission
3. Vision
4. Goal
5. Problem
6. Rules
7. Knowledge
8. Hierarchical relationships
9. Micro/Meso/Macro levels
10. Scientific paradigms
11. Relevant disciplines
12. Structural causal relationships

If [ACTIVATE] appears, use the complete
ontological framework supplied by the user.

Do not invent empirical evidence.

Clearly distinguish:
- established facts
- logical deductions
- hypotheses
- proposed interpretations

The output will be consumed by a second AI
innovation engine.
"""

            groq_synthesis = gemini_generate(
                gemini_client,
                p1_model,
                p1_system_prompt,
                full_ai_input,
                temperature=0.4,
                top_p=0.9,
                huggingface_api_key=huggingface_api_key
            )

            st.session_state.groq_synthesis = (
                groq_synthesis
            )

        # =====================================================================
        # PHASE 2
        # =====================================================================

        phase2_provider_name = (
            "Hugging Face / Qwen2.5-72B-Instruct"
            if p2_is_hf
            else f"Google / {p2_model}"
        )

        with st.spinner(
            f"PHASE 2: Activating 20-MA Engine "
            f"with {phase2_provider_name}..."
        ):

            p2_system_prompt = f"""

You are the SIS Lead Strategic Innovation
Architect and Hierarchographist.

Transform the Phase 1 structural foundation
into a strategic innovation report.

Use ALL 20 Mental Approaches:

{ma_definitions}

MANDATORY MENTAL APPROACHES:

{ma_list_for_ai}

ACTIVE IDEATION FRAMEWORKS:

{", ".join(selected_techniques)}

OUTPUT:

1. STRATEGIC INNOVATION REPORT
2. 3-4 major breakthroughs
3. Cross-disciplinary impact
4. Semantic graph JSON

Each innovation must explicitly identify
THREE Mental Approaches.

SEMANTIC GRAPH RELATIONS:

ISO / THESAURUS:

TT
BT
NT
RT
EQ
AS
IN

UML:

Generalization
Specialization
Containment
Realization
Composition
Aggregation
Dependency
Conflict

LOGICAL:

AND
OR
XOR
NOT
IF-THEN

GEOMETRY:

star = Goal
hexagon = Science Field
diamond = Innovation
triangle = Process
octagon = Rule
ellipse = Human/Biological
rectangle = Fact/Data

IMPORTANT JSON RULES:

Return a section:

### SEMANTIC_GRAPH_JSON

followed immediately by valid JSON.

Every description must be a single-line
string.

Do not put Markdown after the JSON.

"""

            p2_user_content = (
                "PHASE 1 FOUNDATION:\n\n"
                + groq_synthesis
                + "\n\nUSER INNOVATION GOAL:\n"
                + (
                    idea_query
                    if idea_query.strip()
                    else user_query
                )
                + file_context_str
            )

            gemini_innovation = gemini_generate(
                gemini_client,
                p2_model,
                p2_system_prompt,
                p2_user_content,
                temperature=0.85,
                top_p=0.9,
                huggingface_api_key=huggingface_api_key
            )

        # =====================================================================
        # RESULT PROCESSING
        # =====================================================================

        g_data = {
            "nodes": [],
            "edges": []
        }

        if "### SEMANTIC_GRAPH_JSON" in gemini_innovation:

            parts = gemini_innovation.split(
                "### SEMANTIC_GRAPH_JSON",
                1
            )

            innovation_text = parts[0]
            json_raw = parts[1]

        else:

            innovation_text = gemini_innovation
            json_raw = ""

        innovation_text = re.sub(
            r"```(?:json)?",
            "",
            innovation_text,
            flags=re.IGNORECASE
        ).strip()

        # =====================================================================
        # ROBUST JSON EXTRACTION
        # =====================================================================

        json_source = (
            json_raw
            if json_raw.strip()
            else gemini_innovation
        )

        json_source = re.sub(
            r"```json|```",
            "",
            json_source,
            flags=re.IGNORECASE
        ).strip()

        json_match = re.search(
            r"\{.*\}",
            json_source,
            re.DOTALL
        )

        if json_match:

            raw_json_str = json_match.group(0).strip()

            try:

                g_data = json.loads(
                    raw_json_str
                )

            except json.JSONDecodeError:

                # -------------------------------------------------------------
                # SECOND ATTEMPT: remove control characters
                # -------------------------------------------------------------

                sanitized = "".join(
                    ch
                    for ch in raw_json_str
                    if ord(ch) >= 32
                    or ch in "\n\r\t"
                )

                try:

                    g_data = json.loads(
                        sanitized
                    )

                except Exception:

                    # ---------------------------------------------------------
                    # THIRD ATTEMPT: repair common single quote output
                    # ---------------------------------------------------------

                    try:

                        repaired = (
                            sanitized
                            .replace(
                                "“",
                                '"'
                            )
                            .replace(
                                "”",
                                '"'
                            )
                        )

                        g_data = json.loads(
                            repaired
                        )

                    except Exception:

                        st.warning(
                            "⚠️ AI graph JSON could not be parsed. "
                            "The textual report remains available."
                        )

                        g_data = {
                            "nodes": [],
                            "edges": []
                        }

        # =====================================================================
        # GRAPH ELEMENTS
        # =====================================================================

        nodes_to_link = []
        final_elements = []

        valid_shapes = {
            "star",
            "diamond",
            "hexagon",
            "triangle",
            "octagon",
            "ellipse",
            "rectangle"
        }

        if isinstance(
            g_data.get("nodes"),
            list
        ):

            for index, n in enumerate(
                g_data["nodes"]
            ):

                if not isinstance(n, dict):
                    continue

                lbl = str(
                    n.get(
                        "label",
                        "Node"
                    )
                ).strip()

                if not lbl:
                    lbl = "Node"

                nid = str(
                    n.get(
                        "id",
                        f"n{index + 1}"
                    )
                )

                n_color = str(
                    n.get(
                        "color",
                        "#DDEBF7"
                    )
                )

                n_shape = str(
                    n.get(
                        "shape",
                        "rectangle"
                    )
                ).lower()

                if n_shape not in valid_shapes:
                    n_shape = "rectangle"

                if n_shape == "star":
                    n_size = 125

                elif n_shape == "diamond":
                    n_size = 110

                elif n_shape == "octagon":
                    n_size = 105

                elif n_shape == "hexagon":
                    n_size = 100

                elif n_shape == "triangle":
                    n_size = 95

                elif n_shape == "ellipse":
                    n_size = 90

                else:
                    n_size = 85

                nodes_to_link.append({
                    "id": nid,
                    "label": lbl
                })

                final_elements.append({
                    "data": {
                        "id": nid,
                        "label": lbl,
                        "color": n_color,
                        "shape": n_shape,
                        "size": n_size,
                        "description": str(
                            n.get(
                                "description",
                                "Detail breakdown in report."
                            )
                        )
                    }
                })

        # =====================================================================
        # EDGES
        # =====================================================================

        valid_relations = {
            "Generalization",
            "Realization",
            "Composition",
            "Aggregation",
            "Dependency",
            "Specialization",
            "Containment",
            "Conflict",
            "BT",
            "NT",
            "TT",
            "IN",
            "AS",
            "EQ",
            "RT",
            "AND",
            "OR",
            "XOR",
            "NOT",
            "IF-THEN"
        }

        edge_colors = {

            "Conflict": "#b91d1d",
            "Specialization": "#000000",
            "Containment": "#1D3557",
            "Generalization": "#E63946",
            "Realization": "#E63946",

            "BT": "#1D3557",
            "NT": "#1D3557",
            "TT": "#1D3557",

            "IN": "#0077B6",
            "AS": "#7B2CB1",
            "EQ": "#F1C40F",
            "RT": "#2A9D8F",

            "AND": "#00FF00",
            "OR": "#00BFFF",
            "XOR": "#FF8C00",
            "NOT": "#FF0000",
            "IF-THEN": "#FFD700"
        }

        if isinstance(
            g_data.get("edges"),
            list
        ):

            for e in g_data["edges"]:

                if not isinstance(e, dict):
                    continue

                source = e.get("source")
                target = e.get("target")

                if not source or not target:
                    continue

                rel = str(
                    e.get(
                        "rel_type",
                        "Association"
                    )
                )

                if rel not in valid_relations:
                    rel = "Association"

                e_color = edge_colors.get(
                    rel,
                    "#ADB5BD"
                )

                final_elements.append({
                    "data": {
                        "source": str(source),
                        "target": str(target),
                        "rel_type": rel,
                        "color": e_color
                    }
                })

        # =====================================================================
        # REPORT
        # =====================================================================

        full_report = (
            f"## 📚 Phase 1: Structural Foundation "
            f"({phase1_provider_name})\n\n"
            f"{groq_synthesis}\n\n"
            f"---\n\n"
            f"## 💡 Phase 2: Strategic Innovations "
            f"({phase2_provider_name})\n\n"
            f"{innovation_text}"
        )

        final_interactive_report = full_report

        if nodes_to_link:

            sorted_keywords = sorted(
                nodes_to_link,
                key=lambda x:
                len(x["label"]),
                reverse=True
            )

            for item in sorted_keywords:

                lbl = item["label"]

                if len(lbl) <= 2:
                    continue

                g_url = urllib.parse.quote(
                    lbl
                )

                link_html = (
                    f'<a href='
                    f'"https://www.google.com/search?q={g_url}" '
                    f'target="_blank" '
                    f'class="semantic-node-highlight">'
                    f'{lbl}'
                    f'<i class="google-icon">↗</i>'
                    f'</a>'
                )

                pattern = re.compile(
                    rf"(?<!\w){re.escape(lbl)}(?!\w)",
                    re.IGNORECASE |
                    re.UNICODE
                )

                final_interactive_report = (
                    pattern.sub(
                        link_html,
                        final_interactive_report,
                        count=1
                    )
                )

        # =====================================================================
        # DISPLAY
        # =====================================================================

        st.subheader(
            "🧱 INTEGRATED HIERARCHOLOGICAL REPORT"
        )

        if biblio_data:

            with st.expander(
                "📚 EXTRACTED AUTHOR BACKGROUND",
                expanded=False
            ):

                st.markdown(
                    biblio_data
                )

        st.markdown(
            final_interactive_report,
            unsafe_allow_html=True
        )

        # =====================================================================
        # INNOVATION DEEP DIVE
        # =====================================================================

        if final_elements:

            st.divider()

            st.markdown(
                "### 🚀 STRATEGIC INNOVATION DEEP-DIVE"
            )

            st.info(
                "Strategic breakthroughs synthesized "
                "from the multidimensional analysis."
            )

            innovations = [
                n["data"]
                for n in final_elements
                if n["data"].get(
                    "shape"
                ) == "diamond"
            ]

            if innovations:

                for inv in innovations:

                    g_url = urllib.parse.quote(
                        inv["label"]
                    )

                    detailed_desc = inv.get(
                        "description",
                        "Detailed strategic analysis "
                        "is available above."
                    )

                    st.markdown(
                        f"""
<div style="
background:#ffffff;
border-left:6px solid #fd7e14;
padding:25px;
border-radius:15px;
border:1px solid #eee;
margin-bottom:25px;
">

<div style="
display:flex;
justify-content:space-between;
align-items:center;
margin-bottom:10px;
">

<span style="
background:#fff4ed;
color:#fd7e14;
padding:5px 12px;
border-radius:20px;
font-size:0.75em;
font-weight:800;
text-transform:uppercase;
">
Strategic Breakthrough
</span>

<a
href="https://www.google.com/search?q={g_url}"
target="_blank"
style="
text-decoration:none;
color:#457b9d;
font-size:0.85em;
font-weight:600;
">
Technical Search ↗
</a>

</div>

<h2 style="
margin:0 0 15px 0;
color:#1d3557;
">
{inv["label"]}
</h2>

<div style="
color:#333;
font-size:1.05em;
line-height:1.7;
border-top:1px solid #f0f0f0;
padding-top:15px;
">
{detailed_desc}
</div>

</div>
""",
                        unsafe_allow_html=True
                    )

            else:

                st.warning(
                    "No Diamond innovation nodes were found."
                )

            # =================================================================
            # LEGEND
            # =================================================================

            st.markdown(
                """
<div style="
font-size:0.78em;
color:#444;
background:#ffffff;
padding:15px 25px;
border-radius:15px;
border:1px solid #e9ecef;
margin-top:30px;
">

<b style="color:#1d3557;">
NODES:
</b>
⭐ Goal |
⬢ Domain |
💠 Innovation |
△ Process |
▭ Data |
⬣ Rule |
⭔ Human/Bio

<br><br>

<b style="color:#1d3557;">
SEMANTIC LAYERS:
</b>

⬤ Hierarchical |
⬤ Associative |
⬤ Related |
⬤ Equivalence

</div>
""",
                unsafe_allow_html=True
            )

            # ================================================================
            # GRAPH
            # ================================================================

            st.subheader(
                "🕸️ HYBRID SEMANTIC SYSTEM MAP "
                f"({graph_perspective.upper()} VIEW)"
            )

            render_cytoscape_network(
                final_elements,
                layout_type=graph_perspective,
                container_id=(
                    f"cy_{int(time.time())}"
                )
            )

            st.session_state.final_graph_elements = (
                final_elements
            )

            st.session_state.report_ready = True

    except Exception as e:

        st.error(
            "❌ Pipeline Failure"
        )

        st.exception(e)


# =============================================================================
# MULTI-PERSPECTIVE GRAPH GALLERY
# =============================================================================

if (
    st.session_state.get("report_ready")
    and st.session_state.get(
        "final_graph_elements"
    )
):

    st.divider()

    st.markdown(
        """
        <h2 style="
        color:#1d3557;
        text-align:center;">
        🖼️ MULTI-PERSPECTIVE GRAPH GALLERY
        </h2>
        """,
        unsafe_allow_html=True
    )

    st.info(
        "The same semantic graph can be explored "
        "through five architectural perspectives."
    )

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "🌿 ORGANIC",
            "🌲 HIERARCHICAL",
            "⭕ CIRCULAR",
            "🎯 CONCENTRIC",
            "🔲 GRID"
        ]
    )

    with tab1:

        st.markdown(
            "**Organic View:** "
            "Natural thematic clustering."
        )

        render_cytoscape_network(
            st.session_state.final_graph_elements,
            "organic",
            "gal_organic"
        )

    with tab2:

        st.markdown(
            "**Hierarchical View:** "
            "General-to-specific architecture."
        )

        render_cytoscape_network(
            st.session_state.final_graph_elements,
            "hierarchical",
            "gal_hierarchical"
        )

    with tab3:

        st.markdown(
            "**Circular View:** "
            "Relational density."
        )

        render_cytoscape_network(
            st.session_state.final_graph_elements,
            "circular",
            "gal_circular"
        )

    with tab4:

        st.markdown(
            "**Concentric View:** "
            "Systemic centrality."
        )

        render_cytoscape_network(
            st.session_state.final_graph_elements,
            "concentric",
            "gal_concentric"
        )

    with tab5:

        st.markdown(
            "**Grid View:** "
            "Structured data inspection."
        )

        render_cytoscape_network(
            st.session_state.final_graph_elements,
            "grid",
            "gal_grid"
        )


# =============================================================================
# FOOTER
# =============================================================================

st.divider()

st.caption(
    f"SIS Universal Knowledge Synthesizer | "
    f"{VERSION_CODE} | {SYSTEM_DATE}"
)
