# 🤖 Trading AI - Intelligent Signal Processing System

![Trading AI](https://img.shields.io/badge/Trading%20AI-v1.0-blue.svg)
![Python](https://img.shields.io/badge/Python-3.11+-green.svg)
![React](https://img.shields.io/badge/React-19-blue.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

> Ein automatisiertes Trading-System mit Multi-Source Signal Intake, intelligenter Signalfilterung und Paper Trading Engine.

## 🌟 Features

### ✅ Telegram Bot Integration - NEU!
- **@traiding_r2d2_bot** - Sende Signale direkt an den Bot
- Automatisches Signal-Parsing
- Befehle: `/start`, `/help`, `/status`, `/portfolio`

### ✅ Signal Intake (Phase 1) - Fertig
- **Webhook API** - REST API (TradingView-kompatibel) für externe Signale
- **Telegram Bot** - Empfange Signale via Bot-Nachricht
- **Telegram Channel Listener** - Überwacht Channels (Evening Trader, Fat Pig Signals)
- **Multi-Format Parser** - Erkennt automatisch Signal-Formate mit Confidence-Score

### ✅ Paper Trading Engine (Phase 2) - Fertig
- **Risk Manager** - Position Sizing basierend auf Max-Risk, R:R Validation
- **Order Executor** - Market/Limit/SL/TP Order Simulation
- **Position Manager** - Trade Tracking, P&L Berechnung
- **Portfolio Tracker** - Performance-Metriken, Equity Curve

### 📊 Dashboard
- **Real-time Updates** - Live-Aktualisierung aller Daten
- **Signal Cards** - Visuelle Darstellung mit Confidence-Score und R:R Ratio
- **Position Management** - Ein-Klick Trade-Ausführung und Schließung
- **Performance Charts** - Equity Curve, Win Rate, Cumulative P&L

## 🚀 Telegram Bot

Dein Bot: [@traiding_r2d2_bot](https://t.me/traiding_r2d2_bot)

**Signal senden:**
```
BTC/USDT LONG
Entry: 96500
SL: 94000
TP1: 98000
TP2: 100000
Leverage: 5x
```

**Befehle:**
- `/start` - Bot starten
- `/help` - Hilfe anzeigen
- `/status` - System-Status
- `/signal` - Signal-Format Hilfe

### 🛡️ Risk Management
- **Max Risk per Trade** - Konfigurierbar (Standard: 2%)
- **Max Open Positions** - Begrenzt gleichzeitige Trades
- **Risk/Reward Filter** - Mindest-R:R Ratio für Signale
- **Correlation Check** - Verhindert überkonzentrierte Positionen

## 📋 Projektphasen

| Phase | Beschreibung | Status |
|-------|-------------|--------|
| Phase 1 | Signal Intake (Webhook, Parser) | ✅ Fertig |
| Phase 2 | Paper Trading Engine | ✅ Fertig |
| Phase 3 | Context Engine (News, Sentiment) | ⏳ Geplant |
| Phase 4 | Pattern Recognition | ⏳ Geplant |
| Phase 5 | ML Prediction | ⏳ Geplant |
| Phase 6 | Dashboard GUI | ✅ Fertig |
| Phase 7 | Orchestration & Auto-Trading | ⏳ Geplant |

## 🚀 Schnellstart

### Voraussetzungen
- Docker & Docker Compose
- Node.js 18+ (für Entwicklung)
- Python 3.11+ (für Entwicklung)

### Installation mit Docker

```bash
# Repository klonen
git clone https://github.com/robinzi2001-cell/trading-ai.git
cd trading-ai

# .env Datei erstellen
cp .env.example .env

# Container starten
docker-compose up -d

# Logs anzeigen
docker-compose logs -f
```

Das System ist erreichbar unter:
- **Dashboard**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Manuelle Installation

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python server.py

# Frontend (separates Terminal)
cd frontend
yarn install
yarn start
```

## 📁 Projektstruktur

```
trading-ai/
├── backend/
│   ├── models/                 # Pydantic Datenmodelle
│   │   ├── signals.py          # Signal, ParsedSignal
│   │   ├── trading.py          # Trade, Position, Portfolio
│   │   └── settings.py         # Konfiguration
│   ├── services/               # Business Logic
│   │   ├── signal_parser.py    # Multi-Format Signal Parser
│   │   ├── risk_manager.py     # Risikomanagement
│   │   └── trading_engine.py   # Paper Trading Engine
│   └── server.py               # FastAPI Backend
├── frontend/
│   ├── src/
│   │   ├── components/         # React Komponenten
│   │   │   ├── SignalCard.jsx
│   │   │   ├── PositionRow.jsx
│   │   │   ├── MetricCard.jsx
│   │   │   └── Charts.jsx
│   │   ├── pages/              # Seiten
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Signals.jsx
│   │   │   ├── Trades.jsx
│   │   │   ├── Portfolio.jsx
│   │   │   └── Settings.jsx
│   │   └── App.js
│   └── package.json
├── docker-compose.yml
├── Dockerfile
└── README.md
```

## 📡 API Referenz

### Signal Endpoints

| Endpoint | Method | Beschreibung |
|----------|--------|--------------|
| `/api/signals` | GET | Alle Signale abrufen |
| `/api/signals` | POST | Neues Signal erstellen |
| `/api/signals/webhook` | POST | Signal via Webhook (TradingView) |
| `/api/signals/{id}` | DELETE | Signal dismissieren |

### Trade Endpoints

| Endpoint | Method | Beschreibung |
|----------|--------|--------------|
| `/api/trades` | GET | Alle Trades abrufen |
| `/api/trades/open` | GET | Offene Trades |
| `/api/trades/execute` | POST | Trade ausführen |
| `/api/trades/close` | POST | Trade schließen |

### Portfolio & Settings

| Endpoint | Method | Beschreibung |
|----------|--------|--------------|
| `/api/portfolio` | GET | Portfolio-Übersicht |
| `/api/portfolio/stats` | GET | Performance-Statistiken |
| `/api/settings` | GET/PUT | Trading-Einstellungen |
| `/api/health` | GET | Health Check |

### Webhook Beispiel (TradingView)

```json
POST /api/signals/webhook
{
  "text": "BTC/USDT LONG Entry: 95000 SL: 93000 TP: 97000 99000",
  "source_id": "TradingView"
}
```

Oder strukturiert:
```json
POST /api/signals/webhook
{
  "asset": "BTC/USDT",
  "action": "long",
  "entry": 95000,
  "stop_loss": 93000,
  "take_profits": [97000, 99000, 102000],
  "leverage": 3
}
```

## ⚙️ Konfiguration

### Umgebungsvariablen (.env)

```env
# MongoDB
MONGO_URL=mongodb://localhost:27017
DB_NAME=trading_ai

# Binance (für Live Trading - Phase 7)
BINANCE_API_KEY=your_api_key
BINANCE_SECRET=your_secret
BINANCE_TESTNET=true

# Risk Management
MAX_RISK_PER_TRADE=2.0
MAX_OPEN_POSITIONS=5
MIN_RISK_REWARD=1.5

# Signal Sources (Phase 3+)
TELEGRAM_API_ID=your_id
TELEGRAM_API_HASH=your_hash
TELEGRAM_CHANNELS=channel1,channel2
```

### Risk Settings (Dashboard → Settings)

| Parameter | Standard | Beschreibung |
|-----------|----------|--------------|
| Max Risk per Trade | 2% | Max. Risiko pro Trade |
| Max Open Positions | 5 | Max. gleichzeitige Positionen |
| Min Risk/Reward | 1.5 | Mindest R:R Ratio |
| Default Leverage | 1x | Standard-Hebel |

## 🧪 Testing

```bash
# Backend Tests
cd backend
pytest tests/ -v

# API Tests
curl http://localhost:8000/api/health

# Demo Signale erstellen
curl -X POST http://localhost:8000/api/demo/sample-signals

# Demo zurücksetzen
curl -X POST http://localhost:8000/api/demo/reset
```

## 🔮 Roadmap

- [ ] **Phase 3: Context Engine**
  - News API Integration
  - Sentiment Analysis mit FinBERT
  - Market Context Scoring

- [ ] **Phase 4: Pattern Recognition**
  - Chart Pattern Detection
  - Support/Resistance Levels
  - Volume Analysis

- [ ] **Phase 5: ML Prediction**
  - XGBoost/LightGBM Models
  - Signal Quality Prediction
  - Risk-adjusted Recommendations

- [ ] **Phase 7: Live Trading**
  - Binance Integration (Testnet + Live)
  - MetaTrader 5 Support
  - Interactive Brokers Integration

## 🤝 Contributing

1. Fork das Repository
2. Feature Branch erstellen (`git checkout -b feature/AmazingFeature`)
3. Änderungen committen (`git commit -m 'Add AmazingFeature'`)
4. Branch pushen (`git push origin feature/AmazingFeature`)
5. Pull Request erstellen

## 📄 Lizenz

MIT License - siehe [LICENSE](LICENSE) Datei.

## ⚠️ Disclaimer

**Dieses System ist für Bildungs- und Demonstrationszwecke gedacht.**

Trading mit Kryptowährungen und anderen Finanzinstrumenten birgt erhebliche Risiken. Vergangene Performance ist kein Indikator für zukünftige Ergebnisse. Handeln Sie nur mit Kapital, dessen Verlust Sie sich leisten können.

---

<p align="center">
  Built with ❤️ for the trading community
</p>
