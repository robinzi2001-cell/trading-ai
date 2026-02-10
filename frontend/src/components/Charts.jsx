import React from 'react';
import { 
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell
} from 'recharts';

const COLORS = ['#22c55e', '#ef4444', '#3b82f6', '#f59e0b'];

export function EquityCurveChart({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="h-48 flex items-center justify-center text-zinc-500 text-sm">
        No data available
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={200}>
      <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
          </linearGradient>
        </defs>
        <XAxis 
          dataKey="time" 
          axisLine={false}
          tickLine={false}
          tick={{ fill: '#71717a', fontSize: 10 }}
        />
        <YAxis 
          axisLine={false}
          tickLine={false}
          tick={{ fill: '#71717a', fontSize: 10 }}
          width={60}
          tickFormatter={(value) => `$${value.toLocaleString()}`}
        />
        <Tooltip 
          contentStyle={{
            background: '#18181b',
            border: '1px solid #27272a',
            borderRadius: '4px',
            fontSize: '12px'
          }}
          labelStyle={{ color: '#71717a' }}
          itemStyle={{ color: '#fff' }}
          formatter={(value) => [`$${value.toLocaleString()}`, 'Balance']}
        />
        <Area 
          type="monotone" 
          dataKey="value" 
          stroke="#3b82f6" 
          strokeWidth={2}
          fill="url(#colorValue)"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

export function WinRateChart({ winRate, wins, losses }) {
  const data = [
    { name: 'Wins', value: wins },
    { name: 'Losses', value: losses },
  ];

  return (
    <div className="flex items-center gap-4">
      <div className="w-24 h-24">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={30}
              outerRadius={40}
              paddingAngle={2}
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell 
                  key={`cell-${index}`} 
                  fill={index === 0 ? '#22c55e' : '#ef4444'} 
                />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>
      </div>
      <div className="flex-1">
        <div className="text-2xl font-mono font-bold text-white">
          {winRate?.toFixed(1) || 0}%
        </div>
        <div className="text-xs text-zinc-500 mt-1">Win Rate</div>
        <div className="flex items-center gap-3 mt-2 text-xs">
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-full bg-emerald-500" />
            <span className="text-zinc-400">{wins} wins</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-full bg-red-500" />
            <span className="text-zinc-400">{losses} losses</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export function PnLChart({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="h-32 flex items-center justify-center text-zinc-500 text-sm">
        No trade data
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={120}>
      <AreaChart data={data} margin={{ top: 5, right: 5, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="colorPnL" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3}/>
            <stop offset="95%" stopColor="#22c55e" stopOpacity={0}/>
          </linearGradient>
        </defs>
        <Tooltip 
          contentStyle={{
            background: '#18181b',
            border: '1px solid #27272a',
            borderRadius: '4px',
            fontSize: '11px'
          }}
          formatter={(value) => [`$${value.toFixed(2)}`, 'P&L']}
        />
        <Area 
          type="monotone" 
          dataKey="pnl" 
          stroke="#22c55e" 
          strokeWidth={1.5}
          fill="url(#colorPnL)"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
