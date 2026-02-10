import React from 'react';
import { X, TrendingUp, TrendingDown } from 'lucide-react';
import { Button } from './ui/button';
import { cn } from '../lib/utils';

export default function PositionRow({ position, onClose }) {
  const isLong = position.side === 'long';
  const isProfitable = position.unrealized_pnl > 0;

  const formatPrice = (price) => {
    if (price >= 1000) return price.toLocaleString('en-US', { maximumFractionDigits: 2 });
    if (price >= 1) return price.toFixed(2);
    return price.toFixed(6);
  };

  return (
    <div 
      data-testid={`position-${position.id}`}
      className={cn(
        "flex items-center justify-between p-3 rounded-lg border transition-colors",
        isProfitable 
          ? "bg-emerald-500/5 border-emerald-500/20" 
          : "bg-red-500/5 border-red-500/20"
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
            <span className="font-mono text-sm text-white font-medium">{position.symbol}</span>
            <span className={cn(
              "text-[10px] px-1.5 py-0.5 rounded uppercase font-medium",
              isLong ? "badge-long" : "badge-short"
            )}>
              {position.side}
            </span>
            {position.leverage > 1 && (
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-400">
                {position.leverage}x
              </span>
            )}
          </div>
          <div className="text-xs text-zinc-500 font-mono mt-0.5">
            Entry: ${formatPrice(position.entry_price)} → Current: ${formatPrice(position.current_price)}
          </div>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="text-right">
          <div className={cn(
            "font-mono text-sm font-semibold",
            isProfitable ? "text-emerald-500" : "text-red-500"
          )}>
            {isProfitable ? '+' : ''}{position.unrealized_pnl?.toFixed(2) || '0.00'} USD
          </div>
          <div className={cn(
            "text-xs font-mono",
            isProfitable ? "text-emerald-400" : "text-red-400"
          )}>
            {isProfitable ? '+' : ''}{position.unrealized_pnl_percent?.toFixed(2) || '0.00'}%
          </div>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onClose(position)}
          className="h-8 px-2 text-zinc-400 hover:text-white hover:bg-white/10"
          data-testid={`close-position-${position.id}`}
        >
          <X className="w-4 h-4" />
        </Button>
      </div>
    </div>
  );
}
