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
- **Alpaca Broker Integration (Paper + Live)**
- Auto-Execute mit AI Approval
- **Dynamische Telegram-Kanal-Verwaltung**

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
  - Auto-Execute Engine (Alpaca)
  - Notification Service
  - **Alpaca Broker (Paper + Live Trading)**

### Frontend
- **Framework**: React 19
- **UI**: Tailwind CSS + Shadcn/UI
- **State**: Local React State
- **Pages**: Dashboard, Signals, Trades, Portfolio, Settings, AI Center
- **Components**: TelegramChannelManager (Kanal-Verwaltung)

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
│   ├── trading_engine.py              # Paper Trading Engine
│   ├── telegram_bot.py                # Bot Handler
│   ├── telegram_channel_monitor.py    # Channel Listener
│   ├── telegram_listener.py           # Signal Parser
│   ├── ai_analyzer.py                 # GPT Analyse
│   ├── auto_execute_alpaca.py         # Auto-Execute Logic
│   ├── notification_service.py        # Telegram Alerts
│   ├── alpaca_broker.py               # Alpaca API Integration
│   ├── x_twitter_monitor.py           # X/Twitter Analysis
│   └── twitter_rss_monitor.py         # RSS Monitoring

/app/frontend/src/
├── App.js                             # Main App + Router
├── pages/
│   ├── Dashboard.jsx
│   ├── Signals.jsx
│   ├── Trades.jsx
│   ├── Portfolio.jsx
│   ├── Settings.jsx                   # Mit Telegram Tab
│   └── AICenter.jsx
└── components/
    ├── ui/                            # Shadcn Components
    └── TelegramChannelManager.jsx     # NEU: Kanal-Verwaltung
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
- Professionelles Money Management
- Signal Flow: Telegram/RSS → AI Analyse → Alpaca Order → Notification
- Dashboard zeigt Alpaca-Positionen mit Live P&L

### 2026-02-14 - Phase 6: Telegram-Kanal-Verwaltung & Stabilisierung
- **Backend repariert** (fehlende Module erstellt):
  - trading_engine.py - Paper Trading Engine
  - telegram_listener.py - Signal Parser
  - x_twitter_monitor.py - Twitter Analysis
  - twitter_rss_monitor.py - RSS Monitoring
- **Alpaca Live API Keys konfiguriert**
- **Dynamische Telegram-Kanal-Verwaltung**:
  - POST /api/telegram/channels/add - Kanal hinzufügen
  - DELETE /api/telegram/channels/{username} - Kanal entfernen
  - PUT /api/telegram/channels/{username}/toggle - Aktivieren/Deaktivieren
  - GET /api/telegram/channels/list - Alle Kanäle abrufen
- **TelegramChannelManager Komponente** im Frontend
- **Tests**: 100% Erfolgsrate (Backend + Frontend)

---

## Feature Status

### Implementiert ✅
| Feature | Status | Beschreibung |
|---------|--------|--------------|
| Telegram Bot | AKTIV | @traiding_r2d2_bot |
| Channel Monitor | AKTIV | Evening Trader + Fat Pig Signals |
| **Telegram Kanal-Verwaltung** | AKTIV | Dynamisch Kanäle hinzufügen |
| KI Signal-Analyse | AKTIV | GPT-4o Score 0-100 |
| Auto-Execute | AKTIV | Min. Score: 60 |
| **Alpaca Paper Trading** | VERBUNDEN | ~$100,000 Balance |
| **Alpaca Live Keys** | KONFIGURIERT | Bereit für Live Trading |
| X/Twitter Analyse | AKTIV | Elon Musk, etc. |
| Benachrichtigungen | AKTIV | Telegram Alerts |
| Paper Trading | AKTIV | Risikofrei testen |
| Risk Management | AKTIV | Position Sizing, R:R |
| Dashboard | AKTIV | Real-time UI |

### Geplant (P1)
- [ ] **Paper/Live Toggle Button** im UI für Alpaca
- [ ] Trailing Stop Loss
- [ ] Partial Take Profits
- [ ] Performance Analytics

### Backlog (P2)
- [ ] MetaTrader 5 Integration
- [ ] Interactive Brokers Integration
- [ ] Email Signal Parser (IMAP)
- [ ] Mehr Signal-Channels (via Manager hinzufügbar)
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
- **`GET /api/telegram/channels/list` - Alle Kanäle abrufen**
- **`POST /api/telegram/channels/add` - Kanal hinzufügen**
- **`DELETE /api/telegram/channels/{username}` - Kanal entfernen**
- **`PUT /api/telegram/channels/{username}/toggle` - Aktivieren/Deaktivieren**

### Alpaca Broker
- `GET /api/broker/config` - Broker-Konfiguration
- `GET /api/broker/balance` - Kontostand
- `GET /api/broker/positions` - Offene Positionen
- `GET /api/broker/orders` - Orders abrufen
- `POST /api/broker/order` - Order platzieren

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

### telegram_channels (NEU)
```json
{
  "username": "testsignals",
  "name": "@testsignals",
  "enabled": true,
  "added_at": "2026-02-14T01:41:03.550922+00:00",
  "signals_received": 0
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
ALPACA_API_KEY=xxx (Paper)
ALPACA_SECRET_KEY=xxx (Paper)
ALPACA_LIVE_API_KEY=xxx (Live)
ALPACA_LIVE_SECRET_KEY=xxx (Live)
EMERGENT_LLM_KEY=xxx
```

### Frontend (.env)
```env
REACT_APP_BACKEND_URL=https://...
```

---

## Test Results (2026-02-14)

### Iteration 4 - 100% Success Rate ✅
**Backend Tests**: 13/13 passed
- Health Check ✅
- Telegram Channel CRUD (add, list, delete, toggle) ✅
- Alpaca Broker (config, balance, positions) ✅
- Error handling (404, 400) ✅

**Frontend Tests**: 100%
- Settings Page Navigation ✅
- TelegramChannelManager Component ✅
- Channel Add/Toggle/Delete UI ✅

---

## Next Steps

### Priorität 1 (P1)
1. **Paper/Live Toggle** - UI Button für Alpaca Modus-Wechsel
2. Signal-Erkennung verbessern für verschiedene Formate

### Priorität 2 (P2)
3. Performance Reports / Analytics
4. Trailing Stop Loss implementieren

### Backlog (P3)
5. Mobile App
6. Backtesting Engine
7. Mehr Broker-Integrationen

---

*Letzte Aktualisierung: 14. Februar 2026*
