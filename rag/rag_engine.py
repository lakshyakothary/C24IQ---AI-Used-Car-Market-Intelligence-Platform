"""
C24-IQ: RAG (Retrieval-Augmented Generation) Engine
Uses Anthropic API to power an intelligent car market assistant.
Knowledge base: domain facts + live DB context injected at query time.
"""

import json
import time
import re
import os

# ─── Static Knowledge Base ────────────────────────────────────────────────────

KNOWLEDGE_BASE = [
    {
        "id": "kb_001",
        "category": "Depreciation",
        "title": "Depreciation Rates for Used Cars in India",
        "content": """
Used car depreciation in India follows well-established patterns:
- Year 1: ~18-20% depreciation from ex-showroom price
- Year 2: ~15% additional depreciation
- Year 3: ~12% additional depreciation
- Year 4-5: ~8-10% per year
- Beyond 5 years: ~6-8% per year
SUVs depreciate slower than hatchbacks due to higher demand.
Electric vehicles depreciate ~22-25% in year 1 due to battery concerns.
Popular brands like Maruti and Hyundai hold value better than premium brands.
        """.strip()
    },
    {
        "id": "kb_002",
        "category": "Pricing",
        "title": "Used Car Pricing Factors",
        "content": """
Key factors affecting used car prices in India:
1. Brand & Model: Maruti, Hyundai command 5-8% premium over others
2. Fuel Type: Diesel cars cost 10-15% more but save on running costs
3. Age: Each year reduces value by 8-20% depending on segment
4. KM Driven: Beyond 12,000 km/year average, price drops ~3% per 10,000 km excess
5. Owner History: Second owner: -8%, Third: -12%, Fourth+: -20%
6. Condition Grade: Excellent(+8%), Good(base), Fair(-10%), Poor(-22%)
7. Insurance: Valid insurance adds ~2% premium
8. Accident History: Each accident reduces value by ~5%
9. Service Records: Full service records add ~3% premium
10. City: Mumbai/Gurgaon cars command 15-20% premium over Tier-2 cities
        """.strip()
    },
    {
        "id": "kb_003",
        "category": "Market Trends",
        "title": "Indian Used Car Market Overview 2024",
        "content": """
Indian Used Car Market Statistics:
- Market size: ~4.4 million units annually (2024)
- Growing at ~15% CAGR
- Organized sector (Cars24, CarDekho, Spinny) commands ~35% market share
- Average transaction price: ₹5-7 Lakhs
- Most popular segment: Hatchbacks (45%), SUVs (30%), Sedans (20%)
- Top cities by volume: Delhi NCR, Mumbai, Bangalore, Hyderabad, Pune
- Festive season (Sep-Nov) sees 25-30% volume spike
- Electric vehicle used car segment growing at 40% YoY
- Average days to sell: Hatchback (12 days), SUV (18 days), Sedan (15 days)
        """.strip()
    },
    {
        "id": "kb_004",
        "category": "Buying Tips",
        "title": "Car Buying Checklist",
        "content": """
Essential checks when buying a used car:
DOCUMENTATION: RC book, insurance, pollution certificate, service history, loan NOC
INSPECTION: Engine health, transmission smoothness, AC performance, rust check
HISTORY: Check accident history via VAHAN portal, odometer tampering
TEST DRIVE: Cold start performance, braking, steering, noise levels
LEGAL: Verify no challan dues, no hypothecation
PRICING: Compare with market price using 3-5 similar listings
NEGOTIATION: Budget for 3-8% price reduction from listed price
Recommended: Always get a pre-purchase inspection from a certified mechanic
        """.strip()
    },
    {
        "id": "kb_005",
        "category": "Selling Tips",
        "title": "How to Get Best Price When Selling",
        "content": """
Maximize your car's resale value:
TIMING: Sell before the car crosses 5 years (higher depreciation cliff)
PRESENTATION: Professional cleaning and minor denting/painting can add 5-8%
DOCUMENTATION: Complete service history increases buyer confidence and price
PLATFORM: Online platforms (Cars24, OLX) give wider reach vs dealers
PRICING: Start 8-10% above your target to allow negotiation room
CERTIFICATION: Cars24 CERT certification program adds 10-15% trust premium
AVOID: Selling in monsoon season (June-August) — lower demand
BEST TIME: October-November (festive) or March-April (year-end bonuses)
        """.strip()
    },
    {
        "id": "kb_006",
        "category": "Finance",
        "title": "Used Car Loan Guide",
        "content": """
Used Car Loan in India:
- Interest rates: 8.5% to 16% depending on credit score and car age
- Loan-to-Value (LTV): Up to 85% of car value
- Tenure: 12 to 84 months
- Eligibility: Credit score above 650 recommended
- Documents: Income proof, address proof, ID proof, car RC
- EMI thumb rule: EMI should not exceed 15% of monthly income
- Cars older than 10 years typically not eligible for loans
- Pre-approved loans from Cars24 Finance available in 30 minutes
- Zero foreclosure charges after 6 months (Cars24 Finance)
Credit Score Impact:
750+: Best rates (8.5-10%)
700-749: Good rates (10-12%)
650-699: Average rates (12-14%)
Below 650: High rates or rejection (14-16%)
        """.strip()
    },
    {
        "id": "kb_007",
        "category": "EV",
        "title": "Electric Vehicle Used Car Market",
        "content": """
Used Electric Vehicles in India:
Popular models: Tata Nexon EV, MG ZS EV, Hyundai Kona, Tata Tigor EV
Battery health: Check State of Health (SOH) — ideal is >80%
Range anxiety: Real-world range is 20-30% less than claimed
Charging: Check home charging compatibility (15A socket vs wallbox)
Warranty: Most EV batteries have 8-year/160,000 km warranty (transferable)
Depreciation: Year 1 = 22-25% (higher than ICE), then stabilizes
Cost of ownership: EV running cost ~₹1/km vs ICE ₹5-8/km
Servicing: 40% lower maintenance costs vs ICE vehicles
Government incentives: FAME-II subsidies apply to new; used EVs no subsidy
Price range for used EVs: ₹8-25 Lakhs depending on model and age
        """.strip()
    },
    {
        "id": "kb_008",
        "category": "Cars24",
        "title": "Cars24 Business Model and Services (illustrative)",
        "content": """
Illustrative summary, not official Cars24 information (verify details on cars24.com).
Cars24 is a large Indian used-car platform:
SELL: Instant price quote, sell in 30 minutes, doorstep pickup available
BUY: 15,000+ cars listed, 6-month warranty, 7-day return policy
FINANCE: LOANS24 subsidiary, pre-approved in 30 minutes
NEW CARS: New car listings with best OEM prices
SERVICES: Challan check, RTO details, car service history, pre-delivery inspection
CERTIFICATION: CARS24 Certified — 140-point inspection, guaranteed history
COVERAGE: 130+ cities across India
KEY FEATURES:
- Instant price evaluation using AI
- Zero paperwork hassle
- Assured buyback program
- Partner workshops for post-purchase service
        """.strip()
    },
    {
        "id": "kb_009",
        "category": "Valuation",
        "title": "Car Valuation Methods",
        "content": """
Methods for valuing used cars:
1. MARKET COMPARISON: Compare with 5+ similar listings in your city
2. DEPRECIATION METHOD: Apply standard depreciation to ex-showroom price
3. AI PRICE ENGINES: Cars24, CarDekho AI tools use 50+ parameters
4. BANK VALUATION: Banks use Valuation Reports for loan purposes
5. INSURER VALUATION: IDV (Insured Declared Value) = depreciated value

Price Influencers (weightage):
- Brand/Model: 30%
- Age: 25%
- KM Driven: 15%
- Condition: 12%
- Location: 8%
- Features/Variant: 7%
- Color: 3%

About the C24-IQ price engine (trained on synthetic data): it trains XGBoost, Gradient Boosting, Random Forest, Ridge and ElasticNet models plus a weighted blend of all five.
On the held-out test split XGBoost is the best model (R² about 0.986, MAPE about 5%); the blend scores slightly lower (R² about 0.968).
These numbers come from synthetic data, so they validate the pipeline rather than real-world accuracy.
        """.strip()
    },
]


def retrieve_relevant_chunks(query: str, top_k: int = 4) -> list:
    """Simple TF-IDF-style keyword matching for chunk retrieval."""
    query_words = set(re.sub(r"[^a-z0-9 ]", "", query.lower()).split())
    
    scores = []
    for chunk in KNOWLEDGE_BASE:
        text = (chunk["title"] + " " + chunk["content"] + " " + chunk["category"]).lower()
        text_words = set(re.sub(r"[^a-z0-9 ]", "", text).split())
        overlap = len(query_words & text_words)
        scores.append((overlap, chunk))
    
    scores.sort(key=lambda x: -x[0])
    return [chunk for _, chunk in scores[:top_k]]


class AIConfigError(RuntimeError):
    """Raised when no Claude API key can be found."""


_DOTENV_PATH = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))


def _read_dotenv(path: str) -> dict:
    """Tiny .env reader (KEY=VALUE per line), so no terminal setup is needed on Windows."""
    values = {}
    try:
        with open(path, encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                values[key.strip()] = val.strip().strip('"').strip("'")
    except OSError:
        pass
    return values


def _setting(name: str, default: str = "") -> str:
    """Environment variable first, then the .env file in the project root."""
    value = os.environ.get(name) or _read_dotenv(_DOTENV_PATH).get(name) or default
    return value.strip().strip('"').strip("'")


def get_api_key() -> str:
    return _setting("ANTHROPIC_API_KEY")


def get_model() -> str:
    return _setting("ANTHROPIC_MODEL", "claude-sonnet-5-5")


def call_anthropic_api(messages: list, system: str) -> dict:
    """Call the Anthropic Messages API over plain HTTPS (no SDK needed)."""
    import urllib.request
    import urllib.error

    api_key = get_api_key()
    if not api_key:
        raise AIConfigError(
            "no API key found. Set ANTHROPIC_API_KEY in the terminal that runs the app, "
            "or put ANTHROPIC_API_KEY=... in a file named .env in the project folder")

    payload = json.dumps({
        "model": get_model(),
        "max_tokens": 1000,
        "system": system,
        "messages": messages,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
            "x-api-key": api_key,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        try:
            detail = json.loads(body)["error"]["message"]
        except Exception:
            detail = body[:200]
        raise RuntimeError(f"HTTP {e.code}: {detail}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"network error: {e.reason}") from e


class CarAssistant:
    """RAG-powered car market assistant."""

    def __init__(self):
        self.conversation_history = []

    def query(self, user_query: str, market_context: dict = None) -> dict:
        """Answer a car-related question using RAG."""
        t0 = time.time()

        # Step 1: Retrieve relevant knowledge chunks
        chunks = retrieve_relevant_chunks(user_query)
        context_text = "\n\n---\n\n".join(
            f"[{c['category']}] {c['title']}:\n{c['content']}" for c in chunks
        )

        # Step 2: Inject live market context if available
        market_ctx = ""
        if market_context:
            market_ctx = f"""
LIVE MARKET DATA (from C24-IQ database):
- Total Listings: {market_context.get('total', 'N/A'):,}
- Average Price: ₹{market_context.get('avg_price', 0):,.0f}
- Most Listed Brand: {market_context.get('top_brand', 'N/A')}
- Top City by Volume: {market_context.get('top_city', 'N/A')}
- Average Days on Market: {market_context.get('avg_days', 'N/A'):.1f}
"""

        # Step 3: Build system prompt
        system_prompt = f"""You are C24-IQ, an AI assistant for the Indian used-car market, built as a portfolio project inspired by the Cars24 marketplace.
You have deep knowledge of:
- Indian used car market pricing and trends
- Car depreciation, valuation methodologies
- Car buying/selling best practices in India
- Auto finance and loan products
- Electric vehicles in Indian market
- Cars24's services and processes

Answer questions accurately, concisely, and helpfully. When giving prices, always mention they are estimates.
Use Indian number formatting (Lakhs, Crores) for prices.
Be friendly, professional, and data-driven.
You are an independent demo assistant, not affiliated with Cars24. Details about Cars24 in the knowledge base are illustrative and may be out of date: if asked about Cars24's actual prices, policies or offers, say you cannot confirm them and point to cars24.com.
Write in short paragraphs and use simple hyphen bullets; avoid headings and tables.

KNOWLEDGE BASE:
{context_text}

{market_ctx}"""

        # Step 4: Build conversation
        messages = self.conversation_history[-6:] + [
            {"role": "user", "content": user_query}
        ]

        # Step 5: Call API
        try:
            response = call_anthropic_api(messages, system_prompt)
            answer = "".join(b.get("text", "") for b in response.get("content", [])
                             if b.get("type") == "text").strip()
            if not answer:
                raise RuntimeError("the model returned an empty response")
            self.conversation_history.append({"role": "user", "content": user_query})
            self.conversation_history.append({"role": "assistant", "content": answer})
        except Exception as e:
            print(f"[RAG] Claude call failed -> {e}", flush=True)
            fallback = chunks[0]["content"][:700] if chunks else "No matching knowledge-base entry."
            answer = (f"The AI service could not be reached: {e}\n\n"
                      f"Closest knowledge-base entry:\n{fallback}")

        elapsed_ms = int((time.time() - t0) * 1000)

        return {
            "answer": answer,
            "sources": [{"id": c["id"], "title": c["title"], "category": c["category"]}
                        for c in chunks],
            "response_time_ms": elapsed_ms,
        }

    def reset(self):
        self.conversation_history = []


car_assistant = CarAssistant()
