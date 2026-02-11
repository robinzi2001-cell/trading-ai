import React, { useState, useEffect } from 'react';
import { 
  Brain, 
  Zap, 
  Bell, 
  Twitter, 
  TrendingUp, 
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Send,
  RefreshCw,
  ChevronDown
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Switch } from '../components/ui/switch';
import { Slider } from '../components/ui/slider';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { toast } from 'sonner';
import { api } from '../App';
import { cn } from '../lib/utils';

export default function AICenter() {
  const [autoExecuteStatus, setAutoExecuteStatus] = useState(null);
  const [influentialAccounts, setInfluentialAccounts] = useState([]);
  const [tweetText, setTweetText] = useState('');
  const [tweetAuthor, setTweetAuthor] = useState('Donald Trump');
  const [tweetAnalysis, setTweetAnalysis] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [statusRes, accountsRes] = await Promise.all([
        api.get('/auto-execute/status'),
        api.get('/ai/influential-accounts')
      ]);
      setAutoExecuteStatus(statusRes.data);
      setInfluentialAccounts(accountsRes.data.accounts || []);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateAutoExecute = async (updates) => {
    try {
      const params = new URLSearchParams(updates).toString();
      const response = await api.put(`/auto-execute/config?${params}`);
      setAutoExecuteStatus(response.data);
      toast.success('Auto-Execute aktualisiert');
    } catch (error) {
      toast.error('Fehler beim Aktualisieren');
    }
  };

  const analyzeTweet = async () => {
    if (!tweetText.trim()) {
      toast.error('Bitte Tweet-Text eingeben');
      return;
    }

    setAnalyzing(true);
    try {
      const response = await api.post('/ai/analyze-tweet', {
        author: tweetAuthor,
        text: tweetText
      });
      setTweetAnalysis(response.data);
      toast.success('Tweet analysiert');
    } catch (error) {
      toast.error('Analyse fehlgeschlagen');
    } finally {
      setAnalyzing(false);
    }
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
    <div className="p-4 md:p-6 lg:p-8 pb-20 md:pb-8" data-testid="ai-center">
      {/* Header */}
      <div className="glass-header -mx-4 md:-mx-6 lg:-mx-8 -mt-4 md:-mt-6 lg:-mt-8 px-4 md:px-6 lg:px-8 py-4 mb-6 sticky top-0 z-40">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Brain className="w-5 h-5 text-purple-500" />
            <h1 className="font-heading text-xl font-bold tracking-tight uppercase text-white">
              AI Center
            </h1>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Auto-Execute Card */}
        <Card className="bg-zinc-900/50 border-white/5">
          <CardHeader>
            <CardTitle className="font-heading text-lg font-semibold tracking-tight uppercase text-white flex items-center gap-2">
              <Zap className="w-4 h-4 text-yellow-500" />
              Auto-Execute
            </CardTitle>
            <CardDescription className="text-zinc-500">
              Automatische Trade-Ausführung mit AI-Analyse
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Status */}
            <div className={cn(
              "p-4 rounded-lg flex items-center gap-3",
              autoExecuteStatus?.enabled 
                ? "bg-emerald-500/10 border border-emerald-500/30" 
                : "bg-zinc-800/50"
            )}>
              {autoExecuteStatus?.enabled ? (
                <CheckCircle className="w-6 h-6 text-emerald-500" />
              ) : (
                <XCircle className="w-6 h-6 text-zinc-500" />
              )}
              <div>
                <div className="font-medium text-white">
                  {autoExecuteStatus?.enabled ? 'Auto-Execute AKTIV' : 'Auto-Execute DEAKTIVIERT'}
                </div>
                <div className="text-xs text-zinc-400">
                  {autoExecuteStatus?.daily_trades || 0} / {autoExecuteStatus?.max_daily_trades || 10} Trades heute
                </div>
              </div>
              <Switch
                checked={autoExecuteStatus?.enabled}
                onCheckedChange={(checked) => updateAutoExecute({ enabled: checked })}
                className="ml-auto"
              />
            </div>

            {/* Broker Mode */}
            <div className={cn(
              "p-3 rounded-lg flex items-center justify-between",
              autoExecuteStatus?.use_binance 
                ? "bg-yellow-500/10 border border-yellow-500/30" 
                : "bg-zinc-800/50"
            )}>
              <div className="flex items-center gap-2">
                <Zap className={cn("w-4 h-4", autoExecuteStatus?.use_binance ? "text-yellow-500" : "text-zinc-500")} />
                <div>
                  <span className="text-sm font-medium text-white">
                    {autoExecuteStatus?.use_binance ? 'Binance Testnet' : 'Paper Trading'}
                  </span>
                  <p className="text-[10px] text-zinc-500">
                    {autoExecuteStatus?.use_binance ? 'Echte Orders auf Testnet' : 'Simulierte Trades'}
                  </p>
                </div>
              </div>
              <Switch
                checked={autoExecuteStatus?.use_binance || false}
                onCheckedChange={(checked) => updateAutoExecute({ use_binance: checked })}
              />
            </div>

            {/* Settings */}
            <div className="space-y-4">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label className="text-sm text-zinc-400">Min. AI Score</Label>
                  <span className="font-mono text-sm text-white">
                    {autoExecuteStatus?.min_ai_score || 60}
                  </span>
                </div>
                <Slider
                  value={[autoExecuteStatus?.min_ai_score || 60]}
                  onValueChange={([value]) => updateAutoExecute({ min_ai_score: value })}
                  min={30}
                  max={90}
                  step={5}
                />
                <p className="text-[10px] text-zinc-500">
                  Signale unter diesem Score werden nicht ausgeführt
                </p>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label className="text-sm text-zinc-400">Min. Confidence</Label>
                  <span className="font-mono text-sm text-white">
                    {(autoExecuteStatus?.min_confidence || 0.6) * 100}%
                  </span>
                </div>
                <Slider
                  value={[(autoExecuteStatus?.min_confidence || 0.6) * 100]}
                  onValueChange={([value]) => updateAutoExecute({ min_confidence: value / 100 })}
                  min={40}
                  max={90}
                  step={5}
                />
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label className="text-sm text-zinc-400">Max. Trades/Tag</Label>
                  <span className="font-mono text-sm text-white">
                    {autoExecuteStatus?.max_daily_trades || 10}
                  </span>
                </div>
                <Slider
                  value={[autoExecuteStatus?.max_daily_trades || 10]}
                  onValueChange={([value]) => updateAutoExecute({ max_daily_trades: value })}
                  min={1}
                  max={50}
                  step={1}
                />
              </div>

              <div className="flex items-center justify-between pt-2">
                <div>
                  <Label className="text-sm text-white">AI Approval erforderlich</Label>
                  <p className="text-xs text-zinc-500">AI muss Signal genehmigen</p>
                </div>
                <Switch
                  checked={autoExecuteStatus?.require_ai_approval}
                  onCheckedChange={(checked) => updateAutoExecute({ require_ai_approval: checked })}
                />
              </div>
            </div>

            {/* AI Status */}
            <div className="flex items-center gap-2 p-3 rounded-lg bg-zinc-800/50">
              <Brain className="w-4 h-4 text-purple-500" />
              <span className="text-sm text-zinc-400">AI Analyzer:</span>
              <span className={cn(
                "text-sm font-medium",
                autoExecuteStatus?.ai_analyzer_available ? "text-emerald-500" : "text-red-500"
              )}>
                {autoExecuteStatus?.ai_analyzer_available ? 'Verfügbar' : 'Nicht verfügbar'}
              </span>
            </div>
          </CardContent>
        </Card>

        {/* Tweet Analysis Card */}
        <Card className="bg-zinc-900/50 border-white/5">
          <CardHeader>
            <CardTitle className="font-heading text-lg font-semibold tracking-tight uppercase text-white flex items-center gap-2">
              <Twitter className="w-4 h-4 text-blue-400" />
              X/Twitter Analyse
            </CardTitle>
            <CardDescription className="text-zinc-500">
              Analysiere Posts von Trump, Elon Musk & Co.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label className="text-sm text-zinc-400">Autor</Label>
              <Select value={tweetAuthor} onValueChange={setTweetAuthor}>
                <SelectTrigger className="w-full bg-zinc-800 border-white/10">
                  <SelectValue placeholder="Autor auswählen" />
                </SelectTrigger>
                <SelectContent className="bg-zinc-900 border-white/10">
                  {influentialAccounts.map(acc => (
                    <SelectItem key={acc.username} value={acc.name} className="text-white hover:bg-zinc-800">
                      {acc.name} (@{acc.username})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label className="text-sm text-zinc-400">Tweet/Post Text</Label>
              <Textarea
                value={tweetText}
                onChange={(e) => setTweetText(e.target.value)}
                placeholder="Füge hier den Tweet-Text ein..."
                className="bg-zinc-800 border-white/10 min-h-[100px]"
              />
            </div>

            <Button
              onClick={analyzeTweet}
              disabled={analyzing}
              className="w-full bg-blue-500 hover:bg-blue-600"
            >
              {analyzing ? (
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Brain className="w-4 h-4 mr-2" />
              )}
              Analysieren
            </Button>

            {/* Analysis Result */}
            {tweetAnalysis && (
              <div className="space-y-3 p-4 rounded-lg bg-zinc-800/50 border border-white/5">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-zinc-400">Impact Score</span>
                  <span className={cn(
                    "font-mono text-lg font-bold",
                    (tweetAnalysis.ai_analysis?.impact_score || 0) > 0 ? "text-emerald-500" : 
                    (tweetAnalysis.ai_analysis?.impact_score || 0) < 0 ? "text-red-500" : "text-zinc-400"
                  )}>
                    {tweetAnalysis.ai_analysis?.impact_score > 0 ? '+' : ''}
                    {tweetAnalysis.ai_analysis?.impact_score || 0}
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-sm text-zinc-400">Sentiment</span>
                  <span className={cn(
                    "text-sm font-medium px-2 py-1 rounded",
                    tweetAnalysis.ai_analysis?.sentiment === 'bullish' && "bg-emerald-500/20 text-emerald-500",
                    tweetAnalysis.ai_analysis?.sentiment === 'bearish' && "bg-red-500/20 text-red-500",
                    tweetAnalysis.ai_analysis?.sentiment === 'neutral' && "bg-zinc-700 text-zinc-400"
                  )}>
                    {(tweetAnalysis.ai_analysis?.sentiment || 'neutral').toUpperCase()}
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-sm text-zinc-400">Empfehlung</span>
                  <span className={cn(
                    "text-sm font-medium px-2 py-1 rounded",
                    tweetAnalysis.ai_analysis?.suggested_action === 'long' && "bg-emerald-500/20 text-emerald-500",
                    tweetAnalysis.ai_analysis?.suggested_action === 'short' && "bg-red-500/20 text-red-500",
                    tweetAnalysis.ai_analysis?.suggested_action === 'wait' && "bg-yellow-500/20 text-yellow-500"
                  )}>
                    {(tweetAnalysis.ai_analysis?.suggested_action || 'wait').toUpperCase()}
                  </span>
                </div>

                {tweetAnalysis.ai_analysis?.affected_assets?.length > 0 && (
                  <div>
                    <span className="text-sm text-zinc-400 block mb-1">Betroffene Assets</span>
                    <div className="flex flex-wrap gap-1">
                      {tweetAnalysis.ai_analysis.affected_assets.map(asset => (
                        <span key={asset} className="text-xs px-2 py-1 rounded bg-zinc-700 text-white">
                          {asset}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {tweetAnalysis.ai_analysis?.reasoning && (
                  <div>
                    <span className="text-sm text-zinc-400 block mb-1">Analyse</span>
                    <p className="text-xs text-zinc-300">
                      {tweetAnalysis.ai_analysis.reasoning}
                    </p>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Influential Accounts */}
        <Card className="bg-zinc-900/50 border-white/5 lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-sm text-zinc-400 uppercase tracking-wide">
              Überwachte Accounts
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
              {influentialAccounts.map(acc => (
                <div 
                  key={acc.username}
                  className="p-3 rounded-lg bg-zinc-800/50 border border-white/5"
                >
                  <div className="font-medium text-white text-sm">{acc.name}</div>
                  <div className="text-xs text-zinc-500">@{acc.username}</div>
                  <div className="flex items-center gap-1 mt-2">
                    <span className={cn(
                      "text-[10px] px-1.5 py-0.5 rounded",
                      acc.category === 'crypto' && "bg-purple-500/20 text-purple-400",
                      acc.category === 'politics' && "bg-blue-500/20 text-blue-400",
                      acc.category === 'business' && "bg-emerald-500/20 text-emerald-400"
                    )}>
                      {acc.category}
                    </span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-zinc-700 text-zinc-400">
                      {acc.impact_weight}x
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
