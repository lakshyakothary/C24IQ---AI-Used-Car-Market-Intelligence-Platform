# C24-IQ: Cars24 Intelligence Quotient

**An end-to-end ML and GenAI platform for used-car pricing, market intelligence and buyer assistance.**

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![Flask 3](https://img.shields.io/badge/flask-3.x-lightgrey)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

> Independent portfolio project inspired by the Cars24 marketplace. It is **not affiliated with or endorsed by Cars24**, and **all data in it is synthetic**.

C24-IQ predicts a fair price for a used car, flags unusual listings, projects demand, answers buyer and seller questions with a Claude-powered RAG assistant, and streams new listings to a live dashboard. It runs as one Flask app with seven interactive pages and 18 REST endpoints.


## What it does

| Module | What it does |
|---|---|
| Price predictor | Fair-value estimate with a range, a confidence score, a per-model breakdown and a depreciation stage |
| Anomaly detection | An Isolation Forest flags listings whose attribute profile is unusual, for human review |
| Demand outlook | A baseline 30-day projection of listing volume |
| AI assistant | RAG over a nine-entry knowledge base plus live SQL statistics; Claude writes the answer and the UI shows its sources |
| Real-time feed | A Server-Sent Events stream of new listings, plus an ingest API that stores events |
| Dashboard and analytics | Brand, city, segment and fuel views, price trends, an EMI calculator, feature importances and a model comparison |
| Listings explorer | Filter 5,000 listings by brand, city, segment, fuel and price |

## The finding I like most

My weighted ensemble scored **worse** than XGBoost alone (R² about 0.97 against about 0.986). The inverse-MAE weighting still gave over a quarter of the blend to weaker models. For one test car XGBoost predicted roughly ₹2.4–2.5 lakh while ElasticNet predicted roughly ₹6.8–6.9 lakh, which drags the blend upwards. Fixes (pruning weak members, out-of-fold weights, true stacking) are on the roadmap.

## Results

Hold-out set of 1,000 synthetic listings (80/20 split). Ranges cover two independently generated datasets: the generator ends its date range on the day it runs, so every fresh clone gets a slightly different dataset. Check `http://localhost:5000/api/model_metrics` for yours.

| Model | R² | MAE | MAPE |
|---|---|---|---|
| XGBoost | ≈ 0.986 | ≈ ₹31–34K | ≈ 5% |
| Gradient Boosting | ≈ 0.981 | ≈ ₹37–41K | ≈ 6% |
| Weighted blend of all five | ≈ 0.968–0.970 | ≈ ₹46–52K | ≈ 7–8% |
| Random Forest | ≈ 0.92–0.93 | ≈ ₹80–83K | ≈ 12% |
| Ridge | ≈ 0.61–0.63 | ≈ ₹178–190K | ≈ 32% |
| ElasticNet | ≈ 0.04 | ≈ ₹318–335K | ≈ 73–74% |

**Caveat:** the data is synthetic, so these numbers validate the pipeline, not real-world accuracy.

## Architecture

```
                 Browser (Jinja2 pages + Chart.js + EventSource)
                                   |
                                   v
   +------------------------ Flask app (app.py) -------------------------+
   |  7 page routes    18 REST endpoints    SSE stream    bootstrap()    |
   +----------+--------------------+-------------------+-----------------+
              |                    |                   |
              v                    v                   v
        ML engine             RAG engine         Database manager
     (ml/ml_engine.py)    (rag/rag_engine.py)  (database/db_manager.py)
     5 regressors +        9-entry KB +         SQLite: 6 tables,
     blend, Isolation      keyword retrieval    4 indexes, queries,
     Forest, forecaster    + Claude API call    audit logs
              ^                    |                   ^
              |                    v                   |
     models/price_engine.pkl   Anthropic API     data/c24iq.db
                                                       ^
                                                       |
                                    Data generator (data/data_generator.py)
```

## Tech stack

**Used in this project:** Python, Pandas, NumPy, scikit-learn, XGBoost, Flask and Jinja2, SQLite, the Anthropic Messages API (Claude), Chart.js, Server-Sent Events.

**Planned:** PostgreSQL, MLflow, Docker and Kubernetes, embeddings with FAISS, SHAP, Kafka, pytest with CI.

## Quick start

Requires Python 3.10 or newer (developed on 3.12) and an internet connection, because charts, icons and fonts load from CDNs.

**Windows (PowerShell)**

```powershell
git clone https://github.com/YOUR-USERNAME/c24-iq-used-car-intelligence.git
cd c24-iq-used-car-intelligence
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python app.py
```

**macOS / Linux**

```bash
git clone https://github.com/YOUR-USERNAME/c24-iq-used-car-intelligence.git
cd c24-iq-used-car-intelligence
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```

Open http://localhost:5000. The first start generates 5,000 listings and trains the models, which is usually well under two minutes; later starts take seconds.

**AI assistant (optional).** The assistant needs an Anthropic API key with credit (create one in the Claude Console under Settings, then API keys). Create `.env`, replace `your-key-here` with your key and save. Without a key everything else works, and the assistant replies with the failure reason plus the closest knowledge-base entry. Run `python test_key.py` to check the connection. Never commit `.env`.

## How it works

- **Data.** A seeded generator builds 5,000 listings (10 brands, 41 models, 12 cities) and 1,000 loan applications from depreciation curves, city demand multipliers and condition, owner, accident and mileage effects.
- **ML.** 29 features (12 engineered, such as km per year and an ownership penalty) go through one-hot encoding and robust scaling into five regressors (XGBoost, Gradient Boosting, Random Forest, Ridge, ElasticNet). A weighted blend, a price range from the Random Forest tree spread, and an Isolation Forest sit on top.
- **RAG.** Question, then top-4 keyword retrieval over the knowledge base, then live SQL statistics, then a prompt, then Claude, then an answer with sources. Every exchange is logged to SQLite.
- **Real time.** `/api/stream/sse` pushes a synthetic listing every 1.5 seconds; `/api/stream/ingest` stores batches in a `stream_events` table.

## API summary

| Endpoint | Purpose |
|---|---|
| `GET /api/kpis` | Platform KPIs |
| `GET /api/brand_distribution`, `/api/city_heatmap`, `/api/price_trend`, `/api/segment_analysis` | Dashboard data |
| `GET /api/model_metrics`, `/api/models/info` | Model quality, importances and blend weights |
| `GET /api/demand_forecast` | Historical and projected listing volume |
| `POST /api/predict` | Price prediction for a car |
| `POST /api/emi_calculate` | Loan EMI and amortisation schedule |
| `GET /api/listings`, `/api/listings/stats` | Filtered listings and aggregates |
| `GET /api/anomalies` | Unusual listings flagged by the Isolation Forest |
| `POST /api/chat`, `/api/chat/reset` | RAG assistant and history reset |
| `GET /api/stream/sse`, `POST /api/stream/ingest`, `GET /api/stream/events` | Real-time feed and event log |

## Project structure

```
c24iq/
├── app.py                  Flask app: routes, bootstrap, SSE
├── test_key.py             Claude connection test
├── requirements.txt        Python dependencies
├── .env.example            Template for local secrets (copy to .env)
├── data/data_generator.py  Synthetic data generator
├── database/db_manager.py  Schema and queries
├── ml/ml_engine.py         ML engine
├── rag/rag_engine.py       RAG assistant
└── templates/              Seven pages plus the base layout
```

Generated on first run and not committed: `data/c24iq.db` and `models/price_engine.pkl`.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `No module named '_loss'` on start | The model cache was made with a different scikit-learn version. Delete `models/price_engine.pkl` and restart |
| Charts or icons missing | The CDN assets are blocked or there is no internet connection |
| The assistant shows a failure message | Run `python test_key.py`. HTTP 401 means the key is wrong, HTTP 400 mentioning credit means the balance is empty, HTTP 404 mentioning the model means set `ANTHROPIC_MODEL` in `.env` |
| Port 5000 already in use | Stop the other running copy of the app |

## Known limitations

- Data is synthetic, so metrics validate the pipeline only, and rupee values are not market quotes.
- The predictor returns the weighted blend, which is less accurate than XGBoost alone.
- The car model name is not a feature, so brand and segment drive the prediction.
- `demand_index` is computed differently at prediction time than in training (about a 10% price shift in one example); a one-line fix is planned for v1.1.
- The feature-impact bars are a heuristic illustration, not SHAP. The price range and confidence score are model-spread heuristics, not calibrated intervals.
- The anomaly detector is unsupervised and flags unusual attribute profiles (rare segments such as EVs are flagged more often). It does not detect fraud.
- The demand outlook is a baseline projection, not a validated forecasting model.
- The generator ends its date range on the day it runs, so a fresh clone generates a slightly different dataset (fix planned for v1.1).
- Retrieval is keyword-based over nine illustrative entries, and the knowledge text is not from official sources.
- SQLite only, with no authentication, rate limiting, automated tests or deployment pipeline yet.

## Roadmap

- **v1.1:** serve XGBoost or a pruned blend, fix `demand_index`, fix the generator's end date, align UI text with this README.
- **v1.2:** model name as a feature, cross-validation and tuning, a stacking meta-learner, TreeSHAP, pytest with GitHub Actions, a Dockerfile.
- **v2.0:** PostgreSQL, embeddings with FAISS and hybrid retrieval, a RAG evaluation set, MLflow, Docker Compose and Kubernetes, Kafka ingestion, time-based validation on real data.

## License and author

MIT licensed; see [LICENSE](LICENSE). Built by Lakshya. www.linkedin.com/in/lakshyakothary [LinkedIn]
