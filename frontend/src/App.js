import React, { useState, useEffect, useCallback } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import axios from "axios";
import { Toaster, toast } from "sonner";

// Components
import Sidebar from "./components/Sidebar";
import Dashboard from "./pages/Dashboard";
import Signals from "./pages/Signals";
import Trades from "./pages/Trades";
import Portfolio from "./pages/Portfolio";
import Settings from "./pages/Settings";
import AICenter from "./pages/AICenter";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

// Create axios instance with base URL
export const api = axios.create({
  baseURL: API,
  headers: {
    'Content-Type': 'application/json'
  }
});

function App() {
  const [signals, setSignals] = useState([]);
  const [trades, setTrades] = useState([]);
  const [positions, setPositions] = useState([]);
  const [portfolio, setPortfolio] = useState(null);
  const [stats, setStats] = useState(null);
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const [signalsRes, tradesRes, positionsRes, portfolioRes, statsRes, settingsRes] = await Promise.all([
        api.get('/signals?limit=50'),
        api.get('/trades?limit=50'),
        api.get('/positions'),
        api.get('/portfolio'),
        api.get('/portfolio/stats'),
        api.get('/settings')
      ]);

      setSignals(signalsRes.data);
      setTrades(tradesRes.data);
      setPositions(positionsRes.data);
      setPortfolio(portfolioRes.data);
      setStats(statsRes.data);
      setSettings(settingsRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
      toast.error('Failed to fetch data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, [fetchData]);

  const executeSignal = async (signalId, quantity = null) => {
    try {
      const response = await api.post('/trades/execute', {
        signal_id: signalId,
        quantity: quantity
      });
      toast.success(`Trade executed: ${response.data.symbol}`);
      fetchData();
      return response.data;
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to execute trade');
      throw error;
    }
  };

  const closeTrade = async (tradeId, reason = 'manual') => {
    try {
      const response = await api.post('/trades/close', {
        trade_id: tradeId,
        exit_reason: reason
      });
      toast.success('Trade closed successfully');
      fetchData();
      return response.data;
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to close trade');
      throw error;
    }
  };

  const dismissSignal = async (signalId) => {
    try {
      await api.delete(`/signals/${signalId}`);
      toast.success('Signal dismissed');
      fetchData();
    } catch (error) {
      toast.error('Failed to dismiss signal');
    }
  };

  const createSampleSignals = async () => {
    try {
      await api.post('/demo/sample-signals');
      toast.success('Sample signals created');
      fetchData();
    } catch (error) {
      toast.error('Failed to create sample signals');
    }
  };

  const resetDemo = async () => {
    try {
      await api.post('/demo/reset');
      toast.success('Demo account reset');
      fetchData();
    } catch (error) {
      toast.error('Failed to reset demo');
    }
  };

  const updateSettings = async (newSettings) => {
    try {
      const response = await api.put('/settings', newSettings);
      setSettings(response.data);
      toast.success('Settings updated');
      return response.data;
    } catch (error) {
      toast.error('Failed to update settings');
      throw error;
    }
  };

  const pendingSignals = signals.filter(s => !s.executed && !s.dismissed);

  return (
    <div className="App dark">
      <BrowserRouter>
        <div className="flex min-h-screen bg-[#09090b]">
          <Sidebar 
            pendingSignalsCount={pendingSignals.length}
            openTradesCount={positions.length}
          />
          <main className="flex-1 md:pl-64 min-h-screen">
            <Routes>
              <Route 
                path="/" 
                element={
                  <Dashboard 
                    signals={pendingSignals}
                    trades={trades}
                    positions={positions}
                    portfolio={portfolio}
                    stats={stats}
                    loading={loading}
                    onExecuteSignal={executeSignal}
                    onDismissSignal={dismissSignal}
                    onCloseTrade={closeTrade}
                    onCreateSampleSignals={createSampleSignals}
                  />
                } 
              />
              <Route 
                path="/signals" 
                element={
                  <Signals 
                    signals={signals}
                    loading={loading}
                    onExecuteSignal={executeSignal}
                    onDismissSignal={dismissSignal}
                    onCreateSampleSignals={createSampleSignals}
                  />
                } 
              />
              <Route 
                path="/trades" 
                element={
                  <Trades 
                    trades={trades}
                    positions={positions}
                    loading={loading}
                    onCloseTrade={closeTrade}
                  />
                } 
              />
              <Route 
                path="/portfolio" 
                element={
                  <Portfolio 
                    portfolio={portfolio}
                    stats={stats}
                    trades={trades}
                    loading={loading}
                  />
                } 
              />
              <Route 
                path="/settings" 
                element={
                  <Settings 
                    settings={settings}
                    onUpdate={updateSettings}
                    onReset={resetDemo}
                    loading={loading}
                  />
                } 
              />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
      <Toaster 
        theme="dark" 
        position="bottom-right"
        toastOptions={{
          style: {
            background: '#18181b',
            border: '1px solid #27272a',
            color: '#fff'
          }
        }}
      />
    </div>
  );
}

export default App;
