import React, { useState } from 'react';
import { TrendingUp, TrendingDown, X, Clock, DollarSign, Percent } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { cn } from '../lib/utils';

export default function Trades({ trades, positions, loading, onCloseTrade }) {
  const [tab, setTab] = useState('open'); // open, closed

  const openTrades = trades?.filter(t => t.status === 'open') || [];
  const closedTrades = trades?.filter(t => t.status === 'closed') || [];
  const displayTrades = tab === 'open' ? openTrades : closedTrades;

  const formatPrice = (price) => {
    if (!price) return '-';
    if (price >= 1000) return price.toLocaleString('en-US', { maximumFractionDigits: 2 });
    if (price >= 1) return price.toFixed(2);
    return price.toFixed(6);
  };

  const formatTime = (timestamp) => {
    if (!timestamp) return '-';
    return new Date(timestamp).toLocaleString('de-DE', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="p-4 md:p-6 lg:p-8 pb-20 md:pb-8" data-testid="trades-page">
      {/* Header */}
      <div className="glass-header -mx-4 md:-mx-6 lg:-mx-8 -mt-4 md:-mt-6 lg:-mt-8 px-4 md:px-6 lg:px-8 py-4 mb-6 sticky top-0 z-40">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <TrendingUp className="w-5 h-5 text-emerald-500" />
            <h1 className="font-heading text-xl font-bold tracking-tight uppercase text-white">
              Trades
            </h1>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        <Button
          variant={tab === 'open' ? 'default' : 'ghost'}
          size="sm"
          onClick={() => setTab('open')}
          className={tab === 'open' ? 'bg-white/10' : 'text-zinc-400'}
          data-testid="tab-open"
        >
          Open Trades
          <span className="ml-1.5 text-xs font-mono opacity-60">
            {openTrades.length}
          </span>
        </Button>
        <Button
          variant={tab === 'closed' ? 'default' : 'ghost'}
          size="sm"
          onClick={() => setTab('closed')}
          className={tab === 'closed' ? 'bg-white/10' : 'text-zinc-400'}
          data-testid="tab-closed"
        >
          Closed Trades
          <span className="ml-1.5 text-xs font-mono opacity-60">
            {closedTrades.length}
          </span>
        </Button>
      </div>

      {/* Trades List */}
      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map(i => (
            <Card key={i} className="bg-zinc-900/50 border-white/5 animate-pulse">
              <CardContent className="p-4 h-24" />
            </Card>
          ))}
        </div>
      ) : displayTrades.length === 0 ? (
        <Card className="bg-zinc-900/50 border-white/5">
          <CardContent className="py-16 text-center">
            <TrendingUp className="w-16 h-16 text-zinc-700 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-white mb-2">
              {tab === 'open' ? 'No open trades' : 'No closed trades'}
            </h3>
            <p className="text-zinc-500 text-sm">
              {tab === 'open' 
                ? 'Execute signals from the dashboard to open trades.'
                : 'Closed trades will appear here after you exit positions.'}
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {displayTrades.map(trade => {
            const isLong = trade.side === 'long';
            const isProfitable = trade.realized_pnl > 0;
            const position = positions?.find(p => p.symbol === trade.symbol);
            
            return (
              <Card 
                key={trade.id} 
                className={cn(
                  "bg-zinc-900/50 border-white/5 hover:border-white/10 transition-colors",
                  tab === 'closed' && isProfitable && "border-emerald-500/20",
                  tab === 'closed' && !isProfitable && "border-red-500/20"
                )}
                data-testid={`trade-${trade.id}`}
              >
                <CardContent className="p-4">
                  <div className="flex items-start justify-between">
                    {/* Trade Info */}
                    <div className="flex items-start gap-3">
                      <div className={cn(
                        "w-10 h-10 rounded-lg flex items-center justify-center",
                        isLong ? "bg-emerald-500/10 border border-emerald-500/30" : "bg-red-500/10 border border-red-500/30"
                      )}>
                        {isLong ? (
                          <TrendingUp className="w-5 h-5 text-emerald-500" />
                        ) : (
                          <TrendingDown className="w-5 h-5 text-red-500" />
                        )}
                      </div>
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-mono text-lg text-white font-semibold">
                            {trade.symbol}
                          </span>
                          <span className={cn(
                            "text-xs px-2 py-0.5 rounded uppercase font-medium",
                            isLong ? "badge-long" : "badge-short"
                          )}>
                            {trade.side}
                          </span>
                          {trade.leverage > 1 && (
                            <span className="text-xs px-2 py-0.5 rounded bg-zinc-800 text-zinc-400">
                              {trade.leverage}x
                            </span>
                          )}
                          {tab === 'closed' && trade.exit_reason && (
                            <span className={cn(
                              "text-xs px-2 py-0.5 rounded uppercase",
                              trade.exit_reason === 'tp' && "bg-emerald-500/10 text-emerald-500",
                              trade.exit_reason === 'sl' && "bg-red-500/10 text-red-500",
                              trade.exit_reason === 'manual' && "bg-zinc-800 text-zinc-400"
                            )}>
                              {trade.exit_reason}
                            </span>
                          )}
                        </div>
                        
                        {/* Price Details */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-3 text-xs">
                          <div>
                            <div className="text-zinc-500 mb-0.5">Entry</div>
                            <div className="font-mono text-white">${formatPrice(trade.entry_price)}</div>
                          </div>
                          {tab === 'closed' && trade.exit_price && (
                            <div>
                              <div className="text-zinc-500 mb-0.5">Exit</div>
                              <div className="font-mono text-white">${formatPrice(trade.exit_price)}</div>
                            </div>
                          )}
                          <div>
                            <div className="text-zinc-500 mb-0.5">Size</div>
                            <div className="font-mono text-white">{trade.quantity?.toFixed(4)}</div>
                          </div>
                          <div>
                            <div className="text-zinc-500 mb-0.5">Time</div>
                            <div className="font-mono text-zinc-400">{formatTime(trade.entry_time)}</div>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* P&L and Actions */}
                    <div className="text-right">
                      {tab === 'closed' ? (
                        <div>
                          <div className={cn(
                            "font-mono text-xl font-semibold",
                            isProfitable ? "text-emerald-500" : "text-red-500"
                          )}>
                            {isProfitable ? '+' : ''}{trade.realized_pnl?.toFixed(2)} USD
                          </div>
                          <div className={cn(
                            "text-sm font-mono",
                            isProfitable ? "text-emerald-400" : "text-red-400"
                          )}>
                            {isProfitable ? '+' : ''}{trade.realized_pnl_percent?.toFixed(2)}%
                          </div>
                        </div>
                      ) : (
                        <div className="flex flex-col items-end gap-2">
                          {position && (
                            <div className="text-right">
                              <div className={cn(
                                "font-mono text-lg font-semibold",
                                position.unrealized_pnl > 0 ? "text-emerald-500" : "text-red-500"
                              )}>
                                {position.unrealized_pnl > 0 ? '+' : ''}{position.unrealized_pnl?.toFixed(2)} USD
                              </div>
                              <div className="text-xs text-zinc-500 font-mono">
                                Unrealized
                              </div>
                            </div>
                          )}
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => onCloseTrade(trade.id)}
                            className="text-red-400 border-red-500/30 hover:bg-red-500/10"
                            data-testid={`close-trade-${trade.id}`}
                          >
                            <X className="w-3 h-3 mr-1" />
                            Close
                          </Button>
                        </div>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
