import { useEffect, useState } from 'react';
import { Globe, Wifi, WifiOff, Monitor, Smartphone, Cookie, MapPin, MoreVertical } from 'lucide-react';
import { api } from '../lib/api';
import { BrowserProfile } from '../lib/types';

const statusConfig = {
  active: { bg: 'bg-emerald-500/15', text: 'text-emerald-400', dot: 'bg-emerald-400', label: 'Active' },
  idle: { bg: 'bg-zinc-500/15', text: 'text-zinc-400', dot: 'bg-zinc-400', label: 'Idle' },
  error: { bg: 'bg-red-500/15', text: 'text-red-400', dot: 'bg-red-400', label: 'Error' },
};

export default function Profiles() {
  const [profiles, setProfiles] = useState<BrowserProfile[]>([]);

  useEffect(() => {
    api.getProfiles().then(setProfiles);
  }, []);

  const timeAgo = (dateStr: string) => {
    const diff = Date.now() - new Date(dateStr).getTime();
    const hrs = Math.floor(diff / 3600000);
    if (hrs < 1) return 'Just now';
    if (hrs < 24) return `${hrs}h ago`;
    return `${Math.floor(hrs / 24)}d ago`;
  };

  return (
    <div className="animate-fade-in space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Browser Profiles</h1>
        <p className="text-sm text-zinc-500 mt-1">Manage browser configurations and proxy settings</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {profiles.map((profile) => {
          const sc = statusConfig[profile.status];
          const isMobile = profile.viewport.width < 500;
          return (
            <div
              key={profile.id}
              className="bg-surface-card border border-surface-border rounded-xl p-5 hover:border-white/10 transition-all duration-300"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-accent-purple/20 to-accent-blue/20 border border-accent-purple/10 flex items-center justify-center">
                    {isMobile ? (
                      <Smartphone className="w-5 h-5 text-accent-purple" />
                    ) : (
                      <Monitor className="w-5 h-5 text-accent-blue" />
                    )}
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-white">{profile.name}</h3>
                    <p className="text-[10px] text-zinc-500 font-mono mt-0.5">{profile.id}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-medium ${sc.bg} ${sc.text}`}>
                    <span className={`w-1.5 h-1.5 rounded-full ${sc.dot} ${profile.status === 'active' ? 'animate-pulse' : ''}`} />
                    {sc.label}
                  </span>
                  <button className="text-zinc-600 hover:text-zinc-400 transition-colors p-1">
                    <MoreVertical className="w-4 h-4" />
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 mt-3">
                <div className="flex items-center gap-2 text-xs">
                  <Monitor className="w-3.5 h-3.5 text-zinc-500" />
                  <span className="text-zinc-400">{profile.viewport.width}×{profile.viewport.height}</span>
                </div>
                <div className="flex items-center gap-2 text-xs">
                  <Cookie className="w-3.5 h-3.5 text-zinc-500" />
                  <span className="text-zinc-400">{profile.cookies} cookies</span>
                </div>
                {profile.proxy && (
                  <div className="flex items-center gap-2 text-xs col-span-2">
                    <MapPin className="w-3.5 h-3.5 text-zinc-500" />
                    <span className="text-zinc-400 font-mono">{profile.proxy}</span>
                  </div>
                )}
              </div>

              <div className="mt-4 pt-3 border-t border-surface-border flex items-center justify-between">
                <span className="text-[10px] text-zinc-500">
                  Last used: {timeAgo(profile.lastUsed)}
                </span>
                <span className="text-[10px] text-zinc-600 font-mono truncate max-w-[200px]">
                  {profile.userAgent.slice(0, 50)}…
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
