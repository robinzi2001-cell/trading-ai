import React, { useState, useEffect } from 'react';
import { Plus, Trash2, RefreshCw, Radio, ToggleLeft, ToggleRight, AlertCircle, CheckCircle2 } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { toast } from 'sonner';
import { api } from '../App';

export default function TelegramChannelManager() {
  const [channels, setChannels] = useState([]);
  const [newChannel, setNewChannel] = useState('');
  const [channelName, setChannelName] = useState('');
  const [loading, setLoading] = useState(false);
  const [addingChannel, setAddingChannel] = useState(false);
  const [monitorStatus, setMonitorStatus] = useState(null);

  useEffect(() => {
    fetchChannels();
  }, []);

  const fetchChannels = async () => {
    setLoading(true);
    try {
      const [listRes, statusRes] = await Promise.all([
        api.get('/telegram/channels/list'),
        api.get('/telegram/channels/status')
      ]);
      setChannels(listRes.data.channels || []);
      setMonitorStatus(statusRes.data);
    } catch (error) {
      console.error('Error fetching channels:', error);
      toast.error('Fehler beim Laden der Kanäle');
    } finally {
      setLoading(false);
    }
  };

  const handleAddChannel = async (e) => {
    e.preventDefault();
    
    if (!newChannel.trim()) {
      toast.error('Bitte gib einen Kanal-Namen ein');
      return;
    }

    setAddingChannel(true);
    try {
      const response = await api.post('/telegram/channels/add', {
        username: newChannel.trim(),
        name: channelName.trim() || null,
        enabled: true
      });
      
      toast.success(response.data.message || 'Kanal hinzugefügt!');
      setNewChannel('');
      setChannelName('');
      fetchChannels();
    } catch (error) {
      const message = error.response?.data?.detail || 'Fehler beim Hinzufügen';
      toast.error(message);
    } finally {
      setAddingChannel(false);
    }
  };

  const handleRemoveChannel = async (username) => {
    if (!window.confirm(`Kanal @${username} wirklich entfernen?`)) return;

    try {
      await api.delete(`/telegram/channels/${username}`);
      toast.success(`Kanal @${username} entfernt`);
      fetchChannels();
    } catch (error) {
      toast.error('Fehler beim Entfernen');
    }
  };

  const handleToggleChannel = async (username) => {
    try {
      const response = await api.put(`/telegram/channels/${username}/toggle`);
      toast.success(response.data.message);
      fetchChannels();
    } catch (error) {
      toast.error('Fehler beim Umschalten');
    }
  };

  return (
    <Card className="bg-zinc-900/50 border-white/5" data-testid="telegram-channel-manager">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="font-heading text-lg font-semibold tracking-tight uppercase text-white flex items-center gap-2">
              <Radio className="w-4 h-4 text-blue-500" />
              Signal-Kanäle
            </CardTitle>
            <CardDescription className="text-zinc-500">
              Telegram-Kanäle für automatische Signal-Erkennung
            </CardDescription>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={fetchChannels}
            disabled={loading}
            className="h-8 w-8"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Status Banner */}
        {monitorStatus && (
          <div className={`p-3 rounded-lg flex items-center gap-3 ${
            monitorStatus.authorized 
              ? 'bg-emerald-500/10 border border-emerald-500/30' 
              : 'bg-yellow-500/10 border border-yellow-500/30'
          }`}>
            {monitorStatus.authorized ? (
              <CheckCircle2 className="w-5 h-5 text-emerald-500" />
            ) : (
              <AlertCircle className="w-5 h-5 text-yellow-500" />
            )}
            <div className="flex-1">
              <p className={`text-sm font-medium ${monitorStatus.authorized ? 'text-emerald-400' : 'text-yellow-400'}`}>
                {monitorStatus.authorized ? 'Channel Monitor aktiv' : 'Telegram Login erforderlich'}
              </p>
              <p className="text-xs text-zinc-400">
                {monitorStatus.authorized 
                  ? `${monitorStatus.channels?.length || 0} Kanäle werden überwacht`
                  : 'Backend muss einmalig mit Telegram verbunden werden'
                }
              </p>
            </div>
            {monitorStatus.running && (
              <span className="flex items-center gap-1 text-xs text-emerald-400">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                Live
              </span>
            )}
          </div>
        )}

        {/* Add Channel Form */}
        <form onSubmit={handleAddChannel} className="space-y-3">
          <div className="flex gap-2">
            <div className="flex-1">
              <Input
                placeholder="@telegramsignale oder Kanal-Username"
                value={newChannel}
                onChange={(e) => setNewChannel(e.target.value)}
                className="bg-zinc-800 border-white/10"
                data-testid="channel-username-input"
              />
            </div>
            <Button
              type="submit"
              disabled={addingChannel || !newChannel.trim()}
              className="bg-blue-500 hover:bg-blue-600"
              data-testid="add-channel-btn"
            >
              {addingChannel ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <>
                  <Plus className="w-4 h-4 mr-1" />
                  Hinzufügen
                </>
              )}
            </Button>
          </div>
          <Input
            placeholder="Optionaler Anzeigename"
            value={channelName}
            onChange={(e) => setChannelName(e.target.value)}
            className="bg-zinc-800 border-white/10"
            data-testid="channel-name-input"
          />
        </form>

        {/* Channel List */}
        <div className="space-y-2">
          {channels.length === 0 ? (
            <div className="p-6 text-center border border-dashed border-white/10 rounded-lg">
              <Radio className="w-8 h-8 text-zinc-600 mx-auto mb-2" />
              <p className="text-sm text-zinc-500">Keine Kanäle konfiguriert</p>
              <p className="text-xs text-zinc-600 mt-1">
                Füge Telegram-Kanäle hinzu, um Signale automatisch zu empfangen
              </p>
            </div>
          ) : (
            channels.map((channel) => (
              <div 
                key={channel.username} 
                className={`p-3 rounded-lg border flex items-center justify-between transition-all ${
                  channel.enabled 
                    ? 'bg-zinc-800/50 border-white/10' 
                    : 'bg-zinc-900/50 border-white/5 opacity-60'
                }`}
                data-testid={`channel-item-${channel.username}`}
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-white truncate">
                      {channel.name || `@${channel.username}`}
                    </span>
                    {channel.enabled ? (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400">
                        Aktiv
                      </span>
                    ) : (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-zinc-700 text-zinc-400">
                        Deaktiviert
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-zinc-500">@{channel.username}</p>
                  {channel.signals_received > 0 && (
                    <p className="text-[10px] text-zinc-600 mt-1">
                      {channel.signals_received} Signale empfangen
                    </p>
                  )}
                </div>
                <div className="flex items-center gap-1">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleToggleChannel(channel.username)}
                    className="h-8 w-8 text-zinc-400 hover:text-white"
                    data-testid={`toggle-channel-${channel.username}`}
                  >
                    {channel.enabled ? (
                      <ToggleRight className="w-5 h-5 text-emerald-500" />
                    ) : (
                      <ToggleLeft className="w-5 h-5" />
                    )}
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleRemoveChannel(channel.username)}
                    className="h-8 w-8 text-zinc-400 hover:text-red-500"
                    data-testid={`remove-channel-${channel.username}`}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Default Channels Info */}
        {monitorStatus?.default_channels && monitorStatus.default_channels.length > 0 && (
          <div className="pt-3 border-t border-white/5">
            <p className="text-xs text-zinc-500 mb-2">Standard-Kanäle (automatisch überwacht):</p>
            <div className="flex flex-wrap gap-2">
              {monitorStatus.default_channels.map((ch) => (
                <span 
                  key={ch} 
                  className="text-xs px-2 py-1 rounded bg-zinc-800 text-zinc-400"
                >
                  @{ch}
                </span>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
