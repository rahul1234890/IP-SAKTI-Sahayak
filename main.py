import os
import json
import re
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
from google import genai
from pypdf import PdfReader


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

ENV_FILE = BASE_DIR / ".env"

KNOWLEDGE_FILE = (
    BASE_DIR
    / "backend"
    / "knowledge_base.txt"
)

SOURCE_REGISTRY_FILE = (
    BASE_DIR
    / "database"
    / "source_registry.json"
)


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv(
    dotenv_path=ENV_FILE,
    override=True
)


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="IP-SAKTI Sahayak",
    description=(
        "AI-powered multilingual, source-grounded "
        "IP and regulatory guidance for Ayurveda."
    ),
    version="1.3.0"
)


# ============================================================
# REQUEST MODEL
# ============================================================

class QuestionRequest(BaseModel):
    question: str
    jurisdiction: str = "India"
    language: str = "English"


# ============================================================
# PRODUCT CLASSIFICATION
# ============================================================

PRODUCT_CLASSIFICATIONS = [
    "Classical / Generic Medicine",
    "Patent / Proprietary Medicine",
    "New / Non-Classical Drug",
    "Phytopharmaceutical",
    "Ayurveda-Aahar / Nutraceutical",
    "Cosmetic"
]


def classify_product(question: str):

    q = question.lower()

    # ========================================================
    # 1. NEW / NON-CLASSICAL DRUG
    # ========================================================

    new_drug_terms = [
        "new ayurvedic drug",
        "new drug",
        "non-classical drug",
        "non classical drug",
        "not described in any classical",
        "not described in classical",
        "not found in classical text",
        "new therapeutic application",
        "new therapeutic use",
        "completely new formulation",
        "completely new ayurvedic formulation",
    ]

    if any(term in q for term in new_drug_terms):
        return [
            "New / Non-Classical Drug"
        ]

    # ========================================================
    # 2. PHYTOPHARMACEUTICAL
    # ========================================================

    phytopharma_terms = [
        "phytopharmaceutical",
        "phytopharmaceutical drug",
        "standardized botanical drug",
        "standardised botanical drug",
        "standardized botanical product",
        "standardised botanical product",
        "purified plant extract",
        "defined active constituents",
        "defined active constituent",
        "standardized plant extract",
        "standardised plant extract",
        "botanical drug product",
    ]

    if any(term in q for term in phytopharma_terms):
        return [
            "Phytopharmaceutical"
        ]

    # ========================================================
    # 3. AYURVEDA-AHAAR / NUTRACEUTICAL
    # ========================================================

    food_terms = [
        "ayurveda aahar",
        "ayurveda-aahar",
        "ayurveda aahara",
        "ayurveda-aahara",
        "nutraceutical",
        "nutraceutical product",
        "functional food",
        "health food",
        "food product",
        "food supplement",
        "dietary supplement",
        "edible product",
        "food preparation",
    ]

    if any(term in q for term in food_terms):
        return [
            "Ayurveda-Aahar / Nutraceutical"
        ]

    # ========================================================
    # 4. COSMETIC
    # ========================================================

    cosmetic_terms = [
        "cosmetic",
        "cosmetics",
        "skin care",
        "skincare",
        "hair care",
        "haircare",
        "face cream",
        "skin cream",
        "beauty product",
        "personal care product",
        "topical cosmetic",
        "cosmetic formulation",
        "cosmetic product",
    ]

    if any(term in q for term in cosmetic_terms):
        return [
            "Cosmetic"
        ]

    # ========================================================
    # 5. PATENT / PROPRIETARY MEDICINE
    # ========================================================

    proprietary_terms = [
        "proprietary ayurvedic",
        "proprietary medicine",
        "proprietary formulation",
        "proprietary drug",
        "patent / proprietary",
        "patentable formulation",
        "new proprietary formulation",
        "novel composition",
        "novel formulation",
        "novel ayurvedic formulation",
    ]

    if any(term in q for term in proprietary_terms):
        return [
            "Patent / Proprietary Medicine"
        ]

    # ========================================================
    # 6. CLASSICAL / GENERIC MEDICINE
    # ========================================================

    classical_terms = [
        "classical medicine",
        "classical ayurvedic medicine",
        "classical ayurveda medicine",
        "classical formulation",
        "classical formulation from text",
        "established ayurvedic text",
        "established classical text",
        "described in classical text",
        "described in an ayurvedic text",
        "according to classical text",
        "according to an established ayurvedic text",
        "classical ayurvedic text",
        "generic ayurvedic medicine",
    ]

    if any(term in q for term in classical_terms):
        return [
            "Classical / Generic Medicine"
        ]

    # ========================================================
    # 7. UNKNOWN / INSUFFICIENT INFORMATION
    # ========================================================

    return [
        "Classification requires additional product information"
    ]
    """
    Preliminary rule-based product classification.

    IMPORTANT:
    This is NOT a legal or regulatory determination.
    It is only an initial system signal based on wording.
    """

    q = question.lower()

    classifications = []

    # Classical / Generic Medicine
    if any(
        word in q
        for word in [
            "classical medicine",
            "classical ayurvedic",
            "classical formulation",
            "classical drug",
            "generic ayurvedic",
            "traditional formulation"
        ]
    ):
        classifications.append(
            "Classical / Generic Medicine"
        )

    # Patent / Proprietary Medicine
    if any(
        word in q
        for word in [
            "proprietary medicine",
            "proprietary formulation",
            "proprietary ayurvedic",
            "proprietary product",
            "patent medicine"
        ]
    ):
        classifications.append(
            "Patent / Proprietary Medicine"
        )

    # New / Non-Classical Drug
    if any(
        word in q
        for word in [
            "new drug",
            "new ayurvedic drug",
            "non-classical drug",
            "non classical drug",
            "new formulation",
            "novel formulation"
        ]
    ):
        classifications.append(
            "New / Non-Classical Drug"
        )

    # Phytopharmaceutical
    if any(
        word in q
        for word in [
            "phytopharmaceutical",
            "phytopharma",
            "standardized botanical",
            "standardised botanical",
            "plant based pharmaceutical",
            "plant-based pharmaceutical"
        ]
    ):
        classifications.append(
            "Phytopharmaceutical"
        )

    # Ayurveda-Aahar / Nutraceutical
    if any(
        word in q
        for word in [
            "ayurveda aahar",
            "ayurveda-aahar",
            "ayurved aahar",
            "nutraceutical",
            "nutraceutical product",
            "functional food",
            "health food",
            "food supplement",
            "dietary supplement"
        ]
    ):
        classifications.append(
            "Ayurveda-Aahar / Nutraceutical"
        )

    # Cosmetic
    if any(
        word in q
        for word in [
            "cosmetic",
            "cosmetics",
            "face cream",
            "face serum",
            "skin cream",
            "skin serum",
            "hair oil",
            "shampoo",
            "lotion",
            "beauty product",
            "personal care",
            "skin care",
            "skincare"
        ]
    ):
        classifications.append(
            "Cosmetic"
        )

    # General medicine indicators
    if not classifications:
        if any(
            word in q
            for word in [
                "ayurvedic medicine",
                "ayurvedic drug",
                "ayurvedic product",
                "medicine",
                "drug",
                "formulation",
                "churna",
                "kwath",
                "tablet",
                "capsule",
                "syrup",
                "oil",
                "ointment"
            ]
        ):
            classifications.append(
                "Classification requires product-specific verification"
            )

    # No sufficient information
    if not classifications:
        classifications.append(
            "Not enough information for preliminary classification"
        )

    return classifications


# ============================================================
# IP / REGULATORY DOMAIN DETECTION
# ============================================================

def detect_domains(question: str):

    q = question.lower()

    domains = []

    # Patent
    if any(
        word in q
        for word in [
            "patent",
            "patents",
            "patentability",
            "novelty",
            "prior art",
            "inventive step",
            "industrial applicability",
            "patent application",
            "patent protection",
            "patent infringement",
            "freedom to operate",
            "fda approval"
        ]
    ):
        domains.append("Patent")

    # Traditional Knowledge
    if any(
        word in q
        for word in [
            "traditional knowledge",
            "traditional",
            "tkdl",
            "misappropriation",
            "traditional use",
            "community knowledge",
            "traditional medicinal knowledge"
        ]
    ):
        domains.append("Traditional Knowledge")

    # Biodiversity / ABS
    if any(
        word in q
        for word in [
            "abs",
            "access and benefit sharing",
            "access and benefit-sharing",
            "biodiversity",
            "biological diversity",
            "biological resource",
            "biological resources",
            "benefit sharing",
            "benefit-sharing",
            "genetic resource",
            "genetic resources"
        ]
    ):
        domains.append("Biodiversity / ABS")

    # Trademark
    if any(
        word in q
        for word in [
            "trademark",
            "trade mark",
            "brand",
            "brand name",
            "logo",
            "mark registration",
            "trade name"
        ]
    ):
        domains.append("Trademark")

    # Copyright
    if any(
        word in q
        for word in [
            "copyright",
            "artwork",
            "literature",
            "content",
            "original work"
        ]
    ):
        domains.append("Copyright")

    # GI
    if any(
        word in q
        for word in [
            "geographical indication",
            "geographical indications",
            "gi tag",
            "gi registration",
            "geographical origin"
        ]
    ):
        domains.append("Geographical Indication")

    # Design
    if any(
        word in q
        for word in [
            "industrial design",
            "design registration",
            "registered design",
            "product design",
            "packaging design",
            "design protection"
        ]
    ):
        domains.append("Design")

    # Plant Variety Protection
    if any(
        word in q
        for word in [
            "plant variety",
            "plant varieties",
            "plant variety protection",
            "breeders right",
            "breeders' right",
            "breeder right",
            "farmers rights",
            "farmers' rights",
            "ppvfra"
        ]
    ):
        domains.append("Plant Variety Protection")

    # Trade Secret
    if any(
        word in q
        for word in [
            "trade secret",
            "trade secrets",
            "confidential information",
            "confidential formulation",
            "know-how",
            "know how"
        ]
    ):
        domains.append("Trade Secret")

    # Ayurveda / AYUSH
    if any(
        word in q
        for word in [
            "ayurveda",
            "ayurvedic",
            "ayush",
            "ayush medicine",
            "formulation",
            "medicine",
            "drug",
            "classical",
            "proprietary"
        ]
    ):
        domains.append("Ayurveda / AYUSH")

    # Food / Nutraceutical
    if any(
        word in q
        for word in [
            "food",
            "food product",
            "nutraceutical",
            "nutrition",
            "supplement",
            "ayurveda aahar",
            "ayurveda-aahar"
        ]
    ):
        domains.append("Food / Nutraceutical")

    # Cosmetics
    if any(
        word in q
        for word in [
            "cosmetic",
            "cosmetics",
            "face cream",
            "face serum",
            "skin care",
            "skincare",
            "hair care",
            "shampoo",
            "lotion",
            "beauty product",
            "personal care"
        ]
    ):
        domains.append("Cosmetics")

    # Advertising / Labelling
    if any(
        word in q
        for word in [
            "advertising",
            "advertisement",
            "advertise",
            "label",
            "labelling",
            "labeling",
            "claims",
            "claim",
            "health claim",
            "medical claim",
            "marketing claim",
            "promotional claim"
        ]
    ):
        domains.append("Advertising / Labelling")

    # International
    if any(
        word in q
        for word in [
            "international",
            "wipo",
            "pct",
            "trips",
            "madrid",
            "lisbon",
            "hague",
            "budapest treaty",
            "nagoya",
            "cbd",
            "foreign",
            "other countries",
            "overseas",
            "export",
            "global"
        ]
    ):
        domains.append("International IP")

    # Commercialisation
    if any(
        word in q
        for word in [
            "commercialize",
            "commercialise",
            "commercialization",
            "commercialisation",
            "market",
            "market launch",
            "product launch",
            "sell",
            "selling",
            "commercial"
        ]
    ):
        domains.append("Commercialisation")

    if not domains:
        domains.append(
            "General IP / Regulatory"
        )

    return domains


# ============================================================
# JURISDICTION DETECTION
# ============================================================

def detect_jurisdictions(question: str):

    q = question.lower()

    jurisdictions = []

    india_terms = [
        "india",
        "indian",
        "ipindia",
        "indian patent office",
        "indian trademark",
        "ayush india",
        "ministry of ayush",
        "biological diversity act",
        "tkdl",
        "cdsco",
        "fssai",
        "ppvfra"
    ]

    international_terms = [
        "international",
        "wipo",
        "pct",
        "trips",
        "madrid",
        "lisbon",
        "hague",
        "budapest treaty",
        "nagoya",
        "cbd",
        "foreign",
        "other countries",
        "overseas",
        "export",
        "global"
    ]

    if any(
        word in q
        for word in india_terms
    ):
        jurisdictions.append("India")

    if any(
        word in q
        for word in international_terms
    ):
        jurisdictions.append("International")

    if not jurisdictions:
        jurisdictions.append("User-selected")

    return jurisdictions


# ============================================================
# SOURCE REGISTRY
# ============================================================

def load_source_registry():

    if not SOURCE_REGISTRY_FILE.exists():

        print(
            "SOURCE ERROR: source_registry.json NOT FOUND"
        )

        print(
            "Expected location:",
            SOURCE_REGISTRY_FILE
        )

        return []

    try:

        data = json.loads(
            SOURCE_REGISTRY_FILE.read_text(
                encoding="utf-8"
            )
        )

        if isinstance(data, list):

            sources = data

        else:

            sources = data.get(
                "sources",
                []
            )

        if not isinstance(
            sources,
            list
        ):

            sources = []

        print(
            "SOURCE SUCCESS: source registry loaded"
        )

        print(
            "SOURCE COUNT:",
            len(sources)
        )

        return sources

    except Exception as e:

        print(
            "SOURCE ERROR while reading registry:",
            e
        )

        return []


# ============================================================
# SOURCE SAFETY
# ============================================================

def is_source_allowed_for_rag(source):

    """
    A source is RAG-eligible only when the source registry
    explicitly permits normal RAG use.

    Restricted/private/non-public sources are never treated
    as retrieved RAG evidence.
    """

    use_for_rag = source.get(
        "use_for_rag",
        True
    )

    if use_for_rag is False:
        return False

    access = str(
        source.get(
            "access",
            ""
        )
    ).strip().lower()

    restricted_values = {
        "restricted",
        "restricted access",
        "private",
        "not publicly accessible",
        "confidential"
    }

    if access in restricted_values:
        return False

    return True


def source_id_from_source(source):

    return str(
        source.get(
            "source_id",
            ""
        )
    ).strip()


def get_registered_source_map(source_registry):

    result = {}

    for source in source_registry:

        source_id = source_id_from_source(
            source
        )

        if source_id:
            result[source_id] = source

    return result


# ============================================================
# JURISDICTION SOURCE FILTER
# ============================================================

def filter_sources_by_jurisdiction(
    source_registry,
    question,
    selected_jurisdiction
):

    detected_jurisdictions = (
        detect_jurisdictions(question)
    )

    selected = (
        selected_jurisdiction
        or "India"
    ).strip().lower()

    relevant_sources = []

    # Determine effective scope.
    explicit_india = "India" in detected_jurisdictions
    explicit_international = (
        "International"
        in detected_jurisdictions
    )

    for source in source_registry:

        # Restricted/non-RAG sources NEVER enter RAG evidence.
        if not is_source_allowed_for_rag(source):
            continue

        source_jurisdiction = str(
            source.get(
                "jurisdiction",
                ""
            )
        ).strip().lower()

        if not source_jurisdiction:
            continue

        # Explicitly both
        if explicit_india and explicit_international:

            if source_jurisdiction in {
                "india",
                "international"
            }:
                relevant_sources.append(source)

        # Explicitly international
        elif explicit_international:

            if source_jurisdiction == "international":
                relevant_sources.append(source)

        # Explicitly India
        elif explicit_india:

            if source_jurisdiction == "india":
                relevant_sources.append(source)

        # Otherwise use dropdown
        else:

            if selected == "india":

                if source_jurisdiction == "india":
                    relevant_sources.append(source)

            elif selected == "international":

                if source_jurisdiction == "international":
                    relevant_sources.append(source)

    return (
        relevant_sources,
        detected_jurisdictions
    )


# ============================================================
# DOCUMENT EXTRACTION
# ============================================================

def read_uploaded_document(document):

    try:

        filename = (
            document.filename
            or ""
        ).lower()

        # PDF
        if filename.endswith(".pdf"):

            reader = PdfReader(
                document.file
            )

            pages = []

            for page in reader.pages:

                text = page.extract_text()

                if text:
                    pages.append(text)

            return "\n\n".join(
                pages
            ).strip()

        # DOCX
        elif filename.endswith(".docx"):

            from docx import Document

            doc = Document(
                document.file
            )

            paragraphs = []

            for paragraph in doc.paragraphs:

                if paragraph.text.strip():

                    paragraphs.append(
                        paragraph.text.strip()
                    )

            return "\n\n".join(
                paragraphs
            ).strip()

        # TXT
        elif filename.endswith(".txt"):

            return (
                document.file.read()
                .decode(
                    "utf-8",
                    errors="ignore"
                )
                .strip()
            )

        return ""

    except Exception as e:

        print(
            "DOCUMENT ERROR:",
            e
        )

        return ""


# ============================================================
# KNOWLEDGE BASE
# ============================================================

def load_knowledge_base():

    if not KNOWLEDGE_FILE.exists():

        print(
            "RAG ERROR: knowledge_base.txt NOT FOUND"
        )

        print(
            "Expected location:",
            KNOWLEDGE_FILE
        )

        return ""

    try:

        text = KNOWLEDGE_FILE.read_text(
            encoding="utf-8"
        )

        print(
            "RAG SUCCESS: knowledge_base.txt loaded"
        )

        print(
            "RAG file:",
            KNOWLEDGE_FILE
        )

        print(
            "RAG characters:",
            len(text)
        )

        return text

    except Exception as e:

        print(
            "RAG ERROR while reading knowledge base:",
            e
        )

        return ""


# ============================================================
# SOURCE ID EXTRACTION
# ============================================================

def extract_source_ids(text: str):
    if not text:
        return []

    source_ids = []

    patterns = [
        r"SOURCE\s*ID\s*[:=]\s*([A-Za-z0-9_.-]+)",
        r"SOURCE[_\s-]*ID\s*[:=]\s*([A-Za-z0-9_.-]+)",
    ]

    for pattern in patterns:
        matches = re.findall(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        for match in matches:
            clean_id = match.strip()

            if (
                clean_id
                and clean_id not in source_ids
            ):
                source_ids.append(clean_id)

    return source_ids


# ============================================================
# CLEAN AI MARKDOWN
# ============================================================

def clean_ai_markdown(text: str):
    if not text:
        return text

    cleaned = text

    # ========================================================
    # REMOVE BACKSLASHES USED TO ESCAPE MARKDOWN
    # ========================================================

    cleaned = cleaned.replace(r'\###', '###')
    cleaned = cleaned.replace(r'\##', '##')
    cleaned = cleaned.replace(r'\#', '#')

    cleaned = cleaned.replace(r'\*\*\*', '***')
    cleaned = cleaned.replace(r'\*\*', '**')
    cleaned = cleaned.replace(r'\*', '*')

    cleaned = cleaned.replace(r'\_', '_')
    cleaned = cleaned.replace(r'\-', '-')

    cleaned = cleaned.replace(r'\[', '[')
    cleaned = cleaned.replace(r'\]', ']')

    cleaned = cleaned.replace(r'\(', '(')
    cleaned = cleaned.replace(r'\)', ')')

    cleaned = cleaned.replace(r'\`', '`')

    # ========================================================
    # REMOVE BACKSLASH BEFORE MARKDOWN HORIZONTAL RULE
    # ========================================================

    cleaned = cleaned.replace(r'\---', '---')

    # ========================================================
    # FIX SOURCE ID LINE BREAKS
    # ========================================================

    cleaned = re.sub(
        r'Source ID:\s*\n+\s*([A-Za-z0-9_.-]+(?:\s*,\s*[A-Za-z0-9_.-]+)*)',
        r'Source ID: \1',
        cleaned,
        flags=re.IGNORECASE
    )

    # ========================================================
    # NORMALIZE EXCESSIVE BLANK LINES
    # ========================================================

    cleaned = re.sub(
        r'\n{4,}',
        '\n\n\n',
        cleaned
    )

    return cleaned.strip()

# ============================================================
# DOMAIN KEYWORDS
# ============================================================

DOMAIN_KEYWORDS = {

    "Patent": [
        "PATENT",
        "PRIOR ART",
        "NOVELTY",
        "INVENTIVE STEP",
        "INDUSTRIAL APPLICABILITY"
    ],

    "Traditional Knowledge": [
        "TRADITIONAL KNOWLEDGE",
        "TKDL",
        "MISAPPROPRIATION"
    ],

    "Biodiversity / ABS": [
        "ABS",
        "BIOLOGICAL DIVERSITY",
        "BIOLOGICAL RESOURCE",
        "BENEFIT SHARING",
        "NAGOYA"
    ],

    "Trademark": [
        "TRADEMARK",
        "TRADE MARK",
        "BRAND"
    ],

    "Copyright": [
        "COPYRIGHT"
    ],

    "Geographical Indication": [
        "GEOGRAPHICAL INDICATION",
        "GI"
    ],

    "Design": [
        "DESIGN",
        "INDUSTRIAL DESIGN"
    ],

    "Plant Variety Protection": [
        "PLANT VARIETY",
        "PLANT VARIETIES",
        "PPVFRA",
        "BREEDERS"
    ],

    "Trade Secret": [
        "TRADE SECRET",
        "CONFIDENTIAL INFORMATION",
        "KNOW-HOW",
        "KNOW HOW"
    ],

    "Ayurveda / AYUSH": [
        "AYURVEDA",
        "AYURVEDIC",
        "AYUSH",
        "CLASSIFICATION"
    ],

    "Food / Nutraceutical": [
        "FOOD",
        "NUTRACEUTRACEUTICAL",
        "NUTRACEUTICAL",
        "AYURVEDA-AAHAR",
        "AYURVEDA AAHAR",
        "SUPPLEMENT"
    ],

    "Cosmetics": [
        "COSMETIC",
        "COSMETICS",
        "SKIN CARE",
        "SKINCARE"
    ],

    "Advertising / Labelling": [
        "ADVERTISING",
        "ADVERTISEMENT",
        "LABELLING",
        "LABELING",
        "CLAIM",
        "MARKETING"
    ],

    "International IP": [
        "INTERNATIONAL",
        "WIPO",
        "PCT",
        "TRIPS",
        "MADRID",
        "HAGUE",
        "LISBON",
        "BUDAPEST",
        "NAGOYA"
    ],

    "Commercialisation": [
        "COMMERCIAL",
        "COMMERCIALIZE",
        "COMMERCIALISE",
        "MARKET",
        "PRODUCT LAUNCH"
    ]
}


# ============================================================
# RAG RETRIEVAL
# ============================================================

def retrieve_context(
    question: str,
    allowed_source_ids=None
):
    """
    Retrieve relevant evidence from the local knowledge base.

    This is a lightweight keyword/term based RAG retrieval layer.
    It preserves source IDs and jurisdiction filtering while making
    retrieval less restrictive for genuine knowledge-base evidence.
    """

    knowledge = load_knowledge_base()

    if not knowledge:
        print(
            "RAG FILTERED RESULT: knowledge base is empty"
        )
        return ""

    detected_domains = detect_domains(
        question
    )

    print(
        "DOMAIN CHECK:",
        ", ".join(detected_domains)
    )

    sections = knowledge.split(
        "\n\n"
    )

    # --------------------------------------------------------
    # BUILD DOMAIN KEYWORDS
    # --------------------------------------------------------

    keywords = []

    for domain in detected_domains:

        keywords.extend(
            DOMAIN_KEYWORDS.get(
                domain,
                []
            )
        )

    # --------------------------------------------------------
    # QUESTION-SPECIFIC KEYWORDS
    # --------------------------------------------------------

    q = question.lower()

    question_keyword_groups = [

        # Patent
        [
            "patent",
            "patents",
            "patentability",
            "novelty",
            "inventive",
            "invention",
            "industrial applicability",
            "prior art",
            "claim",
            "claims"
        ],

        # Traditional knowledge
        [
            "traditional knowledge",
            "traditional",
            "tk",
            "tkdl",
            "ayurveda",
            "ayurvedic",
            "classical",
            "traditional medicine"
        ],

        # Section 3(p)
        [
            "section 3(p)",
            "section 3p",
            "3(p)",
            "3p",
            "known properties",
            "aggregation",
            "duplication"
        ],

        # ABS / biodiversity
        [
            "abs",
            "access benefit sharing",
            "benefit sharing",
            "biodiversity",
            "biological resource",
            "genetic resource",
            "nagoya"
        ],

        # Trademark
        [
            "trademark",
            "trade mark",
            "brand",
            "logo"
        ],

        # Classification
        [
            "classify",
            "classification",
            "product",
            "formulation",
            "medicine",
            "drug",
            "cosmetic",
            "food",
            "nutraceutical",
            "ayurveda-aahar",
            "proprietary"
        ],

        # International
        [
            "international",
            "pct",
            "wipo",
            "trips",
            "foreign",
            "export"
        ]
    ]

    for group in question_keyword_groups:

        if any(
            phrase in q
            for phrase in group
        ):

            keywords.extend(
                group
            )

    # Remove duplicates while preserving order
    keywords = list(
        dict.fromkeys(
            keywords
        )
    )

    # --------------------------------------------------------
    # JURISDICTION-AWARE SOURCE FILTER
    # --------------------------------------------------------

    if allowed_source_ids is not None:

        allowed_source_ids = {
            str(source_id).strip()
            for source_id in allowed_source_ids
            if str(source_id).strip()
        }

        print(
            "RAG JURISDICTION FILTER:",
            len(allowed_source_ids),
            "allowed source IDs"
        )

    # --------------------------------------------------------
    # QUESTION TERMS
    # --------------------------------------------------------

    question_terms = [
        term.lower()
        for term in re.findall(
            r"[A-Za-z0-9]{3,}",
            q
        )
    ]

    # Terms that are too generic to provide useful matching
    stop_terms = {
        "what",
        "does",
        "this",
        "that",
        "with",
        "from",
        "about",
        "have",
        "will",
        "into",
        "your",
        "based",
        "under",
        "which",
        "their",
        "they",
        "them",
        "and",
        "the",
        "for",
        "are",
        "how",
        "can"
    }

    question_terms = [
        term
        for term in question_terms
        if term not in stop_terms
    ]

    # --------------------------------------------------------
    # SCORE KNOWLEDGE-BASE SECTIONS
    # --------------------------------------------------------

    scored_sections = []

    for section in sections:

        section = section.strip()

        if not section:
            continue

        section_upper = section.upper()

        # ----------------------------------------------------
        # SOURCE ID FILTER
        # ----------------------------------------------------

        section_source_ids = extract_source_ids(
            section
        )

        if (
            allowed_source_ids is not None
            and section_source_ids
            and not (
                set(section_source_ids)
                & allowed_source_ids
            )
        ):
            continue

        # ----------------------------------------------------
        # IMPORTANT:
        #
        # Do NOT automatically discard a section merely
        # because it does not contain SOURCE ID.
        #
        # The knowledge base may contain useful contextual
        # evidence in sections without an inline source ID.
        # Such sections can still contribute to retrieval.
        # Source validation later decides whether a source
        # association is authoritative.
        # ----------------------------------------------------

        score = 0

        # ----------------------------------------------------
        # DOMAIN / EXPLICIT KEYWORD MATCH
        # ----------------------------------------------------

        for keyword in keywords:

            keyword_text = str(
                keyword
            ).strip()

            if not keyword_text:
                continue

            if keyword_text.upper() in section_upper:

                # Stronger weight for exact multi-word concepts
                if " " in keyword_text:
                    score += 2
                else:
                    score += 1

        # ----------------------------------------------------
        # QUESTION TERM MATCH
        # ----------------------------------------------------

        for term in question_terms:

            if term.upper() in section_upper:

                score += 0.5

        # ----------------------------------------------------
        # SOURCE ID BONUS
        # ----------------------------------------------------

        if re.search(
            r"SOURCE\s*ID\s*[:=]",
            section,
            flags=re.IGNORECASE
        ):

            score += 1.0

        # ----------------------------------------------------
        # HIGH-VALUE LEGAL / TECHNICAL CONCEPT BONUS
        # ----------------------------------------------------

        high_value_terms = [

            "SECTION 3(P)",
            "PATENTS ACT",
            "PATENTABILITY",
            "TRADITIONAL KNOWLEDGE",
            "TKDL",
            "PRIOR ART",
            "NOVELTY",
            "INVENTIVE STEP",
            "INDUSTRIAL APPLICABILITY",
            "ACCESS AND BENEFIT SHARING",
            "BIODIVERSITY",
            "PCT",
            "WIPO"
        ]

        for term in high_value_terms:

            if term in section_upper:

                score += 1.5

        # ----------------------------------------------------
        # KEEP ONLY RELEVANT SECTIONS
        # ----------------------------------------------------

        if score > 0:

            scored_sections.append(
                (
                    score,
                    section
                )
            )

    # --------------------------------------------------------
    # SORT BY RELEVANCE
    # --------------------------------------------------------

    scored_sections.sort(
        key=lambda item: item[0],
        reverse=True
    )

    # --------------------------------------------------------
    # RETRIEVE TOP EVIDENCE
    # --------------------------------------------------------

    retrieved = [
        section
        for score, section
        in scored_sections
    ]

    if retrieved:

        print(
            "RAG FILTERED SECTIONS:",
            len(retrieved)
        )

        # Show the highest scoring evidence first
        selected_sections = retrieved[:25]

        result = "\n\n".join(
            selected_sections
        )

        print(
            "RAG RETRIEVAL SUCCESS:",
            len(result),
            "characters"
        )

        return result

    # --------------------------------------------------------
    # FALLBACK:
    #
    # If no exact keyword match was found, retrieve sections
    # containing at least one meaningful question term.
    # --------------------------------------------------------

    fallback_sections = []

    for section in sections:

        section = section.strip()

        if not section:
            continue

        section_upper = section.upper()

        section_source_ids = extract_source_ids(
            section
        )

        if (
            allowed_source_ids is not None
            and section_source_ids
            and not (
                set(section_source_ids)
                & allowed_source_ids
            )
        ):
            continue

        fallback_score = 0

        for term in question_terms:

            if term.upper() in section_upper:

                fallback_score += 1

        if fallback_score > 0:

            fallback_sections.append(
                (
                    fallback_score,
                    section
                )
            )

    fallback_sections.sort(
        key=lambda item: item[0],
        reverse=True
    )

    if fallback_sections:

        result = "\n\n".join(
            section
            for score, section
            in fallback_sections[:15]
        )

        print(
            "RAG FALLBACK SUCCESS:",
            len(result),
            "characters"
        )

        return result

    print(
        "RAG FILTERED RESULT: no matching evidence"
    )

    return ""


# ============================================================
# SOURCE TEXT
# ============================================================

def build_source_text(
    sources
):

    source_blocks = []

    for source in sources:

        source_id = source.get(
            "source_id",
            "UNKNOWN"
        )

        authority = source.get(
            "authority",
            "Not specified"
        )

        document = source.get(
            "document",
            "Not specified"
        )

        jurisdiction = source.get(
            "jurisdiction",
            "Not specified"
        )

        official_url = source.get(
            "official_url",
            "Not specified"
        )

        source_blocks.append(
            (
                f"SOURCE ID: {source_id}\n"
                f"AUTHORITY: {authority}\n"
                f"DOCUMENT: {document}\n"
                f"JURISDICTION: {jurisdiction}\n"
                f"OFFICIAL URL: {official_url}"
            )
        )

    return "\n\n".join(
        source_blocks
    )


# ============================================================
# SOURCE VALIDATION
# ============================================================

def validate_source_associations(
    retrieved_context,
    source_registry,
    relevant_sources
):
    """
    Validate the source IDs actually present in the retrieved
    RAG context.

    A source is considered valid only when:
    1. It exists in the source registry.
    2. It is permitted for RAG use.
    3. It was actually retrieved into the current context.

    This keeps the evidence/citation layer grounded in the
    current RAG retrieval instead of merely relying on the
    complete source registry.
    """

    source_map = get_registered_source_map(
        source_registry
    )

    # --------------------------------------------------------
    # SOURCE IDs ACTUALLY PRESENT IN RETRIEVED RAG CONTEXT
    # --------------------------------------------------------

    referenced_ids = extract_source_ids(
        retrieved_context or ""
    )

    referenced_ids = list(
        dict.fromkeys(
            str(source_id).strip()
            for source_id in referenced_ids
            if str(source_id).strip()
        )
    )

    # --------------------------------------------------------
    # SOURCE IDs SELECTED BY CURRENT JURISDICTION FILTER
    # --------------------------------------------------------

    relevant_source_ids = {
        str(source_id_from_source(source)).strip()
        for source in (relevant_sources or [])
        if source_id_from_source(source)
    }

    valid_ids = []
    invalid_ids = []
    jurisdiction_mismatch_ids = []
    restricted_ids = []

    # --------------------------------------------------------
    # VALIDATE EVERY RETRIEVED SOURCE
    # --------------------------------------------------------

    for source_id in referenced_ids:

        source = source_map.get(
            source_id
        )

        # ----------------------------------------------------
        # 1. SOURCE IS NOT REGISTERED
        # ----------------------------------------------------

        if not source:
            invalid_ids.append(
                source_id
            )
            continue

        # ----------------------------------------------------
        # 2. SOURCE IS REGISTERED BUT NOT ALLOWED FOR RAG
        # ----------------------------------------------------

        if not is_source_allowed_for_rag(
            source
        ):
            restricted_ids.append(
                source_id
            )
            continue

        # ----------------------------------------------------
        # 3. SOURCE IS OUTSIDE THE CURRENT JURISDICTION
        #
        # Only classify it as a mismatch when the current
        # jurisdiction filter actually supplied a source list.
        # ----------------------------------------------------

        if (
            relevant_source_ids
            and source_id not in relevant_source_ids
        ):
            jurisdiction_mismatch_ids.append(
                source_id
            )
            continue

        # ----------------------------------------------------
        # 4. SOURCE IS REGISTERED + ALLOWED + RELEVANT
        # ----------------------------------------------------

        valid_ids.append(
            source_id
        )

    # --------------------------------------------------------
    # REMOVE DUPLICATES WHILE PRESERVING ORDER
    # --------------------------------------------------------

    valid_ids = list(
        dict.fromkeys(
            valid_ids
        )
    )

    invalid_ids = list(
        dict.fromkeys(
            invalid_ids
        )
    )

    jurisdiction_mismatch_ids = list(
        dict.fromkeys(
            jurisdiction_mismatch_ids
        )
    )

    restricted_ids = list(
        dict.fromkeys(
            restricted_ids
        )
    )

    # --------------------------------------------------------
    # DEBUG / AUDIT LOGGING
    # --------------------------------------------------------

    print(
        "SOURCE VALIDATION: referenced IDs =",
        referenced_ids
    )

    print(
        "SOURCE VALIDATION: valid IDs =",
        valid_ids
    )

    if invalid_ids:
        print(
            "SOURCE VALIDATION: invalid IDs =",
            invalid_ids
        )

    if jurisdiction_mismatch_ids:
        print(
            "SOURCE VALIDATION: jurisdiction mismatch IDs =",
            jurisdiction_mismatch_ids
        )

    if restricted_ids:
        print(
            "SOURCE VALIDATION: restricted IDs =",
            restricted_ids
        )

    # --------------------------------------------------------
    # FINAL VALIDATION RESULT
    # --------------------------------------------------------

    return {
        "referenced_ids": referenced_ids,
        "valid_ids": valid_ids,
        "invalid_ids": invalid_ids,
        "jurisdiction_mismatch_ids": jurisdiction_mismatch_ids,
        "restricted_ids": restricted_ids
    }


# ============================================================
# EVIDENCE STRENGTH
# ============================================================

def calculate_evidence_strength(
    retrieved_context,
    source_validation,
    relevant_sources
):

    if not retrieved_context:
        return "None"

    valid_ids = source_validation.get(
        "valid_ids",
        []
    )

    invalid_ids = source_validation.get(
        "invalid_ids",
        []
    )

    jurisdiction_mismatch_ids = (
        source_validation.get(
            "jurisdiction_mismatch_ids",
            []
        )
    )

    restricted_ids = source_validation.get(
        "restricted_ids",
        []
    )

    if (
        valid_ids
        and not invalid_ids
        and not jurisdiction_mismatch_ids
        and not restricted_ids
    ):
        return "Strong"

    if valid_ids or relevant_sources:
        return "Moderate"

    return "Weak"


# ============================================================
# SAFE ABSTENTION
# ============================================================

def needs_safe_abstention(
    retrieved_context,
    question,
    source_validation,
    evidence_strength
):

    if not retrieved_context:
        return True

    q = question.lower()

    high_risk_terms = [

        "definitely patentable",
        "guaranteed patent",
        "will get patent",
        "guaranteed approval",
        "definitely legal",
        "definitely illegal",
        "exact penalty",
        "avoid the law",
        "bypass regulation",
        "guaranteed registration",
        "is this definitely legal",
        "can i definitely sell",
        "definitely compliant",
        "is it legal",
        "is this legal",
        "will my patent be granted"
    ]

    if any(
        term in q
        for term in high_risk_terms
    ):
        return True

    if evidence_strength in {
        "None",
        "Weak"
    }:
        return True

    if source_validation.get(
        "invalid_ids"
    ):
        return True

    if source_validation.get(
        "restricted_ids"
    ):
        return True

    return False


# ============================================================
# HUMAN REVIEW
# ============================================================

def requires_human_review(
    question,
    evidence_strength
):

    q = question.lower()

    high_risk_topics = [

        "patent infringement",
        "lawsuit",
        "litigation",
        "legal notice",
        "court",
        "penalty",
        "violation",
        "regulatory action",
        "enforcement",
        "patentability conclusion",
        "prior art search",
        "freedom to operate",
        "fda approval",
        "licence cancellation",
        "license cancellation",
        "patent validity",
        "infringement",
        "legal dispute"
    ]

    if any(
        topic in q
        for topic in high_risk_topics
    ):
        return True

    if evidence_strength in {
        "None",
        "Weak"
    }:
        return True

    return False


# ============================================================
# CONFIDENCE
# ============================================================

def calculate_confidence(
    retrieved_context,
    relevant_sources,
    source_validation,
    evidence_strength,
    question
):

    """
    Confidence represents confidence in the retrieved
    evidence available to IP-SAKTI.

    It does NOT represent legal certainty.

    IP-SAKTI does not perform:
    - exhaustive prior-art searches
    - court-level legal analysis
    - complete FTO analysis
    - regulatory determinations

    Therefore High confidence is deliberately disabled.
    """

    if not retrieved_context:
        return "Low"

    if evidence_strength == "Strong":

        if (
            source_validation.get("valid_ids")
            and relevant_sources
            and not source_validation.get("invalid_ids")
            and not source_validation.get(
                "jurisdiction_mismatch_ids"
            )
            and not source_validation.get(
                "restricted_ids"
            )
        ):
            return "Moderate"

    if evidence_strength == "Moderate":
        return "Moderate"

    return "Low"


# ============================================================
# FRONTEND
# ============================================================

@app.get("/")
def serve_frontend():

    frontend_file = (
        BASE_DIR
        / "frontend"
        / "index.html"
    )

    if not frontend_file.exists():

        raise HTTPException(
            status_code=404,
            detail=(
                "Frontend index.html was not found."
            )
        )

    return FileResponse(
        frontend_file
    )


# ============================================================
# ASK IP-SAKTI
# ============================================================

@app.post("/api/ask")
def ask_ipsakti(

    question: str = Form(...),

    jurisdiction: str = Form("India"),

    language: str = Form("English"),

    conversation_history: str = Form(""),

    document: UploadFile = File(None)

):

    request = QuestionRequest(

        question=question,

        jurisdiction=jurisdiction,

        language=language

    )

    # ========================================================
    # ENVIRONMENT
    # ========================================================

    load_dotenv(
        dotenv_path=ENV_FILE,
        override=True
    )

    api_key = os.getenv(
        "GEMINI_API_KEY"
    )

    if not api_key:

        raise HTTPException(
            status_code=500,
            detail=(
                "Gemini API key was not detected."
            )
        )

    question = request.question.strip()

    if not question:

        raise HTTPException(
            status_code=400,
            detail=(
                "Please enter your question."
            )
        )

    # ========================================================
    # DOMAIN DETECTION
    # ========================================================

    detected_domains = detect_domains(
        question
    )

    print(
        "DOMAIN CHECK:",
        ", ".join(
            detected_domains
        )
    )

    # ========================================================
    # PRODUCT CLASSIFICATION
    # ========================================================

    product_classification = (
        classify_product(
            question
        )
    )

    print(
        "PRODUCT CLASSIFICATION:",
        ", ".join(
            product_classification
        )
    )

    # ========================================================
    # JURISDICTION
    # ========================================================

    detected_jurisdictions = (
        detect_jurisdictions(
            question
        )
    )

    print(
        "JURISDICTION CHECK:",
        ", ".join(
            detected_jurisdictions
        )
    )

    # ========================================================
    # DOCUMENT
    # ========================================================

    uploaded_document_text = ""

    if document:

        uploaded_document_text = (
            read_uploaded_document(
                document
            )
        )

        print(
            "DOCUMENT CHECK: uploaded document "
            "text characters =",
            len(
                uploaded_document_text
            )
        )

    # ========================================================
    # RAG
    # ========================================================

    retrieved_context = (
        retrieve_context(
            question
        )
    )

    print(
        "RAG CHECK: retrieve_context() was called"
    )

    print(
        "RAG CHECK: retrieved characters =",
        len(
            retrieved_context
        )
    )

    # ========================================================
    # SOURCE REGISTRY
    # ========================================================

    source_registry = (
        load_source_registry()
    )

    (
        relevant_sources,
        detected_jurisdictions
    ) = filter_sources_by_jurisdiction(
        source_registry,
        question,
        request.jurisdiction
    )

    print(
        "SOURCE CHECK: total registered sources =",
        len(
            source_registry
        )
    )

    print(
        "SOURCE CHECK: jurisdiction-matched RAG sources =",
        len(
            relevant_sources
        )
    )

    # ========================================================
    # SOURCE VALIDATION
    # ========================================================

    source_validation = (
        validate_source_associations(
            retrieved_context,
            source_registry,
            relevant_sources
        )
    )

    print(
        "SOURCE VALIDATION: referenced IDs =",
        source_validation["referenced_ids"]
    )

    print(
        "SOURCE VALIDATION: valid IDs =",
        source_validation["valid_ids"]
    )

    print(
        "SOURCE VALIDATION: invalid IDs =",
        source_validation["invalid_ids"]
    )

    print(
        "SOURCE VALIDATION: jurisdiction mismatch IDs =",
        source_validation[
            "jurisdiction_mismatch_ids"
        ]
    )

    print(
        "SOURCE VALIDATION: restricted IDs =",
        source_validation[
            "restricted_ids"
        ]
    )

    # ========================================================
    # EVIDENCE
    # ========================================================

    evidence_strength = (
        calculate_evidence_strength(
            retrieved_context,
            source_validation,
            relevant_sources
        )
    )

    print(
        "EVIDENCE STRENGTH:",
        evidence_strength
    )

    # ========================================================
    # SAFE ABSTENTION
    # ========================================================

    abstention_required = (
        needs_safe_abstention(
            retrieved_context,
            question,
            source_validation,
            evidence_strength
        )
    )

    print(
        "SAFE ABSTENTION:",
        abstention_required
    )

    # ========================================================
    # HUMAN REVIEW
    # ========================================================

    human_review_required = (
        requires_human_review(
            question,
            evidence_strength
        )
    )

    print(
        "HUMAN REVIEW:",
        human_review_required
    )

    # ========================================================
    # CONFIDENCE
    # ========================================================

    confidence = (
        calculate_confidence(
            retrieved_context,
            relevant_sources,
            source_validation,
            evidence_strength,
            question
        )
    )

    print(
        "CONFIDENCE:",
        confidence
    )

    # ========================================================
    # SOURCE TEXT
    # ========================================================

    source_text = build_source_text(
        relevant_sources
    )

    # ========================================================
    # EVIDENCE BLOCK
    # ========================================================

    if retrieved_context:

        evidence = f"""
LOCAL KNOWLEDGE BASE EVIDENCE:

{retrieved_context}

REGISTERED RAG-ELIGIBLE SOURCES MATCHED TO THE
SELECTED / DETECTED JURISDICTION:

{
    source_text
    if source_text
    else
    "No jurisdiction-matched RAG-eligible sources were found."
}

SOURCE ASSOCIATION VALIDATION:

Referenced source IDs:
{
    ", ".join(
        source_validation["referenced_ids"]
    )
    if source_validation["referenced_ids"]
    else
    "None"
}

Valid registered source IDs:
{
    ", ".join(
        source_validation["valid_ids"]
    )
    if source_validation["valid_ids"]
    else
    "None"
}

Invalid or unregistered source IDs:
{
    ", ".join(
        source_validation["invalid_ids"]
    )
    if source_validation["invalid_ids"]
    else
    "None"
}

Jurisdiction-mismatched source IDs:
{
    ", ".join(
        source_validation[
            "jurisdiction_mismatch_ids"
        ]
    )
    if source_validation[
        "jurisdiction_mismatch_ids"
    ]
    else
    "None"
}

Restricted / non-RAG source IDs:
{
    ", ".join(
        source_validation[
            "restricted_ids"
        ]
    )
    if source_validation[
        "restricted_ids"
    ]
    else
    "None"
}
"""

    else:

        evidence = (
            "No relevant evidence was retrieved "
            "from the local knowledge base."
        )

    # ========================================================
    # CONVERSATION CONTEXT
    # ========================================================

    if conversation_history:

        conversation_context = f"""

PREVIOUS CONVERSATION:

{conversation_history}

Use this previous conversation only to understand
the user's context and follow-up references.

Do not treat previous AI answers as authoritative evidence.

For new legal or regulatory claims, use the current
retrieved knowledge base and registered sources.

"""

    else:

        conversation_context = (
            "No previous conversation. "
            "This is the first question."
        )

    # ========================================================
    # JURISDICTION INSTRUCTION
    # ========================================================

    if (
        "India" in detected_jurisdictions
        and "International" in detected_jurisdictions
    ):

        jurisdiction_instruction = """

The question involves both India and international
considerations.

KEEP THESE AREAS STRICTLY SEPARATED.

INDIA:
Discuss only India-specific requirements supported
by India evidence.

INTERNATIONAL:
Discuss only international frameworks supported
by international evidence.

Never present Indian law as international law.

Never present an international framework as an
identical national legal requirement.

"""

    elif "International" in detected_jurisdictions:

        jurisdiction_instruction = """

The question is international in scope.

Prioritize international evidence.

Do not silently substitute Indian law.

If India is relevant, clearly create a separate
India section.

Do not imply that a WIPO or international framework
automatically creates identical requirements in every
country.

"""

    elif "India" in detected_jurisdictions:

        jurisdiction_instruction = """

The question is India-focused.

Prioritize India-specific evidence.

Do not silently substitute foreign requirements.

International frameworks may be mentioned only when
directly relevant and clearly labelled as international.

"""

    else:

        jurisdiction_instruction = """

Use the user's selected jurisdiction as the primary scope.

Do not assume an unstated jurisdiction.

If the answer depends on jurisdiction, clearly state
that verification is required.

"""

    # ========================================================
    # CLASSIFICATION INSTRUCTION
    # ========================================================

    classification_instruction = f"""

PRELIMINARY PRODUCT CLASSIFICATION:

{", ".join(product_classification)}

IMPORTANT CLASSIFICATION RULE:

The preliminary classification supplied above MUST be
preserved exactly in the PRODUCT / FORMULATION CLASSIFICATION
section of the answer.

Do NOT merge it with another category.

Do NOT add alternative categories such as "or Proprietary
Medicine" or "or New Drug" unless the system classification
itself contains multiple categories.

Do NOT override the system classification.

If the system classification is:

"New / Non-Classical Drug"

write exactly:

**Preliminary Classification: New / Non-Classical Drug**

If the system classification is:

"Patent / Proprietary Medicine"

write exactly:

**Preliminary Classification: Patent / Proprietary Medicine**

If the system classification is:

"Classical / Generic Medicine"

write exactly:

**Preliminary Classification: Classical / Generic Medicine**

If the system classification is:

"Phytopharmaceutical"

write exactly:

**Preliminary Classification: Phytopharmaceutical**

If the system classification is:

"Ayurveda-Aahar / Nutraceutical"

write exactly:

**Preliminary Classification: Ayurveda-Aahar / Nutraceutical**

If the system classification is:

"Cosmetic"

write exactly:

**Preliminary Classification: Cosmetic**

If the system classification is:

"Classification requires additional product information"

clearly state that additional information is required.

The classification is a preliminary rule-based signal and
is NOT a legal or regulatory determination.

You may explain what additional facts should be verified,
but do not replace, merge, or weaken the supplied preliminary
classification.

The six IP-SAKTI categories are:

1. Classical / Generic Medicine
2. Patent / Proprietary Medicine
3. New / Non-Classical Drug
4. Phytopharmaceutical
5. Ayurveda-Aahar / Nutraceutical
6. Cosmetic

Relevant verification facts can include:

- intended use
- route of administration
- dosage form
- ingredients
- quantities/concentrations
- product claims
- label
- advertising claims
- classical or proprietary status
- intended market
- whether it is food, medicine or cosmetic

"""

    # ========================================================
    # ABSTENTION INSTRUCTION
    # ========================================================

    if abstention_required:

        abstention_instruction = """

SAFE ABSTENTION IS REQUIRED.

The system has determined that a definitive answer would
be unsafe or insufficiently supported.

You MUST NOT provide a definitive legal or regulatory
conclusion.

Instead:

1. State what the retrieved evidence establishes.
2. State what cannot be established.
3. Identify the missing evidence/facts.
4. Give general educational guidance only.
5. Identify the authority/source that should be verified.
6. Recommend professional review when consequential.

Do not manufacture missing legal details.

"""

    else:

        abstention_instruction = """

SAFE ABSTENTION IS NOT MANDATORY FOR THIS QUESTION.

However, normal grounding and uncertainty rules still apply.

Do not overstate certainty.

"""

    # ========================================================
    # GEMINI PROMPT
    # ========================================================

    try:

        client = genai.Client(
            api_key=api_key
        )

        validated_source_ids = source_validation.get(
            "valid_ids",
            []
        )

        validated_source_ids_text = (
            ", ".join(validated_source_ids)
            if validated_source_ids
            else "None"
        )

        validated_source_instruction = f"""
============================================================
VALIDATED SOURCE IDs FOR THIS RESPONSE
============================================================

ONLY use these validated source IDs:

{validated_source_ids_text}

Do NOT cite or output any other SOURCE ID.

If a claim cannot be associated with one of these validated
source IDs, write:

Source association requires verification.

============================================================
"""
        prompt = f"""

You are IP-SAKTI Sahayak.

You are a multilingual educational information and
decision-support assistant for Intellectual Property
and regulatory guidance related to Ayurveda.

The project is:

"IP-SAKTI Sahayak: A multilingual, RAG-based,
source-cited AI assistant for Intellectual Property
and regulatory guidance in Ayurveda, across national
and international regimes."

Your priority is:

ACCURACY > COMPLETENESS.

============================================================
USER SETTINGS
============================================================

Selected jurisdiction:

{request.jurisdiction}

Selected language:

{request.language}

Detected jurisdictions:

{", ".join(detected_jurisdictions)}

Detected domains:

{", ".join(detected_domains)}

{classification_instruction}

============================================================
CURRENT USER QUESTION
============================================================

{question}

============================================================
PREVIOUS CONVERSATION
============================================================

{conversation_context}

============================================================
JURISDICTION CONTROL
============================================================

{jurisdiction_instruction}

============================================================
RETRIEVED EVIDENCE
============================================================

{evidence}

============================================================
UPLOADED DOCUMENT
============================================================

{
    uploaded_document_text
    if uploaded_document_text
    else
    "No document was uploaded."
}

The uploaded document is USER-PROVIDED MATERIAL.

Do not automatically treat it as an authoritative
government/legal source.

If a claim comes only from the uploaded document,
clearly distinguish it from registered authoritative
sources.

============================================================
SYSTEM EVIDENCE STATUS
============================================================

Evidence strength:

{evidence_strength}

Referenced source IDs:

{
    ", ".join(
        source_validation["referenced_ids"]
    )
    if source_validation["referenced_ids"]
    else
    "None"
}

Valid source IDs:

{
    ", ".join(
        source_validation["valid_ids"]
    )
    if source_validation["valid_ids"]
    else
    "None"
}

Invalid source IDs:

{
    ", ".join(
        source_validation["invalid_ids"]
    )
    if source_validation["invalid_ids"]
    else
    "None"
}

Jurisdiction mismatch IDs:

{
    ", ".join(
        source_validation[
            "jurisdiction_mismatch_ids"
        ]
    )
    if source_validation[
        "jurisdiction_mismatch_ids"
    ]
    else
    "None"
}

Restricted source IDs:

{
    ", ".join(
        source_validation[
            "restricted_ids"
        ]
    )
    if source_validation[
        "restricted_ids"
    ]
    else
    "None"
}

Safe abstention:

{abstention_required}

Human review:

{human_review_required}

System confidence estimate:

{confidence}

{abstention_instruction}

============================================================
{validated_source_instruction}

CORE CONVERSATION RULES
============================================================

1. Answer the CURRENT question directly.

2. Use previous conversation only for context.

3. If the user says "it", "this", "that formulation",
"the product", "the patent", "internationally",
"what about trademark", etc., use previous context
to identify the intended subject.

4. Do not unnecessarily repeat previous answers.

5. Previous AI answers are NOT authoritative evidence.

6. Current retrieved evidence has priority.

============================================================
CRITICAL GROUNDING RULES
============================================================

1. Use retrieved knowledge-base evidence as the primary
evidence source.

2. Do not invent laws, sections, rules, regulations,
treaties, cases, notifications or procedures.

3. Do not fabricate citations.

4. Do not invent source IDs.

5. Only use a source ID if it exists in the supplied
registered source metadata.

6. The existence of a source in the registry does NOT
prove that every claim is supported by that source.

7. If claim-to-source association is uncertain, write:

"Source association requires verification."

8. If evidence is insufficient, write:

"IP-SAKTI does not have sufficient retrieved evidence
to provide a reliable specific conclusion on this point."

9. Provide general educational guidance when specific
evidence is unavailable.

10. Never pretend to be a lawyer, patent attorney,
regulatory authority or government official.

11. Never give definitive legal conclusions when
important facts are missing.

12. Never say a product is definitely patentable.

13. Never say a patent will definitely be granted.

14. Never say a product is definitely legally approved,
registered or compliant unless the retrieved evidence
actually supports that precise conclusion.

15. Never claim that a complete prior-art search was
performed.

16. Never claim that a freedom-to-operate analysis was
performed.

17. Never claim that IP-SAKTI accessed a restricted
database unless the system actually has such access.

18. Clearly distinguish:

- retrieved evidence
- registered source metadata
- user-uploaded material
- plain-language explanation
- preliminary classification
- matters requiring expert verification

============================================================
TKDL SAFETY
============================================================

TKDL-related information must be handled carefully.

IP-SAKTI DOES NOT CLAIM DIRECT ACCESS TO RESTRICTED
TKDL RECORDS.

Do not claim that IP-SAKTI searches restricted TKDL
records unless such functionality actually exists.

If TKDL is mentioned:

- explain its relevance only from available evidence
- distinguish public TKDL/source information from
  restricted database access
- do not claim that IP-SAKTI has access to confidential
  or restricted TKDL records
- do not claim that TKDL guarantees rejection of a patent
- do not claim that TKDL guarantees acceptance or rejection
- recommend appropriate authorised/professional verification
  where necessary

If a TKDL source is marked use_for_rag=false or restricted
in the source registry, it MUST NOT be described as
retrieved RAG evidence.

============================================================
PATENT SAFETY
============================================================

For patent-related questions, explain concepts such as:

- novelty
- inventive step
- industrial applicability
- prior art
- traditional knowledge
- statutory exclusions where supported

But do not provide a definitive patentability conclusion
unless the evidence genuinely supports it.

A knowledge-base retrieval is NOT equivalent to a complete
prior-art search.

For patentability, infringement, validity or FTO questions,
professional patent review should be recommended when
appropriate.

============================================================
BIODIVERSITY / ABS
============================================================

When medicinal plants, biological resources or genetic
resources are involved:

consider where supported by evidence:

- access
- benefit sharing
- biodiversity requirements
- traditional knowledge
- relevant authority
- commercialization implications

Do not assume that every plant automatically creates
the same legal obligation.

Applicability depends on the facts and jurisdiction.

============================================================
PRODUCT CLASSIFICATION
============================================================

Before detailed regulatory guidance, consider:

1. Classical / Generic Medicine
2. Patent / Proprietary Medicine
3. New / Non-Classical Drug
4. Phytopharmaceutical
5. Ayurveda-Aahar / Nutraceutical
6. Cosmetic

Do not force classification.

If classification cannot be determined, say so.

============================================================
OTHER IP RIGHTS
============================================================

Consider only relevant rights:

- Patent
- Trademark
- Copyright
- Geographical Indication
- Industrial Design
- Plant Variety Protection
- Trade Secret
- Traditional Knowledge
- Biodiversity / ABS

Do not recommend every IP right automatically.

Explain relevance.

============================================================
REGULATORY ROUTING
============================================================

Keep these pathways distinct:

- Ayurveda / AYUSH
- drugs / medicines
- food / Ayurveda-Aahar
- nutraceuticals
- cosmetics
- advertising
- labelling
- product claims

Do not merge food, cosmetic and drug requirements.

============================================================
INTERNATIONAL ROUTING
============================================================

When supported by evidence, international frameworks may
include:

- TRIPS
- WIPO systems
- PCT
- Madrid
- Hague
- Lisbon
- Budapest
- CBD
- Nagoya

Do not assume international frameworks create identical
national requirements.

Only discuss frameworks supported by retrieved evidence.

============================================================
HUMAN ESCALATION
============================================================

For:

- litigation
- infringement
- legal notice
- enforcement
- penalties
- FTO
- high-stakes patentability
- regulatory enforcement
- complex regulatory approval

clearly state that professional legal/regulatory
verification is appropriate.

============================================================
ANSWER FORMAT
============================================================

Use this structure where applicable:

### SHORT ANSWER

### PRODUCT / FORMULATION CLASSIFICATION

### IP / REGULATORY AREAS

### INDIA

### INTERNATIONAL

### WHY THIS MATTERS

### RECOMMENDED PATHWAY

### IMPORTANT LIMITATIONS

### RETRIEVED EVIDENCE

For important evidence-supported statements:

Evidence:
[plain-language explanation]

Source ID:
[exact registered source ID]

If association cannot be established:

Source association requires verification.

### AUTHORITATIVE SOURCES TO VERIFY

For relevant registered sources:

SOURCE ID:
AUTHORITY:
DOCUMENT:
JURISDICTION:
OFFICIAL URL:

### CONFIDENCE

Use:

Moderate
Low

High confidence must NOT be used by this system for
legal/regulatory conclusions because IP-SAKTI does not
perform complete external verification.

Confidence refers to evidence support, NOT legal certainty.

### HUMAN REVIEW

Explain when professional review is appropriate.

Information and educational guidance only;
not legal advice.

============================================================
MARKDOWN FORMAT
============================================================

Use NORMAL Markdown.

Do NOT escape Markdown characters.

Correct:

### SHORT ANSWER

**Important**

---

- Point one
- Point two

Incorrect:

\\### SHORT ANSWER

\\*Important\\*

\\---

Do not add unnecessary backslashes before Markdown
headings, bold text, lists or horizontal rules.

============================================================
LANGUAGE
============================================================

Respond in:

{request.language}

If Hindi or Marathi is selected, retain important legal,
scientific and technical terms in English when this
improves precision.

Do not change jurisdiction because of language.

============================================================
FINAL SAFETY REQUIREMENT
============================================================

Accuracy is more important than completeness.

If evidence is missing:

DO NOT GUESS.

If a source association is uncertain:

DO NOT FABRICATE IT.

If a legal conclusion requires professional verification:

SAY SO.

"""

                # ====================================================
        # GEMINI CALL
        # ====================================================

        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt
        )

        answer_text = (
            response.text
            if response.text
            else
            (
                "IP-SAKTI could not generate a response "
                "from the available evidence."
            )
        )

        # ====================================================
        # CLEAN MARKDOWN
        # ====================================================

        answer_text = clean_ai_markdown(
            answer_text
        )

        # ====================================================
        # FINAL SOURCE-ID CHECK
        # ====================================================

        answer_source_ids = extract_source_ids(
            answer_text
        )

        registered_source_ids = {
            str(
                source.get(
                    "source_id",
                    ""
                )
            ).strip()
            for source in source_registry
            if source.get("source_id")
        }

        invalid_answer_source_ids = [
            source_id
            for source_id in answer_source_ids
            if source_id not in registered_source_ids
        ]

        if invalid_answer_source_ids:

            print(
                "WARNING: AI returned unregistered "
                "source IDs:",
                invalid_answer_source_ids
            )

            answer_text += """

### SOURCE VALIDATION NOTICE

One or more source IDs generated in the response could
not be matched to the registered IP-SAKTI source registry.

Those source associations require verification before
being treated as authoritative.

"""

        # ====================================================
        # RESTRICTED SOURCE VALIDATION
        # ====================================================

        restricted_answer_source_ids = [
            source_id
            for source_id in answer_source_ids
            if source_id in source_validation.get(
                "restricted_ids",
                []
            )
        ]

        if restricted_answer_source_ids:

            print(
                "WARNING: AI referenced restricted/non-RAG "
                "source IDs:",
                restricted_answer_source_ids
            )

            answer_text += """

### SOURCE ACCESS NOTICE

A referenced source is marked restricted or non-RAG-eligible
in the IP-SAKTI source registry.

IP-SAKTI does not treat that source as directly retrieved
RAG evidence and does not claim direct access to restricted
records.

Source association and access status require verification.

"""

        # ====================================================
        # SOURCE CONSISTENCY CHECK
        # ====================================================

        answer_source_ids_set = set(
            answer_source_ids
        )

        valid_answer_source_ids = [
            source_id
            for source_id in answer_source_ids_set
            if source_id in source_validation.get(
                "valid_ids",
                []
            )
        ]

        unsupported_answer_source_ids = [
            source_id
            for source_id in answer_source_ids_set
            if (
                source_id not in valid_answer_source_ids
                and source_id not in invalid_answer_source_ids
                and source_id not in restricted_answer_source_ids
            )
        ]

        if unsupported_answer_source_ids:

            print(
                "WARNING: answer source IDs were not "
                "validated against retrieved jurisdiction "
                "evidence:",
                unsupported_answer_source_ids
            )

            answer_text += """

### SOURCE ASSOCIATION NOTICE

One or more cited source IDs were registered but were
not validated as retrieved evidence for the current
jurisdiction/question.

The association requires verification.

"""

        # ====================================================
        # ENFORCE SAFETY NOTICE
        # ====================================================

        if abstention_required:

            safety_notice = """

### SAFETY / VERIFICATION NOTICE

This question requires additional verification before a
definitive legal or regulatory conclusion can be made.
IP-SAKTI provides educational, source-grounded guidance
and does not replace a qualified patent, legal or
regulatory professional.

"""

            if (
                "SAFETY / VERIFICATION NOTICE"
                not in answer_text
            ):

                answer_text += safety_notice

        # ====================================================
        # RETURN
        # ====================================================

        return {

            "status": "success",

            "answer": answer_text,

            "jurisdiction":
                request.jurisdiction,

            "language":
                request.language,

            "detected_domains":
                detected_domains,

            "detected_jurisdictions":
                detected_jurisdictions,

            "product_classification":
                product_classification,

            "confidence":
                confidence,

            "evidence_strength":
                evidence_strength,

            "human_review_required":
                human_review_required,

            "safe_abstention":
                abstention_required,

            "rag_used":
                bool(
                    retrieved_context
                ),

            "source_validation": {

                "referenced_ids":
                    source_validation[
                        "referenced_ids"
                    ],

                "valid_ids":
                    source_validation[
                        "valid_ids"
                    ],

                "invalid_ids":
                    source_validation[
                        "invalid_ids"
                    ],

                "jurisdiction_mismatch_ids":
                    source_validation[
                        "jurisdiction_mismatch_ids"
                    ],

                "restricted_ids":
                    source_validation[
                        "restricted_ids"
                    ],

                "answer_source_ids":
                    answer_source_ids,

                "valid_answer_source_ids":
                    valid_answer_source_ids,

                "invalid_answer_source_ids":
                    invalid_answer_source_ids,

                "unsupported_answer_source_ids":
                    unsupported_answer_source_ids
            },

            "relevant_source_count":
                len(
                    relevant_sources
                ),

            "retrieved_context":
                retrieved_context
        }

    except Exception as e:

        print(
            "AI REQUEST ERROR:",
            repr(e)
        )

        raise HTTPException(
            status_code=500,
            detail=(
                f"AI request failed: {str(e)}"
            )
        )




