# Trading AI - Product Requirements Document

## Original Problem Statement
Trading KI die Signale aus Top-Kreisen verwendet um wahrscheinliche Signale rauszufiltern für einen Trade und diesen darstellt. Über ein angeschlossenes Handelskonto einer beliebigen Broker etc kompatibel ist um automatische Trades einzugeben mit vernünftigem Money Risk/Lose etc. Das ganze soll als Container oder geschlossenes Plugin funktionieren.

## User Personas
1. **Active Trader** - Filtert Signale aus mehreren Quellen
2. **Copy Trader** - Folgt Signalen von Top-Trading-Gruppen
3. **Risk-conscious Investor** - Benötigt professionelles Money Management

## Core Requirements
- Multi-Source Signal Intake (Webhook, Telegram Bot, Telegram Channels)
- AI-gestützte Signalanalyse mit GPT-4o
- Risk-basierte Position Sizing
- Paper Trading Simulation
- Real-time Dashboard mit P&L Tracking
- Broker Integration (Binance Futures Testnet)
- Auto-Execute mit AI Approval
- X/Twitter Sentiment Analyse

---

## Architecture

### Backend
- **Framework**: FastAPI (Python)
- **Database**: MongoDB
- **Services**:
  - Signal Parser (Multi-Format: Evening Trader, Fat Pig Signals)
  - Risk Manager (Position Sizing, R:R Validation)
  - Trading Engine (Paper Trading)
  - Telegram Bot Service (@traiding_r2d2_bot)
  - Telegram Channel Monitor (Telethon)
  - AI Analyzer (GPT-4o via Emergent LLM)
  - Auto-Execute Engine
  - Notification Service
  - Binance Broker (Testnet)

### Frontend
- **Framework**: React 19
- **UI**: Tailwind CSS + Shadcn/UI
- **State**: Local React State
- **Pages**: Dashboard, Signals, Trades, Portfolio, Settings, AI Center

### Key Files
```
/app/backend/
├── server.py                          # FastAPI Server + Routes
├── models/
│   ├── signals.py                     # Signal Datenmodelle
│   ├── trading.py                     # Trade/Position Modelle
│   └── settings.py                    # Einstellungen
├── services/
│   ├── signal_parser.py               # Multi-Format Parser
│   ├── risk_manager.py                # Risk Management
│   ├── trading_engine.py              # Paper Trading
│   ├── telegram_bot.py                # Bot Handler
│   ├── telegram_channel_monitor.py    # Channel Listener
│   ├── ai_analyzer.py                 # GPT Analyse
│   ├── auto_execute.py                # Auto-Execute Logic
│   ├── notification_service.py        # Telegram Alerts
│   └── binance_broker.py              # Binance API

/app/frontend/src/
├── App.js                             # Main App + Router
├── pages/
│   ├── Dashboard.jsx
│   ├── Signals.jsx
│   ├── Trades.jsx
│   ├── Portfolio.jsx
│   ├── Settings.jsx
│   └── AICenter.jsx
└── components/
    └── ui/                            # Shadcn Components
```

---

## Implementation History

### 2026-02-10 - Phase 1: MVP
- Signal Parser mit Multi-Format Support
- Risk Manager mit Position Sizing
- Paper Trading Engine
- Dashboard mit Real-time Updates
- REST API mit Webhook Support

### 2026-02-10 - Phase 2: Telegram Integration
- Telegram Bot (@traiding_r2d2_bot)
- Channel Monitor (Evening Trader, Fat Pig Signals)
- Signal-Parsing für beide Formate
- Bot Commands (/start, /help, /status, /signal)

### 2026-02-11 - Phase 3: AI & Automatisierung
- AI Signal-Analyse (GPT-4o via Emergent LLM)
- Auto-Execute Engine mit konfigurierbaren Schwellwerten
- X/Twitter Sentiment Analyse
- AI Center UI Seite
- Notification Service für Telegram Alerts

### 2026-02-12 - Phase 4: Alpaca Broker Integration
- Binance entfernt (regionale Beschränkungen)
- Alpaca Paper Trading integriert ($100,000 Testguthaben)
- Unterstützt: Aktien (US Markets), Crypto 24/7
- Features: Fractional Shares, Bracket Orders, Extended Hours
- API Endpoints für Orders, Positions, Balance

### 2026-02-13 - Phase 5: End-to-End Auto-Execute
- Neuer Auto-Execute Service mit Alpaca-Integration
- Professionelles Money Management:
  - Risk-basierte Position Sizing (2% pro Trade)
  - AI Score Scaling (höherer Score = größere Position)
  - Max. Positionen Limit (5)
  - Cooldown zwischen Trades
  - Circuit Breaker bei Fehlern
- Signal Flow: Telegram/RSS → AI Analyse → Alpaca Order → Notification
- Dashboard zeigt Alpaca-Positionen mit Live P&L
- Health Monitoring und Reliability Features

---

## Feature Status

### Implementiert
| Feature | Status | Beschreibung |
|---------|--------|--------------|
| Telegram Bot | AKTIV | @traiding_r2d2_bot |
| Channel Monitor | AKTIV | Evening Trader + Fat Pig Signals |
| KI Signal-Analyse | AKTIV | GPT-4o Score 0-100 |
| Auto-Execute | AKTIV | Min. Score: 60 |
| Binance Testnet | VERBUNDEN | $5,000 USDT |
| X/Twitter Analyse | AKTIV | Trump, Elon Musk, etc. |
| Benachrichtigungen | AKTIV | Telegram Alerts |
| Paper Trading | AKTIV | Risikofrei testen |
| Risk Management | AKTIV | Position Sizing, R:R |
| Dashboard | AKTIV | Real-time UI |

### Geplant (P1)
- [ ] Live Binance Trading (Paper -> Live Switch)
- [ ] Trailing Stop Loss
- [ ] Partial Take Profits
- [ ] Performance Analytics

### Backlog (P2)
- [ ] MetaTrader 5 Integration
- [ ] Interactive Brokers Integration
- [ ] Email Signal Parser (IMAP)
- [ ] Mehr Signal-Channels
- [ ] Mobile App (React Native)
- [ ] Backtesting Engine

---

## API Endpoints

### Signals
- `GET /api/signals` - Alle Signale
- `POST /api/signals` - Neues Signal erstellen
- `POST /api/signals/webhook` - Signal via Webhook
- `DELETE /api/signals/{id}` - Signal dismissieren

### Trades
- `GET /api/trades` - Alle Trades
- `GET /api/trades/open` - Offene Trades
- `POST /api/trades/execute` - Trade ausführen
- `POST /api/trades/close` - Trade schließen

### Portfolio
- `GET /api/portfolio` - Portfolio-Übersicht
- `GET /api/portfolio/stats` - Statistiken

### AI
- `POST /api/ai/analyze-signal` - Signal analysieren
- `POST /api/ai/analyze-tweet` - Tweet analysieren
- `GET /api/ai/influential-accounts` - Überwachte Accounts

### Auto-Execute
- `GET /api/auto-execute/status` - Status abrufen
- `PUT /api/auto-execute/config` - Konfiguration ändern

### Telegram
- `GET /api/telegram/bot/status` - Bot-Status
- `GET /api/telegram/channels/status` - Channel-Monitor Status

### Binance
- `GET /api/binance/balance` - Kontostand
- `GET /api/binance/positions` - Offene Positionen

---

## Database Schema (MongoDB)

### signals
```json
{
  "id": "uuid",
  "source": "telegram|webhook|manual",
  "asset": "BTC/USDT",
  "action": "long|short",
  "entry": 96500.0,
  "stop_loss": 94000.0,
  "take_profits": [99000, 102000],
  "leverage": 3,
  "confidence": 0.85,
  "executed": false,
  "dismissed": false,
  "ai_analysis": {...}
}
```

### trades
```json
{
  "id": "uuid",
  "signal_id": "uuid",
  "symbol": "BTCUSDT",
  "side": "long|short",
  "entry_price": 96500.0,
  "quantity": 0.01,
  "stop_loss": 94000.0,
  "take_profits": [99000, 102000],
  "status": "open|closed",
  "pnl": 0.0
}
```

---

## Environment Variables

### Backend (.env)
```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=trading_ai
TELEGRAM_BOT_TOKEN=xxx
TELEGRAM_API_ID=xxx
TELEGRAM_API_HASH=xxx
BINANCE_API_KEY=xxx
BINANCE_SECRET=xxx
BINANCE_TESTNET=true
EMERGENT_LLM_KEY=xxx
```

### Frontend (.env)
```env
REACT_APP_BACKEND_URL=https://...
```

---

## Known Issues
Keine bekannten Probleme zum aktuellen Zeitpunkt.

---

## Completed Tests (2026-02-11)

### End-to-End Workflow Test ✅
1. Signal erstellt (BTC/USDT LONG via Webhook)
2. AI Analyse durchgeführt (Score: 75/100, Quality: good)
3. Trade ausgeführt (Paper Trading: 0.075 BTC @ $96,986)
4. Position im Dashboard sichtbar

### Komponenten-Tests ✅
- Telegram Bot: AKTIV (@traiding_r2d2_bot)
- Channel Monitor: AKTIV (Evening Trader + Fat Pig Signals)
- AI Analyzer: VERFÜGBAR (GPT-4o via Emergent LLM)
- Auto-Execute: AKTIVIERT (Paper Trading Mode)
- Binance Testnet: Keys ungültig - Paper Trading wird verwendet
- X/Twitter Analyse: FUNKTIONIERT

### Testing Agent Results (iteration_3.json)
- Backend Tests: 100% (16/16 bestanden)
- Frontend Tests: 100%
- Bug behoben: rssRes capture in AICenter.jsx

### Verifizierte Features ✅
- Execute Order: Paper Trading funktioniert (Trade erstellen, Position öffnen)
- Trade Close: P&L Berechnung funktioniert
- Auto-Execute: Aktiviert mit Binance Testnet Modus
- Twitter RSS: Konfiguriert (5 Accounts), aber Nitter-Instanzen down → Manueller Modus
- AI Analyse: Signal-Scoring und Tweet-Impact-Analyse funktionieren
- Telegram Bot: Läuft (@traiding_r2d2_bot)

---

## Next Steps

### Empfohlen (P1)
1. **Neue Binance Testnet Keys** - Erstelle neue API Keys auf https://testnet.binancefuture.com
2. Aktiviere dann Binance Testnet Modus im AI Center

### Bald (P1)
3. Live Binance Trading aktivieren
4. Mehr Signal-Channels hinzufügen
5. Performance-Berichte

### Später (P2)
6. Mobile App
7. Backtesting Engine
8. Multi-Broker Support

---

*Letzte Aktualisierung: 11. Februar 2026*
