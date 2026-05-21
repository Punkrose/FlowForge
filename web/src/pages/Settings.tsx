import { useEffect, useState } from 'react';
import { Save, Key, Server, Cpu, Camera, Clock, RotateCcw, CheckCircle2 } from 'lucide-react';
import { api } from '../lib/api';
import { ApiConfig } from '../lib/types';

export default function Settings() {
  const [config, setConfig] = useState<ApiConfig | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    api.getConfig().then(setConfig);
  }, []);

  const handleSave = async () => {
    if (config) {
      await api.saveConfig(config);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    }
  };

  if (!config) return <div className="animate-pulse text-zinc-500 p-8">Loading settings…</div>;

  const update = (key: keyof ApiConfig, value: string | number) => {
    setConfig((prev) => prev ? { ...prev, [key]: value } : prev);
  };

  const sections = [
    {
      title: 'API Connection',
      icon: Server,
      fields: [
        { key: 'baseUrl' as const, label: 'API Base URL', type: 'text', placeholder: 'http://localhost:8080' },
        { key: 'apiKey' as const, label: 'API Key', type: 'password', placeholder: 'sk-...' },
      ],
    },
    {
      title: 'AI Model',
      icon: Cpu,
      fields: [
        { key: 'model' as const, label: 'Model', type: 'text', placeholder: 'gpt-4o' },
      ],
    },
    {
      title: 'Execution',
      icon: Clock,
      fields: [
        { key: 'maxConcurrency' as const, label: 'Max Concurrency', type: 'number', placeholder: '5' },
        { key: 'timeout' as const, label: 'Timeout (seconds)', type: 'number', placeholder: '30' },
        { key: 'retryCount' as const, label: 'Retry Count', type: 'number', placeholder: '3' },
      ],
    },
    {
      title: 'Screenshots',
      icon: Camera,
      fields: [
        { key: 'screenshotQuality' as const, label: 'Quality (1-100)', type: 'number', placeholder: '80' },
      ],
    },
  ];

  return (
    <div className="animate-fade-in space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-white">Settings</h1>
        <p className="text-sm text-zinc-500 mt-1">Configure API connection and execution parameters</p>
      </div>

      {sections.map(({ title, icon: Icon, fields }) => (
        <div key={title} className="bg-surface-card border border-surface-border rounded-xl p-6">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center">
              <Icon className="w-4 h-4 text-accent-purple" />
            </div>
            <h2 className="text-sm font-semibold text-white">{title}</h2>
          </div>

          <div className="space-y-4">
            {fields.map(({ key, label, type, placeholder }) => (
              <div key={key}>
                <label className="block text-xs font-medium text-zinc-400 mb-1.5">{label}</label>
                <input
                  type={type}
                  value={config[key] ?? ''}
                  onChange={(e) => update(key, type === 'number' ? Number(e.target.value) : e.target.value)}
                  placeholder={placeholder}
                  className="w-full bg-surface-elevated border border-surface-border rounded-lg px-3 py-2.5 text-sm text-white placeholder-zinc-600 focus:outline-none focus:border-accent-purple/50 focus:ring-1 focus:ring-accent-purple/20 transition-all font-mono"
                />
              </div>
            ))}
          </div>
        </div>
      ))}

      {/* Save */}
      <div className="flex items-center gap-3">
        <button
          onClick={handleSave}
          className="flex items-center gap-2 px-5 py-2.5 text-sm font-medium text-white bg-gradient-to-r from-accent-purple to-accent-blue rounded-lg hover:opacity-90 transition-opacity shadow-lg shadow-accent-purple/20"
        >
          {saved ? (
            <>
              <CheckCircle2 className="w-4 h-4" />
              Saved
            </>
          ) : (
            <>
              <Save className="w-4 h-4" />
              Save Settings
            </>
          )}
        </button>
        <button
          onClick={() => api.getConfig().then(setConfig)}
          className="flex items-center gap-2 px-4 py-2.5 text-sm text-zinc-400 hover:text-white border border-surface-border rounded-lg hover:bg-white/5 transition-all"
        >
          <RotateCcw className="w-4 h-4" />
          Reset
        </button>
      </div>
    </div>
  );
}
