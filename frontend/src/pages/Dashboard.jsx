import React from 'react';
import { Activity, TrendingUp, Radio, Wallet, Plus, RefreshCw } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import MetricCard from '../components/MetricCard';
import SignalCard from '../components/SignalCard';
import PositionRow from '../components/PositionRow';
import { WinRateChart, PnLChart } from '../components/Charts';

export default function Dashboard({ 
  signals, 
  trades, 
  positions, 
  portfolio, 
  stats,
  loading,
  onExecuteSignal,
  onDismissSignal,
  onCloseTrade,
  onCreateSampleSignals
}) {
  // Get recent closed trades for P&L chart
  const closedTrades = trades?.filter(t => t.status === 'closed') || [];
  const pnlData = closedTrades.slice(0, 20).reverse().map((t, i) => ({
    trade: i + 1,
    pnl: closedTrades.slice(0, i + 1).reduce((sum, trade) => sum + (trade.realized_pnl || 0), 0)
  }));

  // High priority signal (highest confidence)
  const sortedSignals = [...(signals || [])].sort((a, b) => b.confidence - a.confidence);
  const highPrioritySignal = sortedSignals[0];
  const otherSignals = sortedSignals.slice(1, 4);

  const handleClosePosition = async (position) => {
    // Find the trade for this position
    const trade = trades?.find(t => t.symbol === position.symbol && t.status === 'open');
    if (trade) {
      await onCloseTrade(trade.id);
    }
  };

  return (
    <div className="p-4 md:p-6 lg:p-8 pb-20 md:pb-8" data-testid="dashboard">
      {/* Header */}
      <div className="glass-header -mx-4 md:-mx-6 lg:-mx-8 -mt-4 md:-mt-6 lg:-mt-8 px-4 md:px-6 lg:px-8 py-4 mb-6 sticky top-0 z-40">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Activity className="w-5 h-5 text-blue-500" />
            <h1 className="font-heading text-xl font-bold tracking-tight uppercase text-white">
              Dashboard
            </h1>
            <span className="w-2 h-2 rounded-full bg-emerald-500 live-indicator" />
          </div>
          <div className="flex items-center gap-2">
            {signals?.length === 0 && (
              <Button
                variant="outline"
                size="sm"
                onClick={onCreateSampleSignals}
                className="text-xs"
                data-testid="create-sample-signals-btn"
              >
                <Plus className="w-3 h-3 mr-1" />
                Sample Signals
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Portfolio Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <MetricCard
          label="Balance"
          value={portfolio?.current_balance || 10000}
          prefix="$"
          change={portfolio?.total_pnl_percent}
          variant="highlight"
          loading={loading}
        />
        <MetricCard
          label="Total P&L"
          value={stats?.combined_pnl || 0}
          prefix="$"
          trend={stats?.combined_pnl > 0 ? 'up' : stats?.combined_pnl < 0 ? 'down' : undefined}
          variant="highlight"
          loading={loading}
        />
        <MetricCard
          label="Open Positions"
          value={positions?.length || 0}
          loading={loading}
        />
        <MetricCard
          label="Win Rate"
          value={stats?.win_rate?.toFixed(1) || 0}
          suffix="%"
          loading={loading}
        />
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column - Signals */}
        <div className="lg:col-span-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-heading text-lg font-semibold tracking-tight uppercase text-white flex items-center gap-2">
              <Radio className="w-4 h-4 text-blue-500" />
              Pending Signals
            </h2>
            <span className="text-xs font-mono text-zinc-500">
              {signals?.length || 0} signals
            </span>
          </div>

          {signals?.length === 0 ? (
            <Card className="bg-zinc-900/50 border-white/5">
              <CardContent className="py-12 text-center">
                <Radio className="w-12 h-12 text-zinc-600 mx-auto mb-4" />
                <p className="text-zinc-500 mb-4">No pending signals</p>
                <Button
                  variant="outline"
                  onClick={onCreateSampleSignals}
                  data-testid="create-signals-empty-btn"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Create Sample Signals
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {highPrioritySignal && (
                <SignalCard
                  signal={highPrioritySignal}
                  onExecute={onExecuteSignal}
                  onDismiss={onDismissSignal}
                  isHighPriority={true}
                />
              )}
              {otherSignals.map(signal => (
                <SignalCard
                  key={signal.id}
                  signal={signal}
                  onExecute={onExecuteSignal}
                  onDismiss={onDismissSignal}
                  compact={true}
                />
              ))}
              {signals.length > 4 && (
                <p className="text-xs text-zinc-500 text-center">
                  +{signals.length - 4} more signals
                </p>
              )}
            </div>
          )}
        </div>

        {/* Right Column - Positions & Stats */}
        <div className="lg:col-span-7 space-y-6">
          {/* Open Positions */}
          <Card className="bg-zinc-900/50 border-white/5">
            <CardHeader className="pb-3">
              <CardTitle className="font-heading text-lg font-semibold tracking-tight uppercase text-white flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-emerald-500" />
                Open Positions
              </CardTitle>
            </CardHeader>
            <CardContent>
              {positions?.length === 0 ? (
                <div className="py-8 text-center text-zinc-500 text-sm">
                  No open positions
                </div>
              ) : (
                <div className="space-y-2">
                  {positions?.map(position => (
                    <PositionRow
                      key={position.id}
                      position={position}
                      onClose={handleClosePosition}
                    />
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Win Rate */}
            <Card className="bg-zinc-900/50 border-white/5">
              <CardHeader className="pb-2">
                <CardTitle className="text-xs text-zinc-500 uppercase tracking-wide">
                  Performance
                </CardTitle>
              </CardHeader>
              <CardContent>
                <WinRateChart
                  winRate={stats?.win_rate || 0}
                  wins={stats?.winning_trades || 0}
                  losses={stats?.losing_trades || 0}
                />
              </CardContent>
            </Card>

            {/* P&L Chart */}
            <Card className="bg-zinc-900/50 border-white/5">
              <CardHeader className="pb-2">
                <CardTitle className="text-xs text-zinc-500 uppercase tracking-wide">
                  Cumulative P&L
                </CardTitle>
              </CardHeader>
              <CardContent>
                <PnLChart data={pnlData} />
              </CardContent>
            </Card>
          </div>

          {/* Quick Stats */}
          <div className="grid grid-cols-3 gap-3">
            <div className="p-3 rounded-lg bg-zinc-900/50 border border-white/5">
              <div className="text-[10px] text-zinc-500 uppercase tracking-wide mb-1">Total Trades</div>
              <div className="font-mono text-xl text-white">{stats?.total_trades || 0}</div>
            </div>
            <div className="p-3 rounded-lg bg-zinc-900/50 border border-white/5">
              <div className="text-[10px] text-zinc-500 uppercase tracking-wide mb-1">Profit Factor</div>
              <div className="font-mono text-xl text-white">{stats?.profit_factor?.toFixed(2) || '0.00'}</div>
            </div>
            <div className="p-3 rounded-lg bg-zinc-900/50 border border-white/5">
              <div className="text-[10px] text-zinc-500 uppercase tracking-wide mb-1">Avg Win</div>
              <div className="font-mono text-xl text-emerald-500">${stats?.avg_win?.toFixed(0) || 0}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
