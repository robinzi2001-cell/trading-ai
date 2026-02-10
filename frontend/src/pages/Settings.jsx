import React, { useState, useEffect } from 'react';
import { 
  Settings as SettingsIcon, 
  Shield, 
  Radio, 
  RefreshCw, 
  Save, 
  AlertTriangle,
  MessageCircle,
  Wallet,
  ExternalLink,
  CheckCircle,
  XCircle,
  Copy
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Switch } from '../components/ui/switch';
import { Slider } from '../components/ui/slider';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { toast } from 'sonner';
import { api } from '../App';

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
  const [telegramConfig, setTelegramConfig] = useState(null);
  const [binanceConfig, setBinanceConfig] = useState(null);
  const [knownChannels, setKnownChannels] = useState([]);
  const [botStatus, setBotStatus] = useState(null);

  useEffect(() => {
    fetchIntegrationConfigs();
  }, []);

  const fetchIntegrationConfigs = async () => {
    try {
      const [tgRes, bnRes, channelsRes, botRes] = await Promise.all([
        api.get('/telegram/config'),
        api.get('/binance/config'),
        api.get('/telegram/channels'),
        api.get('/telegram/bot/status')
      ]);
      setTelegramConfig(tgRes.data);
      setBinanceConfig(bnRes.data);
      setKnownChannels(channelsRes.data.channels || []);
      setBotStatus(botRes.data);
    } catch (error) {
      console.error('Failed to fetch integration configs:', error);
    }
  };

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
    if (window.confirm('Bist du sicher? Alle Trades und Signale werden gelöscht.')) {
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

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Kopiert!');
  };

  if (loading) {
    return (
      <div className="p-4 md:p-6 lg:p-8 pb-20 md:pb-8">
        <div className="animate-pulse space-y-6">
          <div className="h-8 w-48 bg-zinc-800 rounded" />
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

      <Tabs defaultValue="trading" className="w-full">
        <TabsList className="bg-zinc-900 border border-white/10 mb-6">
          <TabsTrigger value="trading" className="data-[state=active]:bg-white/10">
            <Shield className="w-4 h-4 mr-2" />
            Trading
          </TabsTrigger>
          <TabsTrigger value="telegram" className="data-[state=active]:bg-white/10">
            <MessageCircle className="w-4 h-4 mr-2" />
            Telegram
          </TabsTrigger>
          <TabsTrigger value="binance" className="data-[state=active]:bg-white/10">
            <Wallet className="w-4 h-4 mr-2" />
            Binance
          </TabsTrigger>
          <TabsTrigger value="sources" className="data-[state=active]:bg-white/10">
            <Radio className="w-4 h-4 mr-2" />
            Quellen
          </TabsTrigger>
        </TabsList>

        {/* TRADING TAB */}
        <TabsContent value="trading">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Trading Settings */}
            <Card className="bg-zinc-900/50 border-white/5">
              <CardHeader>
                <CardTitle className="font-heading text-lg font-semibold tracking-tight uppercase text-white flex items-center gap-2">
                  <Shield className="w-4 h-4 text-blue-500" />
                  Trading Settings
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-2">
                  <Label className="text-sm text-zinc-400">Initial Balance (USD)</Label>
                  <Input
                    type="number"
                    value={formData.initial_balance}
                    onChange={(e) => handleChange('initial_balance', parseFloat(e.target.value))}
                    className="bg-zinc-800 border-white/10 font-mono"
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label className="text-sm text-white">Paper Trading</Label>
                    <p className="text-xs text-zinc-500">Simuliere Trades ohne echtes Geld</p>
                  </div>
                  <Switch
                    checked={formData.paper_trading}
                    onCheckedChange={(checked) => handleChange('paper_trading', checked)}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label className="text-sm text-white">Auto Execute</Label>
                    <p className="text-xs text-zinc-500">Signale automatisch ausführen</p>
                  </div>
                  <Switch
                    checked={formData.auto_execute}
                    onCheckedChange={(checked) => handleChange('auto_execute', checked)}
                  />
                </div>

                {formData.auto_execute && (
                  <div className="p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/30 flex items-start gap-2">
                    <AlertTriangle className="w-4 h-4 text-yellow-500 shrink-0 mt-0.5" />
                    <p className="text-xs text-yellow-200">
                      Auto-Execute aktiv! Alle Signale werden automatisch ausgeführt.
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
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label className="text-sm text-zinc-400">Max Risk Per Trade</Label>
                    <span className="font-mono text-sm text-white">{formData.max_risk_per_trade_percent}%</span>
                  </div>
                  <Slider
                    value={[formData.max_risk_per_trade_percent]}
                    onValueChange={([value]) => handleChange('max_risk_per_trade_percent', value)}
                    min={0.5}
                    max={10}
                    step={0.5}
                  />
                </div>

                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label className="text-sm text-zinc-400">Max Open Positions</Label>
                    <span className="font-mono text-sm text-white">{formData.max_open_positions}</span>
                  </div>
                  <Slider
                    value={[formData.max_open_positions]}
                    onValueChange={([value]) => handleChange('max_open_positions', value)}
                    min={1}
                    max={20}
                    step={1}
                  />
                </div>

                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label className="text-sm text-zinc-400">Min Risk/Reward Ratio</Label>
                    <span className="font-mono text-sm text-white">1:{formData.min_risk_reward_ratio}</span>
                  </div>
                  <Slider
                    value={[formData.min_risk_reward_ratio]}
                    onValueChange={([value]) => handleChange('min_risk_reward_ratio', value)}
                    min={0.5}
                    max={5}
                    step={0.5}
                  />
                </div>

                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label className="text-sm text-zinc-400">Default Leverage</Label>
                    <span className="font-mono text-sm text-white">{formData.default_leverage}x</span>
                  </div>
                  <Slider
                    value={[formData.default_leverage]}
                    onValueChange={([value]) => handleChange('default_leverage', value)}
                    min={1}
                    max={20}
                    step={1}
                  />
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* TELEGRAM TAB */}
        <TabsContent value="telegram">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Bot Status Card */}
            {botStatus?.configured && (
              <Card className="bg-emerald-500/5 border-emerald-500/20 lg:col-span-2">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-emerald-500/20 flex items-center justify-center">
                        <MessageCircle className="w-5 h-5 text-emerald-500" />
                      </div>
                      <div>
                        <h3 className="font-medium text-white flex items-center gap-2">
                          @{botStatus.bot_username}
                          {botStatus.running && (
                            <span className="w-2 h-2 rounded-full bg-emerald-500 live-indicator" />
                          )}
                        </h3>
                        <p className="text-xs text-zinc-400">
                          {botStatus.running ? 'Bot ist aktiv und empfängt Signale' : 'Bot ist konfiguriert aber nicht aktiv'}
                        </p>
                      </div>
                    </div>
                    <a
                      href={botStatus.bot_link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-4 py-2 rounded-lg bg-blue-500 hover:bg-blue-600 text-white text-sm font-medium flex items-center gap-2 transition-colors"
                    >
                      Bot öffnen
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  </div>
                  <div className="mt-3 p-3 rounded-lg bg-zinc-900/50 text-xs text-zinc-400">
                    <strong className="text-white">So nutzt du den Bot:</strong> Sende Trading-Signale direkt an den Bot. 
                    Er parsed sie automatisch und fügt sie dem Dashboard hinzu.
                  </div>
                </CardContent>
              </Card>
            )}

            <Card className="bg-zinc-900/50 border-white/5">
              <CardHeader>
                <CardTitle className="font-heading text-lg font-semibold tracking-tight uppercase text-white flex items-center gap-2">
                  <MessageCircle className="w-4 h-4 text-blue-500" />
                  Telegram Integration
                </CardTitle>
                <CardDescription className="text-zinc-500">
                  Empfange Trading-Signale von Telegram-Channels
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center gap-2 p-3 rounded-lg bg-zinc-800/50">
                  {telegramConfig?.configured ? (
                    <CheckCircle className="w-5 h-5 text-emerald-500" />
                  ) : (
                    <XCircle className="w-5 h-5 text-red-500" />
                  )}
                  <span className="text-sm">
                    {telegramConfig?.configured ? 'API Credentials konfiguriert' : 'API Credentials fehlen'}
                  </span>
                </div>

                <div className="space-y-2 p-4 rounded-lg bg-zinc-800/30 border border-white/5">
                  <h4 className="text-sm font-medium text-white">Setup-Anleitung:</h4>
                  <ol className="text-xs text-zinc-400 space-y-2 list-decimal list-inside">
                    <li>Gehe zu <a href="https://my.telegram.org" target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline">my.telegram.org</a></li>
                    <li>Erstelle eine App und kopiere API_ID und API_HASH</li>
                    <li>Füge diese zur .env Datei hinzu:
                      <div className="mt-1 p-2 rounded bg-zinc-900 font-mono text-[10px]">
                        TELEGRAM_API_ID=your_id<br/>
                        TELEGRAM_API_HASH=your_hash
                      </div>
                    </li>
                  </ol>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label className="text-sm text-white">Telegram Listener</Label>
                    <p className="text-xs text-zinc-500">Channels automatisch überwachen</p>
                  </div>
                  <Switch
                    checked={formData.telegram_enabled}
                    onCheckedChange={(checked) => handleChange('telegram_enabled', checked)}
                    disabled={!telegramConfig?.configured}
                  />
                </div>
              </CardContent>
            </Card>

            <Card className="bg-zinc-900/50 border-white/5">
              <CardHeader>
                <CardTitle className="text-sm text-zinc-400 uppercase tracking-wide">
                  Empfohlene Signal-Channels
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {knownChannels.map((channel) => (
                  <div key={channel.id} className="p-3 rounded-lg bg-zinc-800/50 border border-white/5">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-white">{channel.name}</span>
                      <span className="text-xs px-2 py-0.5 rounded bg-blue-500/20 text-blue-400">
                        {channel.signal_type}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-zinc-500">
                      <span>@{channel.username}</span>
                      <button 
                        onClick={() => copyToClipboard(channel.username)}
                        className="hover:text-white"
                      >
                        <Copy className="w-3 h-3" />
                      </button>
                    </div>
                    {channel.format_hints && (
                      <div className="mt-2 text-[10px] text-zinc-500">
                        {channel.format_hints.multiple_targets && '• Multiple TPs '}
                        {channel.format_hints.clear_structure && '• Klare Struktur '}
                      </div>
                    )}
                  </div>
                ))}

                <div className="p-3 rounded-lg border border-dashed border-white/10 text-center">
                  <p className="text-xs text-zinc-500">
                    Weitere Channels können manuell hinzugefügt werden
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* BINANCE TAB */}
        <TabsContent value="binance">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="bg-zinc-900/50 border-white/5">
              <CardHeader>
                <CardTitle className="font-heading text-lg font-semibold tracking-tight uppercase text-white flex items-center gap-2">
                  <Wallet className="w-4 h-4 text-yellow-500" />
                  Binance Futures
                </CardTitle>
                <CardDescription className="text-zinc-500">
                  Verbinde mit Binance für Live-Trading
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center gap-2 p-3 rounded-lg bg-zinc-800/50">
                  {binanceConfig?.configured ? (
                    <CheckCircle className="w-5 h-5 text-emerald-500" />
                  ) : (
                    <XCircle className="w-5 h-5 text-red-500" />
                  )}
                  <span className="text-sm">
                    {binanceConfig?.configured ? 'API Credentials konfiguriert' : 'API Credentials fehlen'}
                  </span>
                  {binanceConfig?.configured && (
                    <span className={`ml-auto text-xs px-2 py-0.5 rounded ${
                      binanceConfig?.testnet ? 'bg-yellow-500/20 text-yellow-400' : 'bg-red-500/20 text-red-400'
                    }`}>
                      {binanceConfig?.testnet ? 'Testnet' : 'LIVE'}
                    </span>
                  )}
                </div>

                <div className="space-y-2 p-4 rounded-lg bg-zinc-800/30 border border-white/5">
                  <h4 className="text-sm font-medium text-white">Testnet Setup:</h4>
                  <ol className="text-xs text-zinc-400 space-y-2 list-decimal list-inside">
                    <li>Gehe zu <a href="https://testnet.binancefuture.com" target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline inline-flex items-center gap-1">
                      testnet.binancefuture.com <ExternalLink className="w-3 h-3" />
                    </a></li>
                    <li>Erstelle einen Account und generiere API Keys</li>
                    <li>Füge diese zur .env Datei hinzu:
                      <div className="mt-1 p-2 rounded bg-zinc-900 font-mono text-[10px]">
                        BINANCE_API_KEY=your_key<br/>
                        BINANCE_SECRET=your_secret<br/>
                        BINANCE_TESTNET=true
                      </div>
                    </li>
                  </ol>
                </div>

                {!formData.paper_trading && (
                  <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30 flex items-start gap-2">
                    <AlertTriangle className="w-4 h-4 text-red-500 shrink-0 mt-0.5" />
                    <p className="text-xs text-red-200">
                      <strong>Warnung:</strong> Paper Trading ist deaktiviert! 
                      Trades werden mit echtem Geld ausgeführt.
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card className="bg-zinc-900/50 border-white/5">
              <CardHeader>
                <CardTitle className="text-sm text-zinc-400 uppercase tracking-wide">
                  Weitere Broker (Coming Soon)
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {[
                  { name: 'MetaTrader 5', status: 'planned' },
                  { name: 'Interactive Brokers', status: 'planned' },
                  { name: 'Alpaca', status: 'planned' },
                  { name: 'Bybit', status: 'planned' },
                ].map((broker) => (
                  <div key={broker.name} className="p-3 rounded-lg bg-zinc-800/30 border border-white/5 opacity-50">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-zinc-400">{broker.name}</span>
                      <span className="text-[10px] px-2 py-0.5 rounded bg-zinc-700 text-zinc-400">
                        {broker.status}
                      </span>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* SOURCES TAB */}
        <TabsContent value="sources">
          <Card className="bg-zinc-900/50 border-white/5">
            <CardHeader>
              <CardTitle className="font-heading text-lg font-semibold tracking-tight uppercase text-white flex items-center gap-2">
                <Radio className="w-4 h-4 text-blue-500" />
                Signal Quellen
              </CardTitle>
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
                    />
                  </div>
                  <p className="text-xs text-zinc-500 mb-3">
                    REST API für externe Signale (TradingView-kompatibel)
                  </p>
                  {formData.webhook_enabled && (
                    <div className="p-2 rounded bg-zinc-900 text-xs font-mono text-zinc-400">
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
                      disabled={!telegramConfig?.configured}
                    />
                  </div>
                  <p className="text-xs text-zinc-500">
                    Überwacht Telegram-Channels für Signale
                  </p>
                  {!telegramConfig?.configured && (
                    <span className="text-[10px] text-yellow-500">Setup erforderlich</span>
                  )}
                </div>

                {/* Email */}
                <div className="p-4 rounded-lg bg-zinc-800/50 border border-white/5">
                  <div className="flex items-center justify-between mb-3">
                    <Label className="text-sm text-white">Email</Label>
                    <Switch
                      checked={formData.email_enabled}
                      onCheckedChange={(checked) => handleChange('email_enabled', checked)}
                    />
                  </div>
                  <p className="text-xs text-zinc-500">
                    Parsed Trading-Signale aus Emails
                  </p>
                  <span className="text-[10px] text-yellow-500">Coming soon</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
