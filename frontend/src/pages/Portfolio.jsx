import React from 'react';
import { Wallet, TrendingUp, TrendingDown, Target, Shield, BarChart3 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import MetricCard, { StatRow } from '../components/MetricCard';
import { EquityCurveChart, WinRateChart, PnLChart } from '../components/Charts';
import { cn } from '../lib/utils';

export default function Portfolio({ portfolio, stats, trades, loading }) {
  // Generate equity curve data
  const closedTrades = trades?.filter(t => t.status === 'closed') || [];
  const initialBalance = portfolio?.initial_balance || 10000;
  
  const equityData = closedTrades.reduce((acc, trade, index) => {
    const prevBalance = index === 0 ? initialBalance : acc[index - 1].value;
    const newBalance = prevBalance + (trade.realized_pnl || 0);
    acc.push({
      time: new Date(trade.exit_time).toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit' }),
      value: newBalance
    });
    return acc;
  }, []);

  // Add starting point
  if (equityData.length > 0) {
    equityData.unshift({ time: 'Start', value: initialBalance });
  }

  // P&L data for mini chart
  const pnlData = closedTrades.slice(-20).map((t, i) => ({
    trade: i + 1,
    pnl: closedTrades.slice(0, i + 1).reduce((sum, trade) => sum + (trade.realized_pnl || 0), 0)
  }));

  return (
    <div className="p-4 md:p-6 lg:p-8 pb-20 md:pb-8" data-testid="portfolio-page">
      {/* Header */}
      <div className="glass-header -mx-4 md:-mx-6 lg:-mx-8 -mt-4 md:-mt-6 lg:-mt-8 px-4 md:px-6 lg:px-8 py-4 mb-6 sticky top-0 z-40">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Wallet className="w-5 h-5 text-blue-500" />
            <h1 className="font-heading text-xl font-bold tracking-tight uppercase text-white">
              Portfolio
            </h1>
          </div>
        </div>
      </div>

      {/* Main Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <MetricCard
          label="Total Balance"
          value={portfolio?.current_balance || 10000}
          prefix="$"
          loading={loading}
        />
        <MetricCard
          label="Total P&L"
          value={portfolio?.total_pnl || 0}
          prefix="$"
          change={portfolio?.total_pnl_percent}
          variant="highlight"
          loading={loading}
        />
        <MetricCard
          label="Available"
          value={portfolio?.available_balance || 10000}
          prefix="$"
          loading={loading}
        />
        <MetricCard
          label="Margin Used"
          value={portfolio?.margin_used || 0}
          prefix="$"
          loading={loading}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Equity Curve */}
        <div className="lg:col-span-2">
          <Card className="bg-zinc-900/50 border-white/5 h-full">
            <CardHeader>
              <CardTitle className="font-heading text-lg font-semibold tracking-tight uppercase text-white flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-blue-500" />
                Equity Curve
              </CardTitle>
            </CardHeader>
            <CardContent>
              <EquityCurveChart data={equityData} />
            </CardContent>
          </Card>
        </div>

        {/* Performance Stats */}
        <div className="space-y-4">
          {/* Win Rate Card */}
          <Card className="bg-zinc-900/50 border-white/5">
            <CardHeader className="pb-2">
              <CardTitle className="text-xs text-zinc-500 uppercase tracking-wide">
                Win/Loss Ratio
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

          {/* Quick Stats */}
          <Card className="bg-zinc-900/50 border-white/5">
            <CardHeader className="pb-2">
              <CardTitle className="text-xs text-zinc-500 uppercase tracking-wide">
                Statistics
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-0">
              <StatRow 
                label="Total Trades" 
                value={stats?.total_trades || 0} 
              />
              <StatRow 
                label="Open Trades" 
                value={stats?.open_trades || 0}
                variant={stats?.open_trades > 0 ? 'warning' : 'default'}
              />
              <StatRow 
                label="Profit Factor" 
                value={stats?.profit_factor?.toFixed(2) || '0.00'}
                variant={stats?.profit_factor >= 1.5 ? 'success' : stats?.profit_factor >= 1 ? 'warning' : 'danger'}
              />
              <StatRow 
                label="Avg Win" 
                value={`$${stats?.avg_win?.toFixed(2) || '0.00'}`}
                variant="success"
              />
              <StatRow 
                label="Avg Loss" 
                value={`$${stats?.avg_loss?.toFixed(2) || '0.00'}`}
                variant="danger"
              />
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Recent P&L Chart */}
      <Card className="bg-zinc-900/50 border-white/5 mt-6">
        <CardHeader>
          <CardTitle className="font-heading text-lg font-semibold tracking-tight uppercase text-white flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-emerald-500" />
            Cumulative P&L (Last 20 Trades)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-48">
            <PnLChart data={pnlData} />
          </div>
        </CardContent>
      </Card>

      {/* Risk Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
        <Card className="bg-zinc-900/50 border-white/5">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <Shield className="w-4 h-4 text-blue-500" />
              <span className="text-xs text-zinc-500 uppercase">Max Drawdown</span>
            </div>
            <div className="font-mono text-xl text-white">
              {portfolio?.max_drawdown?.toFixed(2) || '0.00'}%
            </div>
          </CardContent>
        </Card>
        <Card className="bg-zinc-900/50 border-white/5">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <Target className="w-4 h-4 text-emerald-500" />
              <span className="text-xs text-zinc-500 uppercase">Best Trade</span>
            </div>
            <div className="font-mono text-xl text-emerald-500">
              +${closedTrades.reduce((max, t) => Math.max(max, t.realized_pnl || 0), 0).toFixed(2)}
            </div>
          </CardContent>
        </Card>
        <Card className="bg-zinc-900/50 border-white/5">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <TrendingDown className="w-4 h-4 text-red-500" />
              <span className="text-xs text-zinc-500 uppercase">Worst Trade</span>
            </div>
            <div className="font-mono text-xl text-red-500">
              ${closedTrades.reduce((min, t) => Math.min(min, t.realized_pnl || 0), 0).toFixed(2)}
            </div>
          </CardContent>
        </Card>
        <Card className="bg-zinc-900/50 border-white/5">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <Wallet className="w-4 h-4 text-yellow-500" />
              <span className="text-xs text-zinc-500 uppercase">Unrealized</span>
            </div>
            <div className={cn(
              "font-mono text-xl",
              (stats?.unrealized_pnl || 0) >= 0 ? "text-emerald-500" : "text-red-500"
            )}>
              {(stats?.unrealized_pnl || 0) >= 0 ? '+' : ''}${stats?.unrealized_pnl?.toFixed(2) || '0.00'}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
