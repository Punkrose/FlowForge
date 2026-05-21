import { TaskStep } from '../lib/types';
import { Globe, MousePointer2, Type, Camera, Download, Clock, ChevronDown, Play, CheckCircle2, XCircle, SkipForward } from 'lucide-react';

const stepIcons: Record<string, typeof Globe> = {
  navigate: Globe,
  click: MousePointer2,
  type: Type,
  screenshot: Camera,
  extract: Download,
  wait: Clock,
  scroll: ChevronDown,
  evaluate: Play,
};

const statusIcons = {
  pending: SkipForward,
  running: Play,
  done: CheckCircle2,
  failed: XCircle,
  skipped: SkipForward,
};

const statusColors: Record<string, string> = {
  pending: 'text-zinc-500 bg-zinc-500/10 border-zinc-500/20',
  running: 'text-blue-400 bg-blue-500/10 border-blue-500/20 animate-pulse',
  done: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
  failed: 'text-red-400 bg-red-500/10 border-red-500/20',
  skipped: 'text-zinc-500 bg-zinc-500/10 border-zinc-500/20',
};

const lineColors: Record<string, string> = {
  pending: 'bg-zinc-700',
  running: 'bg-gradient-to-b from-blue-500 to-blue-500/30',
  done: 'bg-emerald-500/50',
  failed: 'bg-red-500/50',
  skipped: 'bg-zinc-700',
};

export default function StepTimeline({ steps }: { steps: TaskStep[] }) {
  return (
    <div className="space-y-0">
      {steps.map((step, i) => {
        const Icon = stepIcons[step.type] ?? Play;
        const StatusIcon = statusIcons[step.status] ?? Play;
        const isLast = i === steps.length - 1;

        return (
          <div key={step.id} className="flex gap-4 animate-fade-in" style={{ animationDelay: `${i * 80}ms` }}>
            {/* Timeline line + node */}
            <div className="flex flex-col items-center">
              <div className={`w-10 h-10 rounded-xl border flex items-center justify-center flex-shrink-0 ${statusColors[step.status]}`}>
                <Icon className="w-4 h-4" />
              </div>
              {!isLast && (
                <div className={`w-0.5 flex-1 min-h-[40px] ${lineColors[step.status]}`} />
              )}
            </div>

            {/* Content */}
            <div className="pb-6 pt-1 flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-white">{step.description}</span>
                <StatusIcon className={`w-3.5 h-3.5 ${
                  step.status === 'done' ? 'text-emerald-400' :
                  step.status === 'failed' ? 'text-red-400' :
                  step.status === 'running' ? 'text-blue-400' : 'text-zinc-500'
                }`} />
              </div>
              <div className="flex items-center gap-3 mt-1">
                <span className="text-[10px] uppercase tracking-wider text-zinc-500 font-mono">{step.type}</span>
                {step.duration && (
                  <span className="text-[10px] text-zinc-500">{step.duration}s</span>
                )}
              </div>
              {step.error && (
                <div className="mt-2 text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
                  {step.error}
                </div>
              )}
              {step.output && (
                <div className="mt-2 text-xs text-zinc-400 bg-white/5 border border-surface-border rounded-lg px-3 py-2 font-mono">
                  {step.output}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
