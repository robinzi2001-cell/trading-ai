import React, { useState } from 'react';
import { Settings as SettingsIcon, Shield, Radio, RefreshCw, Save, AlertTriangle } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Switch } from '../components/ui/switch';
import { Slider } from '../components/ui/slider';
import { toast } from 'sonner';

export default function Settings({ settings, onUpdate, onReset, loading }) {
  const [formData, setFormData] = useState({
    initial_balance: settings?.initial_balance || 10000,
    paper_trading: settings?.paper_trading ?? true,
    auto_execute: settings?.auto_execute ?? false,
    max_risk_per_trade_percent: settings?.risk_settings?.max_risk_per_trade_percent || 2.0,
    max_open_positions: settings?.risk_settings?.max_open_positions || 5,
    min_risk_reward_ratio: settings?.risk_settings?.min_risk_reward_ratio || 1.5,
    default_leverage: settings?.risk_settings?.default_leverage || 1,
    telegram_enabled: settings?.telegram_enabled ?? false,
    email_enabled: settings?.email_enabled ?? false,
    webhook_enabled: settings?.webhook_enabled ?? true,
  });

  const [saving, setSaving] = useState(false);

  const handleChange = (key, value) => {
    setFormData(prev => ({ ...prev, [key]: value }));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await onUpdate(formData);
    } finally {
      setSaving(false);
    }
  };

  const handleReset = async () => {
    if (window.confirm('Are you sure you want to reset the demo account? All trades and signals will be deleted.')) {
      await onReset();
      setFormData({
        initial_balance: 10000,
        paper_trading: true,
        auto_execute: false,
        max_risk_per_trade_percent: 2.0,
        max_open_positions: 5,
        min_risk_reward_ratio: 1.5,
        default_leverage: 1,
        telegram_enabled: false,
        email_enabled: false,
        webhook_enabled: true,
      });
    }
  };

  if (loading) {
    return (
      <div className="p-4 md:p-6 lg:p-8 pb-20 md:pb-8">
        <div className="animate-pulse space-y-6">
          <div className="h-8 w-48 bg-zinc-800 rounded" />
          <div className="h-64 bg-zinc-800 rounded" />
          <div className="h-64 bg-zinc-800 rounded" />
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 md:p-6 lg:p-8 pb-20 md:pb-8" data-testid="settings-page">
      {/* Header */}
      <div className="glass-header -mx-4 md:-mx-6 lg:-mx-8 -mt-4 md:-mt-6 lg:-mt-8 px-4 md:px-6 lg:px-8 py-4 mb-6 sticky top-0 z-40">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <SettingsIcon className="w-5 h-5 text-zinc-400" />
            <h1 className="font-heading text-xl font-bold tracking-tight uppercase text-white">
              Settings
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleReset}
              className="text-red-400 border-red-500/30 hover:bg-red-500/10"
              data-testid="reset-demo-btn"
            >
              <RefreshCw className="w-3 h-3 mr-1" />
              Reset Demo
            </Button>
            <Button
              size="sm"
              onClick={handleSave}
              disabled={saving}
              className="bg-blue-500 hover:bg-blue-600"
              data-testid="save-settings-btn"
            >
              <Save className="w-3 h-3 mr-1" />
              {saving ? 'Saving...' : 'Save'}
            </Button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Trading Settings */}
        <Card className="bg-zinc-900/50 border-white/5">
          <CardHeader>
            <CardTitle className="font-heading text-lg font-semibold tracking-tight uppercase text-white flex items-center gap-2">
              <Shield className="w-4 h-4 text-blue-500" />
              Trading Settings
            </CardTitle>
            <CardDescription className="text-zinc-500">
              Configure your trading parameters and account settings
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Initial Balance */}
            <div className="space-y-2">
              <Label className="text-sm text-zinc-400">Initial Balance (USD)</Label>
              <Input
                type="number"
                value={formData.initial_balance}
                onChange={(e) => handleChange('initial_balance', parseFloat(e.target.value))}
                className="bg-zinc-800 border-white/10 font-mono"
                data-testid="input-initial-balance"
              />
            </div>

            {/* Paper Trading */}
            <div className="flex items-center justify-between">
              <div>
                <Label className="text-sm text-white">Paper Trading</Label>
                <p className="text-xs text-zinc-500">Simulate trades without real money</p>
              </div>
              <Switch
                checked={formData.paper_trading}
                onCheckedChange={(checked) => handleChange('paper_trading', checked)}
                data-testid="switch-paper-trading"
              />
            </div>

            {/* Auto Execute */}
            <div className="flex items-center justify-between">
              <div>
                <Label className="text-sm text-white">Auto Execute</Label>
                <p className="text-xs text-zinc-500">Automatically execute incoming signals</p>
              </div>
              <Switch
                checked={formData.auto_execute}
                onCheckedChange={(checked) => handleChange('auto_execute', checked)}
                data-testid="switch-auto-execute"
              />
            </div>

            {formData.auto_execute && (
              <div className="p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/30 flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 text-yellow-500 shrink-0 mt-0.5" />
                <p className="text-xs text-yellow-200">
                  Auto-execute is enabled. All incoming signals will be executed automatically based on your risk settings.
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Risk Management */}
        <Card className="bg-zinc-900/50 border-white/5">
          <CardHeader>
            <CardTitle className="font-heading text-lg font-semibold tracking-tight uppercase text-white flex items-center gap-2">
              <Shield className="w-4 h-4 text-emerald-500" />
              Risk Management
            </CardTitle>
            <CardDescription className="text-zinc-500">
              Configure position sizing and risk parameters
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Max Risk Per Trade */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label className="text-sm text-zinc-400">Max Risk Per Trade</Label>
                <span className="font-mono text-sm text-white">
                  {formData.max_risk_per_trade_percent}%
                </span>
              </div>
              <Slider
                value={[formData.max_risk_per_trade_percent]}
                onValueChange={([value]) => handleChange('max_risk_per_trade_percent', value)}
                min={0.5}
                max={10}
                step={0.5}
                className="w-full"
                data-testid="slider-max-risk"
              />
              <p className="text-xs text-zinc-500">
                Maximum percentage of account to risk on a single trade
              </p>
            </div>

            {/* Max Open Positions */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label className="text-sm text-zinc-400">Max Open Positions</Label>
                <span className="font-mono text-sm text-white">
                  {formData.max_open_positions}
                </span>
              </div>
              <Slider
                value={[formData.max_open_positions]}
                onValueChange={([value]) => handleChange('max_open_positions', value)}
                min={1}
                max={20}
                step={1}
                className="w-full"
                data-testid="slider-max-positions"
              />
            </div>

            {/* Min Risk/Reward */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label className="text-sm text-zinc-400">Min Risk/Reward Ratio</Label>
                <span className="font-mono text-sm text-white">
                  1:{formData.min_risk_reward_ratio}
                </span>
              </div>
              <Slider
                value={[formData.min_risk_reward_ratio]}
                onValueChange={([value]) => handleChange('min_risk_reward_ratio', value)}
                min={0.5}
                max={5}
                step={0.5}
                className="w-full"
                data-testid="slider-min-rr"
              />
            </div>

            {/* Default Leverage */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label className="text-sm text-zinc-400">Default Leverage</Label>
                <span className="font-mono text-sm text-white">
                  {formData.default_leverage}x
                </span>
              </div>
              <Slider
                value={[formData.default_leverage]}
                onValueChange={([value]) => handleChange('default_leverage', value)}
                min={1}
                max={20}
                step={1}
                className="w-full"
                data-testid="slider-default-leverage"
              />
            </div>
          </CardContent>
        </Card>

        {/* Signal Sources */}
        <Card className="bg-zinc-900/50 border-white/5 lg:col-span-2">
          <CardHeader>
            <CardTitle className="font-heading text-lg font-semibold tracking-tight uppercase text-white flex items-center gap-2">
              <Radio className="w-4 h-4 text-blue-500" />
              Signal Sources
            </CardTitle>
            <CardDescription className="text-zinc-500">
              Configure where trading signals are received from
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Webhook */}
              <div className="p-4 rounded-lg bg-zinc-800/50 border border-white/5">
                <div className="flex items-center justify-between mb-3">
                  <Label className="text-sm text-white">Webhook</Label>
                  <Switch
                    checked={formData.webhook_enabled}
                    onCheckedChange={(checked) => handleChange('webhook_enabled', checked)}
                    data-testid="switch-webhook"
                  />
                </div>
                <p className="text-xs text-zinc-500">
                  Receive signals via HTTP webhook (TradingView compatible)
                </p>
                {formData.webhook_enabled && (
                  <div className="mt-3 p-2 rounded bg-zinc-900 text-xs font-mono text-zinc-400 break-all">
                    POST /api/signals/webhook
                  </div>
                )}
              </div>

              {/* Telegram */}
              <div className="p-4 rounded-lg bg-zinc-800/50 border border-white/5">
                <div className="flex items-center justify-between mb-3">
                  <Label className="text-sm text-white">Telegram</Label>
                  <Switch
                    checked={formData.telegram_enabled}
                    onCheckedChange={(checked) => handleChange('telegram_enabled', checked)}
                    data-testid="switch-telegram"
                  />
                </div>
                <p className="text-xs text-zinc-500">
                  Monitor Telegram channels for trading signals
                </p>
                <span className="text-xs text-yellow-500">Coming soon</span>
              </div>

              {/* Email */}
              <div className="p-4 rounded-lg bg-zinc-800/50 border border-white/5">
                <div className="flex items-center justify-between mb-3">
                  <Label className="text-sm text-white">Email</Label>
                  <Switch
                    checked={formData.email_enabled}
                    onCheckedChange={(checked) => handleChange('email_enabled', checked)}
                    data-testid="switch-email"
                  />
                </div>
                <p className="text-xs text-zinc-500">
                  Parse trading signals from emails
                </p>
                <span className="text-xs text-yellow-500">Coming soon</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
