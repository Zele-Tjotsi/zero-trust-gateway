# Zero-Trust API Gateway

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com)
[![MIT License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Render](https://img.shields.io/badge/Deployed-Render-purple.svg)](https://render.com)

**Production-ready API gateway with JWT authentication, rate limiting, and ML fraud detection.**

---

## Live Demo

| Resource | URL |
|----------|-----|
| Swagger UI | https://zero-trust-gateway-s592.onrender.com/docs |
| API Root | https://zero-trust-gateway-s592.onrender.com |
| Health Check | https://zero-trust-gateway-s592.onrender.com/health |

> Free tier spins down after inactivity. First request takes ~30 seconds.

---

## Features

- JWT authentication with role-based access (Admin/Analyst/Readonly)
- API key generation with rate limiting (100-10,000 requests/day)
- Random Forest fraud detection model (91% recall)
- Redis-backed rate limiting
- OpenAPI/Swagger documentation

---

## Tech Stack

FastAPI + JWT + Redis + Scikit-learn + Pandas + Uvicorn

---

## Quick Start

```bash
git clone https://github.com/Zele-Tjotsi/zero-trust-gateway.git
cd zero-trust-gateway
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -c "from app.models.ml_model import fraud_detector; fraud_detector.train()"
uvicorn app.main:app --reload --port 8000
```

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | /health | No | Health check |
| POST | /auth/register | No | Create account |
| POST | /auth/login | No | Get JWT token |
| GET | /auth/me | JWT | Current user |
| POST | /predict/ | JWT + API Key | Fraud score |
| POST | /predict/batch | JWT + API Key | Batch scoring |

---

## Example Requests

### Register

```bash
curl -X POST https://zero-trust-gateway-s592.onrender.com/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","name":"John","password":"Pass123!","role":"analyst"}'
```

### Login

```bash
curl -X POST https://zero-trust-gateway-s592.onrender.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"Pass123!"}'
```

### Fraud Prediction

```bash
curl -X POST https://zero-trust-gateway-s592.onrender.com/predict/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{"transaction_id":"TXN_001","amount":25000,"hour":3,"day_of_week":6,"user_avg_amount":100,"user_tx_count":5,"device_fingerprint_match":0,"location_distance_km":300}'
```

---

## Project Structure

```
zero-trust-gateway/
├── app/
│   ├── main.py           # FastAPI entry point
│   ├── models/           # User + ML models
│   ├── routes/           # Auth + Predict endpoints
│   └── services/         # JWT + Rate limiting
├── data/                 # Trained model storage
├── tests/                # Unit tests
├── requirements.txt
├── Procfile
└── README.md
```

---

## Model Performance

| Metric | Score |
|--------|-------|
| Recall | 91% |
| Precision | 31% |
| Accuracy | 44% |

---

## Author

**Zele Tjotsi** - BSc Computer Science, National University of Lesotho

- GitHub: https://github.com/Zele-Tjotsi
- Project: https://github.com/Zele-Tjotsi/zero-trust-gateway
- Live API: https://zero-trust-gateway-s592.onrender.com

## License

MIT
