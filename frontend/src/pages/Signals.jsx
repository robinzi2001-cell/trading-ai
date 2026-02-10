import React, { useState } from 'react';
import { Radio, Filter, Plus, Search } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent } from '../components/ui/card';
import SignalCard from '../components/SignalCard';

export default function Signals({ 
  signals, 
  loading, 
  onExecuteSignal, 
  onDismissSignal,
  onCreateSampleSignals 
}) {
  const [filter, setFilter] = useState('pending'); // pending, executed, dismissed, all
  const [search, setSearch] = useState('');

  const filteredSignals = signals?.filter(signal => {
    // Status filter
    if (filter === 'pending' && (signal.executed || signal.dismissed)) return false;
    if (filter === 'executed' && !signal.executed) return false;
    if (filter === 'dismissed' && !signal.dismissed) return false;
    
    // Search filter
    if (search && !signal.asset.toLowerCase().includes(search.toLowerCase())) return false;
    
    return true;
  }) || [];

  const sortedSignals = [...filteredSignals].sort((a, b) => {
    if (filter === 'pending') {
      return b.confidence - a.confidence;
    }
    return new Date(b.received_at) - new Date(a.received_at);
  });

  const pendingCount = signals?.filter(s => !s.executed && !s.dismissed).length || 0;
  const executedCount = signals?.filter(s => s.executed).length || 0;
  const dismissedCount = signals?.filter(s => s.dismissed).length || 0;

  return (
    <div className="p-4 md:p-6 lg:p-8 pb-20 md:pb-8" data-testid="signals-page">
      {/* Header */}
      <div className="glass-header -mx-4 md:-mx-6 lg:-mx-8 -mt-4 md:-mt-6 lg:-mt-8 px-4 md:px-6 lg:px-8 py-4 mb-6 sticky top-0 z-40">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Radio className="w-5 h-5 text-blue-500" />
            <h1 className="font-heading text-xl font-bold tracking-tight uppercase text-white">
              Signals
            </h1>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={onCreateSampleSignals}
            className="text-xs"
            data-testid="add-sample-signals-btn"
          >
            <Plus className="w-3 h-3 mr-1" />
            Add Samples
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col md:flex-row gap-4 mb-6">
        {/* Status Tabs */}
        <div className="flex gap-2">
          {[
            { key: 'pending', label: 'Pending', count: pendingCount },
            { key: 'executed', label: 'Executed', count: executedCount },
            { key: 'dismissed', label: 'Dismissed', count: dismissedCount },
            { key: 'all', label: 'All', count: signals?.length || 0 },
          ].map(tab => (
            <Button
              key={tab.key}
              variant={filter === tab.key ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setFilter(tab.key)}
              className={filter === tab.key ? 'bg-white/10' : 'text-zinc-400'}
              data-testid={`filter-${tab.key}`}
            >
              {tab.label}
              <span className="ml-1.5 text-xs font-mono opacity-60">
                {tab.count}
              </span>
            </Button>
          ))}
        </div>

        {/* Search */}
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
          <Input
            placeholder="Search by asset..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 bg-zinc-900/50 border-white/10"
            data-testid="search-signals"
          />
        </div>
      </div>

      {/* Signals Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map(i => (
            <Card key={i} className="bg-zinc-900/50 border-white/5 animate-pulse">
              <CardContent className="p-4 space-y-3">
                <div className="h-10 bg-zinc-800 rounded" />
                <div className="h-20 bg-zinc-800 rounded" />
                <div className="h-8 bg-zinc-800 rounded" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : sortedSignals.length === 0 ? (
        <Card className="bg-zinc-900/50 border-white/5">
          <CardContent className="py-16 text-center">
            <Radio className="w-16 h-16 text-zinc-700 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-white mb-2">
              {filter === 'pending' ? 'No pending signals' : 'No signals found'}
            </h3>
            <p className="text-zinc-500 text-sm mb-6">
              {filter === 'pending' 
                ? 'New signals will appear here when received via webhook or manual entry.'
                : 'Try adjusting your filters or search query.'}
            </p>
            {filter === 'pending' && (
              <Button onClick={onCreateSampleSignals} data-testid="create-signals-btn">
                <Plus className="w-4 h-4 mr-2" />
                Create Sample Signals
              </Button>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {sortedSignals.map((signal, index) => (
            <SignalCard
              key={signal.id}
              signal={signal}
              onExecute={onExecuteSignal}
              onDismiss={onDismissSignal}
              isHighPriority={filter === 'pending' && index === 0}
            />
          ))}
        </div>
      )}
    </div>
  );
}
