# Trading AI - Product Requirements Document

## Original Problem Statement
Trading KI die Signale aus Top-Kreisen verwendet um wahrscheinliche Signale rauszufiltern für einen Trade und diesen darstellt. Über ein angeschlossenes Handelskonto einer beliebigen Broker etc kompatibel ist um automatische Trades einzugeben mit vernünftigem Money Risk/Lose etc. Das ganze soll als Container oder geschlossenes Plugin funktionieren.

## Architecture
- **Backend**: FastAPI + MongoDB (Paper Trading Engine)
- **Frontend**: React + Tailwind + Shadcn/UI
- **Services**: Signal Parser, Risk Manager, Trading Engine

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

## Implementation History

### 2026-02-10 - Initial MVP
- ✅ Signal Parser with multi-format support
- ✅ Risk Manager with position sizing
- ✅ Paper Trading Engine
- ✅ Dashboard with real-time updates
- ✅ Signals, Trades, Portfolio, Settings pages
- ✅ REST API with Webhook support

## Prioritized Backlog

### P0 (Critical)
- ✅ Signal Intake via Webhook
- ✅ Paper Trading Engine
- ✅ Risk Management

### P1 (High)
- [ ] Telegram Signal Listener
- [ ] Email Signal Parser
- [ ] Binance Testnet Integration

### P2 (Medium)
- [ ] Context Engine (News/Sentiment)
- [ ] Pattern Recognition
- [ ] ML Prediction Model

## Next Tasks
1. Implement Telegram listener for signal channels
2. Add email IMAP parsing
3. Connect to Binance Testnet for real execution
4. Add Context Engine for market sentiment
