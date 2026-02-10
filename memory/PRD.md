# Trading AI - Product Requirements Document

## Original Problem Statement
Trading KI die Signale aus Top-Kreisen verwendet um wahrscheinliche Signale rauszufiltern für einen Trade und diesen darstellt. Über ein angeschlossenes Handelskonto einer beliebigen Broker etc kompatibel ist um automatische Trades einzugeben mit vernünftigem Money Risk/Lose etc. Das ganze soll als Container oder geschlossenes Plugin funktionieren.

## Architecture
- **Backend**: FastAPI + MongoDB (Paper Trading Engine + Integrations)
- **Frontend**: React + Tailwind + Shadcn/UI
- **Services**: 
  - Signal Parser (Multi-Format)
  - Risk Manager
  - Trading Engine
  - Telegram Listener (Evening Trader, Fat Pig Signals)
  - Email Parser
  - Binance Broker

## User Personas
1. **Active Trader** - Wants to filter signals from multiple sources
2. **Copy Trader** - Follows signals from top trading groups
3. **Risk-conscious Investor** - Needs proper money management

## Core Requirements (Static)
- Multi-source signal intake (Webhook, Telegram, Email)
- Signal parsing with confidence scoring
- Risk-based position sizing
- Paper trading simulation
- Real-time dashboard with P&L tracking
- Broker integration (Binance Futures)

## Implementation History

### 2026-02-10 - Initial MVP
- ✅ Signal Parser with multi-format support
- ✅ Risk Manager with position sizing
- ✅ Paper Trading Engine
- ✅ Dashboard with real-time updates
- ✅ Signals, Trades, Portfolio, Settings pages
- ✅ REST API with Webhook support

### 2026-02-10 - Phase 2: Integrations
- ✅ Telegram Listener Service (Telethon)
- ✅ Evening Trader + Fat Pig Signals Parser
- ✅ Email Parser Service (IMAP)
- ✅ Binance Futures Integration
- ✅ Settings UI with Tabs (Trading, Telegram, Binance, Quellen)
- ✅ Setup-Anleitungen im UI

## Prioritized Backlog

### P0 (Critical) - DONE
- ✅ Signal Intake via Webhook
- ✅ Paper Trading Engine
- ✅ Risk Management

### P1 (High) - IN PROGRESS
- ✅ Telegram Signal Listener (Code ready)
- ✅ Email Signal Parser (Code ready)
- ✅ Binance Testnet Integration (Code ready)
- ⏳ Telegram API Credentials Setup (User action required)
- ⏳ Binance API Credentials Setup (User action required)

### P2 (Medium)
- [ ] Context Engine (News/Sentiment)
- [ ] Pattern Recognition
- [ ] ML Prediction Model
- [ ] MetaTrader 5 Integration
- [ ] Interactive Brokers Integration

## Next Tasks
1. **User Action**: Telegram API Credentials von my.telegram.org holen
2. **User Action**: Binance Testnet Account erstellen
3. Telegram Listener aktivieren und Channels verbinden
4. Binance Paper Trading aktivieren
5. Auto-Execute Feature testen
