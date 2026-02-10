import React from 'react';
import { TrendingUp, TrendingDown, X, Zap, Clock } from 'lucide-react';
import { Button } from './ui/button';
import { cn } from '../lib/utils';

export default function SignalCard({ 
  signal, 
  onExecute, 
  onDismiss, 
  isHighPriority = false,
  compact = false 
}) {
  const isLong = signal.action === 'long' || signal.action === 'buy';
  const confidencePercent = (signal.confidence * 100).toFixed(0);
  
  const riskReward = signal.take_profits?.length > 0 
    ? Math.abs(signal.take_profits[0] - signal.entry) / Math.abs(signal.entry - signal.stop_loss)
    : null;

  const formatPrice = (price) => {
    if (price >= 1000) return price.toLocaleString('en-US', { maximumFractionDigits: 0 });
    if (price >= 1) return price.toFixed(2);
    return price.toFixed(4);
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = (now - date) / 1000;
    
    if (diff < 60) return 'Just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return date.toLocaleDateString();
  };

  if (compact) {
    return (
      <div 
        data-testid={`signal-card-${signal.id}`}
        className={cn(
          "flex items-center justify-between p-3 rounded-lg border border-white/5 bg-zinc-900/50",
          "hover:border-white/10 transition-colors"
        )}
      >
        <div className="flex items-center gap-3">
          <div className={cn(
            "w-8 h-8 rounded flex items-center justify-center",
            isLong ? "bg-emerald-500/10" : "bg-red-500/10"
          )}>
            {isLong ? (
              <TrendingUp className="w-4 h-4 text-emerald-500" />
            ) : (
              <TrendingDown className="w-4 h-4 text-red-500" />
            )}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-sm text-white font-medium">{signal.asset}</span>
              <span className={cn(
                "text-xs px-1.5 py-0.5 rounded uppercase font-medium",
                isLong ? "badge-long" : "badge-short"
              )}>
                {signal.action}
              </span>
            </div>
            <div className="text-xs text-zinc-500 font-mono">
              @ {formatPrice(signal.entry)}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-zinc-400">{confidencePercent}%</span>
          <Button
            size="sm"
            variant="ghost"
            className="h-7 px-2 text-emerald-500 hover:bg-emerald-500/10"
            onClick={() => onExecute(signal.id)}
            data-testid={`execute-signal-${signal.id}`}
          >
            <Zap className="w-3 h-3" />
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div 
      data-testid={`signal-card-${signal.id}`}
      className={cn(
        "relative p-4 rounded-lg border bg-zinc-900/50 transition-all duration-200 hover-lift",
        isHighPriority ? "signal-card-highlight border-blue-500/30" : "border-white/5 hover:border-white/10"
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
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
            <div className="flex items-center gap-2">
              <span className="font-mono text-lg text-white font-semibold">{signal.asset}</span>
              <span className={cn(
                "text-xs px-2 py-0.5 rounded uppercase font-semibold",
                isLong ? "badge-long" : "badge-short"
              )}>
                {signal.action}
              </span>
              {signal.leverage > 1 && (
                <span className="text-xs px-2 py-0.5 rounded bg-zinc-800 text-zinc-400">
                  {signal.leverage}x
                </span>
              )}
            </div>
            <div className="flex items-center gap-2 mt-1 text-xs text-zinc-500">
              <Clock className="w-3 h-3" />
              <span>{formatTime(signal.received_at)}</span>
              <span className="text-zinc-600">•</span>
              <span className="capitalize">{signal.source}</span>
            </div>
          </div>
        </div>
        
        <button
          onClick={() => onDismiss(signal.id)}
          className="p-1 hover:bg-white/5 rounded text-zinc-500 hover:text-white transition-colors"
          data-testid={`dismiss-signal-${signal.id}`}
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Price Levels */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        <div className="p-2 rounded bg-zinc-800/50">
          <div className="text-[10px] text-zinc-500 uppercase tracking-wide mb-1">Entry</div>
          <div className="font-mono text-sm text-white">${formatPrice(signal.entry)}</div>
        </div>
        <div className="p-2 rounded bg-red-500/5 border border-red-500/10">
          <div className="text-[10px] text-zinc-500 uppercase tracking-wide mb-1">Stop Loss</div>
          <div className="font-mono text-sm text-red-400">${formatPrice(signal.stop_loss)}</div>
        </div>
        <div className="p-2 rounded bg-emerald-500/5 border border-emerald-500/10">
          <div className="text-[10px] text-zinc-500 uppercase tracking-wide mb-1">Take Profit</div>
          <div className="font-mono text-sm text-emerald-400">
            {signal.take_profits?.length > 0 ? `$${formatPrice(signal.take_profits[0])}` : '-'}
          </div>
        </div>
      </div>

      {/* Confidence Bar */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-1">
          <span className="text-[10px] text-zinc-500 uppercase tracking-wide">Confidence</span>
          <span className="font-mono text-xs text-white">{confidencePercent}%</span>
        </div>
        <div className="h-1.5 bg-zinc-800 rounded-full overflow-hidden">
          <div 
            className="h-full confidence-bar transition-all duration-500"
            style={{ width: `${confidencePercent}%` }}
          />
        </div>
      </div>

      {/* Stats Row */}
      <div className="flex items-center gap-4 mb-4 text-xs">
        {riskReward && (
          <div className="flex items-center gap-1.5">
            <span className="text-zinc-500">R:R</span>
            <span className={cn(
              "font-mono font-medium",
              riskReward >= 2 ? "text-emerald-400" : riskReward >= 1 ? "text-yellow-400" : "text-red-400"
            )}>
              1:{riskReward.toFixed(1)}
            </span>
          </div>
        )}
        {signal.take_profits?.length > 1 && (
          <div className="flex items-center gap-1.5">
            <span className="text-zinc-500">Targets</span>
            <span className="font-mono text-zinc-300">{signal.take_profits.length}</span>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex gap-2">
        <Button
          onClick={() => onExecute(signal.id)}
          className="flex-1 bg-emerald-500 hover:bg-emerald-600 text-white button-press"
          data-testid={`execute-signal-btn-${signal.id}`}
        >
          <Zap className="w-4 h-4 mr-2" />
          Execute Trade
        </Button>
      </div>
    </div>
  );
}
