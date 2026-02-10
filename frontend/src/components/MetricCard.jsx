import React from 'react';
import { ArrowUpRight, ArrowDownRight, TrendingUp, TrendingDown } from 'lucide-react';
import { cn } from '../lib/utils';

export default function MetricCard({ 
  label, 
  value, 
  change, 
  trend, 
  prefix = '',
  suffix = '',
  variant = 'default',
  loading = false
}) {
  const isPositive = trend === 'up' || (typeof change === 'number' && change > 0);
  const isNegative = trend === 'down' || (typeof change === 'number' && change < 0);

  const formatValue = (val) => {
    if (typeof val === 'number') {
      if (Math.abs(val) >= 1000000) {
        return (val / 1000000).toFixed(2) + 'M';
      }
      if (Math.abs(val) >= 1000) {
        return (val / 1000).toFixed(2) + 'K';
      }
      if (val % 1 !== 0) {
        return val.toFixed(2);
      }
      return val.toLocaleString();
    }
    return val;
  };

  const formatChange = (val) => {
    if (typeof val !== 'number') return val;
    const sign = val > 0 ? '+' : '';
    return `${sign}${val.toFixed(2)}%`;
  };

  if (loading) {
    return (
      <div className="p-4 rounded-lg bg-zinc-900/50 border border-white/5 animate-pulse">
        <div className="h-3 w-20 bg-zinc-800 rounded mb-2" />
        <div className="h-7 w-32 bg-zinc-800 rounded mb-2" />
        <div className="h-3 w-16 bg-zinc-800 rounded" />
      </div>
    );
  }

  return (
    <div 
      className={cn(
        "p-4 rounded-lg border transition-all duration-200 hover-lift",
        variant === 'highlight' && isPositive && "bg-emerald-500/5 border-emerald-500/20",
        variant === 'highlight' && isNegative && "bg-red-500/5 border-red-500/20",
        variant === 'default' && "bg-zinc-900/50 border-white/5 hover:border-white/10"
      )}
    >
      <div className="flex items-center justify-between">
        <span className="text-[10px] text-zinc-500 uppercase tracking-wide font-medium">
          {label}
        </span>
        {(trend || change !== undefined) && (
          <div className={cn(
            "flex items-center gap-0.5 text-xs font-mono",
            isPositive && "text-emerald-500",
            isNegative && "text-red-500",
            !isPositive && !isNegative && "text-zinc-400"
          )}>
            {isPositive && <ArrowUpRight className="w-3 h-3" />}
            {isNegative && <ArrowDownRight className="w-3 h-3" />}
            {change !== undefined && <span>{formatChange(change)}</span>}
          </div>
        )}
      </div>
      <div className={cn(
        "font-mono text-2xl font-semibold mt-1",
        variant === 'highlight' && isPositive && "text-emerald-500",
        variant === 'highlight' && isNegative && "text-red-500",
        (variant === 'default' || (!isPositive && !isNegative)) && "text-white"
      )}>
        {prefix}{formatValue(value)}{suffix}
      </div>
    </div>
  );
}

export function StatRow({ label, value, variant = 'default' }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-white/5 last:border-0">
      <span className="text-sm text-zinc-400">{label}</span>
      <span className={cn(
        "font-mono text-sm",
        variant === 'success' && "text-emerald-500",
        variant === 'danger' && "text-red-500",
        variant === 'warning' && "text-yellow-500",
        variant === 'default' && "text-white"
      )}>
        {value}
      </span>
    </div>
  );
}
