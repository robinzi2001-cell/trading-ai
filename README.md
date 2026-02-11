# 🤖 Trading AI - Automatisiertes Trading Signal System

![Version](https://img.shields.io/badge/Version-2.0-blue.svg)
![Status](https://img.shields.io/badge/Status-Production-green.svg)
![Python](https://img.shields.io/badge/Python-3.11+-green.svg)
![React](https://img.shields.io/badge/React-19-blue.svg)

> Ein vollautomatisiertes Trading-System mit Multi-Source Signal Intake, KI-gestützter Signalanalyse, automatischer Trade-Ausführung und Echtzeit-Benachrichtigungen.

---

## 📋 Inhaltsverzeichnis

1. [Features Übersicht](#-features-übersicht)
2. [System-Architektur](#-system-architektur)
3. [Installation](#-installation)
4. [Konfiguration](#-konfiguration)
5. [Signal-Quellen](#-signal-quellen)
6. [KI-Analyse](#-ki-analyse)
7. [Auto-Execute](#-auto-execute)
8. [API Dokumentation](#-api-dokumentation)
9. [Dashboard](#-dashboard)
10. [Aktueller Status](#-aktueller-status)
11. [Roadmap & TODOs](#-roadmap--todos)

---

## 🌟 Features Übersicht

### ✅ Implementiert

| Feature | Status | Beschreibung |
|---------|--------|--------------|
| **Telegram Bot** | 🟢 Aktiv | @traiding_r2d2_bot - Empfängt manuelle Signale |
| **Channel Monitor** | 🟢 Aktiv | Überwacht Evening Trader & Fat Pig Signals |
| **KI Signal-Analyse** | 🟢 Aktiv | GPT-4o analysiert jedes Signal |
| **Auto-Execute** | 🟢 Aktiv | Automatische Trade-Ausführung |
| **Binance Testnet** | 🟢 Verbunden | $5,000 USDT Testguthaben |
| **X/Twitter Analyse** | 🟢 Aktiv | Trump, Elon Musk, etc. |
| **Benachrichtigungen** | 🟢 Aktiv | Telegram-Alerts |
| **Paper Trading** | 🟢 Aktiv | Risikofrei testen |
| **Risk Management** | 🟢 Aktiv | Position Sizing, R:R Validation |
| **Dashboard** | 🟢 Aktiv | Real-time UI |

### 📊 Statistiken (Live)

- **Telegram Bot**: @traiding_r2d2_bot
- **Überwachte Channels**: 2 (Evening Trader, Fat Pig Signals)
- **Binance Balance**: $5,000 USDT (Testnet)
- **Auto-Execute**: Aktiviert (Max. 10 Trades/Tag)

---

## 🏗 System-Architektur

```
┌─────────────────────────────────────────────────────────────────┐
│                      SIGNAL QUELLEN                              │
├─────────────┬─────────────┬─────────────┬─────────────┬─────────┤
│  Telegram   │  Telegram   │   Webhook   │   Email     │ X/Twitter│
│    Bot      │  Channels   │    API      │   (IMAP)    │  Monitor │
│  @r2d2_bot  │ Evening/Fat │ TradingView │   Coming    │  Trump+  │
└──────┬──────┴──────┬──────┴──────┬──────┴──────┬──────┴────┬────┘
       │             │             │             │           │
       └─────────────┴─────────────┴─────────────┴───────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                     SIGNAL PARSER                                │
│  • Multi-Format Erkennung (Evening Trader, Fat Pig, etc.)       │
│  • Confidence Score Berechnung                                   │
│  • Asset, Entry, SL, TP Extraktion                              │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                     KI ANALYSE (GPT-4o)                          │
│  • Signal Qualitätsbewertung (0-100)                            │
│  • Risk/Reward Analyse                                           │
│  • Markt-Sentiment Bewertung                                     │
│  • Execute/Reject Empfehlung                                     │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                     AUTO-EXECUTE ENGINE                          │
│  • Min. AI Score Check (60)                                      │
│  • Min. Confidence Check (60%)                                   │
│  • Daily Limit Check (10/Tag)                                    │
│  • Risk Manager Validation                                       │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
┌───────────────────────────┐   ┌───────────────────────────────┐
│     PAPER TRADING         │   │      BINANCE TESTNET          │
│   (Simulierte Trades)     │   │    (Echte Testnet Orders)     │
└───────────────────────────┘   └───────────────────────────────┘
                    │                           │
                    └─────────────┬─────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                   BENACHRICHTIGUNGEN                             │
│  • Telegram Bot sendet Alerts                                    │
│  • Signal erkannt → AI Analyse → Trade ausgeführt               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Installation

### Voraussetzungen

- Docker & Docker Compose
- Node.js 18+ (für Entwicklung)
- Python 3.11+ (für Entwicklung)
- MongoDB
- Telegram Account
- Binance Testnet Account

### Docker Installation

```bash
# Repository klonen
git clone https://github.com/robinzi2001-cell/trading-ai.git
cd trading-ai

# .env Dateien erstellen
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Container starten
docker-compose up -d
```

### Manuelle Installation

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd frontend
yarn install
yarn start
```

---

## ⚙️ Konfiguration

### Backend Environment (.env)

```env
# MongoDB
MONGO_URL=mongodb://localhost:27017
DB_NAME=trading_ai

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token

# Telegram User API (für Channel Monitor)
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash

# Binance Futures Testnet
BINANCE_API_KEY=your_api_key
BINANCE_SECRET=your_secret
BINANCE_TESTNET=true

# AI (Emergent LLM Key)
EMERGENT_LLM_KEY=your_key
```

### Telegram Bot Setup

1. Erstelle Bot bei @BotFather
2. Kopiere Token in `.env`
3. Bot ist erreichbar unter: https://t.me/traiding_r2d2_bot

### Telegram Channel Monitor Setup

1. Gehe zu https://my.telegram.org
2. Erstelle App und kopiere API_ID + API_HASH
3. Führe Login aus:
   ```bash
   cd backend
   python services/telegram_channel_monitor.py --login
   ```

### Binance Testnet Setup

1. Erstelle Account: https://testnet.binancefuture.com
2. Generiere API Keys
3. Trage in `.env` ein

---

## 📡 Signal-Quellen

### 1. Telegram Bot (@traiding_r2d2_bot)

Sende Signale direkt an den Bot:

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

### 2. Telegram Channels (Automatisch)

Überwachte Channels:
- **Evening Trader** (@eveningtrader) - Hohe Frequenz
- **Fat Pig Signals** (@fatpigsignals) - Klares Format

Signale werden automatisch erkannt und verarbeitet.

### 3. Webhook API (TradingView)

```bash
POST /api/signals/webhook
Content-Type: application/json

{
  "text": "BTC/USDT LONG Entry: 96500 SL: 94000 TP: 98000"
}
```

Oder strukturiert:
```json
{
  "asset": "BTC/USDT",
  "action": "long",
  "entry": 96500,
  "stop_loss": 94000,
  "take_profits": [98000, 100000],
  "leverage": 3
}
```

---

## 🧠 KI-Analyse

### Signal-Analyse

Jedes Signal wird von GPT-4o analysiert:

```json
{
  "score": 75,
  "quality": "good",
  "should_execute": true,
  "reasoning": "Gutes R:R Verhältnis von 1:2, klare Levels...",
  "risk_assessment": "Moderate Volatilität erwartet",
  "position_size_multiplier": 1.0,
  "warnings": ["Erhöhte Volatilität möglich"]
}
```

**Qualitätsstufen:**
- `excellent` (90-100): Sofort ausführen
- `good` (70-89): Standard-Größe
- `moderate` (50-69): Reduzierte Größe
- `poor` (30-49): Manuell prüfen
- `reject` (0-29): Nicht ausführen

### X/Twitter Analyse

Analysiert Posts von einflussreichen Personen:

**Überwachte Accounts:**
| Account | Kategorie | Impact |
|---------|-----------|--------|
| @realDonaldTrump | Politics | 2.0x |
| @elonmusk | Crypto | 2.0x |
| @michael_saylor | Crypto | 1.5x |
| @VitalikButerin | Crypto | 1.5x |
| @caborai (CZ) | Crypto | 1.5x |

**Analyse-Ergebnis:**
```json
{
  "impact_score": 85,
  "sentiment": "bullish",
  "affected_assets": ["BTC", "ETH"],
  "suggested_action": "long",
  "urgency": "immediate",
  "reasoning": "Starke bullische Aussage..."
}
```

---

## ⚡ Auto-Execute

### Konfiguration

| Parameter | Standard | Beschreibung |
|-----------|----------|--------------|
| `enabled` | true | Auto-Execute aktiviert |
| `min_ai_score` | 60 | Minimum AI Score |
| `min_confidence` | 0.6 | Minimum Parser Confidence |
| `max_daily_trades` | 10 | Maximale Trades pro Tag |
| `require_ai_approval` | true | AI muss genehmigen |

### Ablauf

1. Signal empfangen (Bot/Channel/Webhook)
2. Parser extrahiert Daten + Confidence
3. AI analysiert Signal (Score, Qualität)
4. Auto-Execute prüft:
   - Confidence >= 60%?
   - AI Score >= 60?
   - Daily Limit nicht erreicht?
   - Risk Manager OK?
5. Trade ausführen (Paper oder Binance)
6. Benachrichtigung senden

### API

```bash
# Status abrufen
GET /api/auto-execute/status

# Konfiguration ändern
PUT /api/auto-execute/config?enabled=true&min_ai_score=70
```

---

## 📚 API Dokumentation

### Basis-URL

```
Production: https://signal-trader-ai-4.preview.emergentagent.com/api
Local: http://localhost:8001/api
```

### Endpoints

#### Signals

| Method | Endpoint | Beschreibung |
|--------|----------|--------------|
| GET | `/signals` | Alle Signale |
| POST | `/signals` | Neues Signal erstellen |
| POST | `/signals/webhook` | Signal via Webhook |
| DELETE | `/signals/{id}` | Signal dismissieren |

#### Trades

| Method | Endpoint | Beschreibung |
|--------|----------|--------------|
| GET | `/trades` | Alle Trades |
| GET | `/trades/open` | Offene Trades |
| POST | `/trades/execute` | Trade ausführen |
| POST | `/trades/close` | Trade schließen |

#### Portfolio

| Method | Endpoint | Beschreibung |
|--------|----------|--------------|
| GET | `/portfolio` | Portfolio-Übersicht |
| GET | `/portfolio/stats` | Statistiken |

#### AI

| Method | Endpoint | Beschreibung |
|--------|----------|--------------|
| POST | `/ai/analyze-signal` | Signal analysieren |
| POST | `/ai/analyze-tweet` | Tweet analysieren |
| GET | `/ai/influential-accounts` | Überwachte Accounts |

#### Auto-Execute

| Method | Endpoint | Beschreibung |
|--------|----------|--------------|
| GET | `/auto-execute/status` | Status abrufen |
| PUT | `/auto-execute/config` | Konfiguration ändern |

#### Telegram

| Method | Endpoint | Beschreibung |
|--------|----------|--------------|
| GET | `/telegram/bot/status` | Bot-Status |
| GET | `/telegram/channels/status` | Channel-Monitor Status |
| GET | `/telegram/channels` | Bekannte Channels |

#### Binance

| Method | Endpoint | Beschreibung |
|--------|----------|--------------|
| GET | `/binance/config` | Konfiguration |
| GET | `/binance/balance` | Kontostand |
| GET | `/binance/positions` | Offene Positionen |
| GET | `/binance/price/{symbol}` | Aktueller Preis |

---

## 🖥 Dashboard

### Seiten

1. **Dashboard** (`/`) - Hauptübersicht
   - Portfolio-Metriken
   - Pending Signals
   - Open Positions
   - Performance Charts

2. **Signals** (`/signals`) - Signal-Verwaltung
   - Alle Signale (Pending/Executed/Dismissed)
   - Filter & Suche
   - Signal-Ausführung

3. **Trades** (`/trades`) - Trade-Verwaltung
   - Open/Closed Trades
   - P&L Tracking
   - Trade schließen

4. **Portfolio** (`/portfolio`) - Portfolio-Analyse
   - Equity Curve
   - Win Rate Chart
   - Statistiken

5. **AI Center** (`/ai`) - KI-Steuerung
   - Auto-Execute Kontrolle
   - Tweet-Analyse Tool
   - Überwachte Accounts

6. **Settings** (`/settings`) - Einstellungen
   - Trading Settings
   - Risk Management
   - Telegram Integration
   - Binance Integration

---

## 📊 Aktueller Status

**Stand: 11. Februar 2026**

### System-Komponenten

| Komponente | Status | Details |
|------------|--------|---------|
| Backend (FastAPI) | 🟢 Running | Port 8001 |
| Frontend (React) | 🟢 Running | Port 3000 |
| MongoDB | 🟢 Connected | |
| Telegram Bot | 🟢 Polling | @traiding_r2d2_bot |
| Channel Monitor | 🟢 Monitoring | 2 Channels |
| AI Analyzer | 🟢 Ready | GPT-4o |
| Auto-Execute | 🟢 Enabled | 0/10 Trades heute |
| Binance Testnet | 🟢 Connected | $5,000 USDT |

### Statistiken

- **Signale**: 12 total (3 pending, 9 executed)
- **Trades**: 1 total (1 open)
- **Win Rate**: 0% (noch keine geschlossenen Trades)
- **P&L**: $0 (Paper Trading)

---

## 🗺 Roadmap & TODOs

### ✅ Phase 1: MVP (Abgeschlossen)
- [x] Signal Parser (Multi-Format)
- [x] Risk Manager
- [x] Paper Trading Engine
- [x] Dashboard UI
- [x] Webhook API

### ✅ Phase 2: Telegram Integration (Abgeschlossen)
- [x] Telegram Bot (@traiding_r2d2_bot)
- [x] Channel Monitor (Evening Trader, Fat Pig)
- [x] Signal-Parsing für beide Formate

### ✅ Phase 3: KI & Automatisierung (Abgeschlossen)
- [x] AI Signal-Analyse (GPT-4o)
- [x] Auto-Execute Engine
- [x] Benachrichtigungs-System
- [x] X/Twitter Analyse

### ✅ Phase 4: Broker Integration (Abgeschlossen)
- [x] Binance Futures Testnet
- [x] Balance & Positions API
- [x] Order Execution (vorbereitet)

### 🔄 Phase 5: Optimierung (In Arbeit)
- [ ] Live Binance Trading aktivieren
- [ ] Trailing Stop Loss
- [ ] Partial Take Profits
- [ ] Performance Analytics Dashboard

### 📋 Phase 6: Erweiterungen (Geplant)
- [ ] MetaTrader 5 Integration
- [ ] Email Signal Parser (IMAP)
- [ ] Mehr Signal-Channels
- [ ] Mobile App (React Native)
- [ ] Backtesting Engine

### 🎯 Nächste TODOs

1. **Hochpriorität**
   - [ ] Test mit echtem Channel-Signal
   - [ ] Benachrichtigungen testen (Chat ID registrieren)
   - [ ] Ersten Auto-Execute Trade ausführen

2. **Mittelpriorität**
   - [ ] Binance Live Trading (Paper deaktivieren)
   - [ ] Mehr Signal-Channels hinzufügen
   - [ ] Performance-Berichte

3. **Niedrigpriorität**
   - [ ] Email Parser aktivieren
   - [ ] Mobile App
   - [ ] Backtesting

---

## 🔧 Entwicklung

### Projekt-Struktur

```
/app/
├── backend/
│   ├── models/
│   │   ├── signals.py       # Signal Datenmodelle
│   │   ├── trading.py       # Trade/Position Modelle
│   │   └── settings.py      # Einstellungen
│   ├── services/
│   │   ├── signal_parser.py         # Multi-Format Parser
│   │   ├── risk_manager.py          # Risk Management
│   │   ├── trading_engine.py        # Paper Trading
│   │   ├── telegram_bot.py          # Bot Handler
│   │   ├── telegram_channel_monitor.py  # Channel Listener
│   │   ├── telegram_listener.py     # Signal Parser
│   │   ├── ai_analyzer.py           # GPT Analyse
│   │   ├── auto_execute.py          # Auto-Execute Logic
│   │   ├── notification_service.py  # Benachrichtigungen
│   │   ├── binance_broker.py        # Binance API
│   │   └── x_twitter_monitor.py     # Social Media
│   ├── server.py            # FastAPI Server
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/      # UI Komponenten
│   │   ├── pages/           # Seiten
│   │   └── App.js           # Main App
│   └── package.json
└── README.md
```

### Befehle

```bash
# Backend starten
cd backend && python server.py

# Frontend starten
cd frontend && yarn start

# Tests ausführen
pytest tests/

# Logs anzeigen
tail -f /var/log/supervisor/backend.err.log
```

---

## 📞 Support

- **Telegram Bot**: @traiding_r2d2_bot
- **GitHub**: https://github.com/robinzi2001-cell/trading-ai
- **Dashboard**: https://signal-trader-ai-4.preview.emergentagent.com

---

## ⚠️ Disclaimer

**Dieses System ist für Bildungs- und Demonstrationszwecke.**

Trading mit Kryptowährungen birgt erhebliche Risiken. Vergangene Performance ist kein Indikator für zukünftige Ergebnisse. Nutze zunächst das Paper Trading und Testnet, bevor du echtes Kapital einsetzt.

---

<p align="center">
  Built with ❤️ by Trading AI Team<br>
  <small>Letzte Aktualisierung: 11. Februar 2026</small>
</p>
