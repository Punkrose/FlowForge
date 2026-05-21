import { TaskStatus } from '../lib/types';

const config: Record<TaskStatus, { bg: string; text: string; dot: string; label: string }> = {
  running:  { bg: 'bg-blue-500/15', text: 'text-blue-400',   dot: 'bg-blue-400',   label: 'Running' },
  done:     { bg: 'bg-emerald-500/15', text: 'text-emerald-400', dot: 'bg-emerald-400', label: 'Done' },
  failed:   { bg: 'bg-red-500/15',  text: 'text-red-400',    dot: 'bg-red-400',    label: 'Failed' },
  blocked:  { bg: 'bg-amber-500/15', text: 'text-amber-400',  dot: 'bg-amber-400',  label: 'Blocked' },
  queued:   { bg: 'bg-zinc-500/15', text: 'text-zinc-400',   dot: 'bg-zinc-400',   label: 'Queued' },
  paused:   { bg: 'bg-violet-500/15', text: 'text-violet-400', dot: 'bg-violet-400', label: 'Paused' },
};

export default function StatusBadge({ status }: { status: TaskStatus }) {
  const c = config[status];
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${c.bg} ${c.text}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${c.dot} ${status === 'running' ? 'animate-pulse' : ''}`} />
      {c.label}
    </span>
  );
}
