import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Radio, 
  TrendingUp, 
  Wallet, 
  Settings,
  Activity,
  Brain
} from 'lucide-react';
import { cn } from '../lib/utils';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/signals', icon: Radio, label: 'Signals' },
  { to: '/trades', icon: TrendingUp, label: 'Trades' },
  { to: '/portfolio', icon: Wallet, label: 'Portfolio' },
  { to: '/ai', icon: Brain, label: 'AI Center' },
  { to: '/settings', icon: Settings, label: 'Settings' },
];

export default function Sidebar({ pendingSignalsCount = 0, openTradesCount = 0 }) {
  return (
    <>
      {/* Desktop Sidebar */}
      <aside 
        data-testid="sidebar"
        className="fixed left-0 top-0 h-screen w-64 border-r border-white/10 bg-[#09090b] hidden md:flex flex-col z-50"
      >
        {/* Logo */}
        <div className="p-6 border-b border-white/10">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-blue-500/10 border border-blue-500/30 flex items-center justify-center">
              <Activity className="w-5 h-5 text-blue-500" />
            </div>
            <div>
              <h1 className="font-heading text-xl font-bold tracking-tight text-white uppercase">
                TRADING AI
              </h1>
              <p className="text-xs text-zinc-500">Signal Processing</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              data-testid={`nav-${item.label.toLowerCase()}`}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200',
                  'hover:bg-white/5 hover:translate-x-1',
                  isActive 
                    ? 'bg-white/10 text-white border border-white/10' 
                    : 'text-zinc-400 hover:text-white'
                )
              }
            >
              <item.icon className="w-5 h-5" />
              <span className="text-sm font-medium">{item.label}</span>
              {item.label === 'Signals' && pendingSignalsCount > 0 && (
                <span className="ml-auto bg-blue-500 text-white text-xs px-2 py-0.5 rounded-full font-mono">
                  {pendingSignalsCount}
                </span>
              )}
              {item.label === 'Trades' && openTradesCount > 0 && (
                <span className="ml-auto bg-emerald-500/20 text-emerald-500 text-xs px-2 py-0.5 rounded-full font-mono">
                  {openTradesCount}
                </span>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Status */}
        <div className="p-4 border-t border-white/10">
          <div className="flex items-center gap-2 text-xs text-zinc-500">
            <span className="w-2 h-2 rounded-full bg-emerald-500 live-indicator" />
            <span>Paper Trading Active</span>
          </div>
        </div>
      </aside>

      {/* Mobile Bottom Navigation */}
      <nav className="fixed bottom-0 left-0 right-0 bg-[#09090b] border-t border-white/10 md:hidden z-50">
        <div className="flex justify-around py-2">
          {navItems.slice(0, 4).map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                cn(
                  'flex flex-col items-center gap-1 p-2 rounded-lg',
                  isActive ? 'text-white' : 'text-zinc-500'
                )
              }
            >
              <item.icon className="w-5 h-5" />
              <span className="text-[10px]">{item.label}</span>
            </NavLink>
          ))}
        </div>
      </nav>
    </>
  );
}
