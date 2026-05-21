import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Globe, Clock, Tag, User, ExternalLink } from 'lucide-react';
import { api } from '../lib/api';
import { Task } from '../lib/types';
import StatusBadge from '../components/StatusBadge';
import StepTimeline from '../components/StepTimeline';

export default function TaskDetail() {
  const { id } = useParams<{ id: string }>();
  const [task, setTask] = useState<Task | null>(null);

  useEffect(() => {
    if (id) api.getTask(id).then(setTask);
  }, [id]);

  if (!task) {
    return (
      <div className="animate-pulse text-zinc-500 p-8">Loading task…</div>
    );
  }

  const duration = task.completedAt && task.startedAt
    ? ((new Date(task.completedAt).getTime() - new Date(task.startedAt).getTime()) / 1000).toFixed(1)
    : null;

  return (
    <div className="animate-fade-in space-y-6">
      {/* Breadcrumb */}
      <Link
        to="/tasks"
        className="inline-flex items-center gap-2 text-sm text-zinc-400 hover:text-white transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to tasks
      </Link>

      {/* Header */}
      <div className="bg-surface-card border border-surface-border rounded-xl p-6">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-xl font-bold text-white">{task.name}</h1>
              <StatusBadge status={task.status} />
            </div>
            <p className="text-sm text-zinc-400">{task.description}</p>
          </div>
          <span className="text-xs text-zinc-500 font-mono bg-white/5 px-2 py-1 rounded">{task.id}</span>
        </div>

        {/* Meta */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-6 pt-5 border-t border-surface-border">
          <div className="flex items-center gap-2">
            <Globe className="w-4 h-4 text-zinc-500" />
            <div>
              <p className="text-[10px] text-zinc-500 uppercase tracking-wider">URL</p>
              <a href={task.url} target="_blank" rel="noopener noreferrer" className="text-xs text-accent-blue hover:underline flex items-center gap-1">
                {task.url.replace(/^https?:\/\//, '').slice(0, 30)}
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <User className="w-4 h-4 text-zinc-500" />
            <div>
              <p className="text-[10px] text-zinc-500 uppercase tracking-wider">Profile</p>
              <p className="text-xs text-white">{task.profile}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-zinc-500" />
            <div>
              <p className="text-[10px] text-zinc-500 uppercase tracking-wider">Duration</p>
              <p className="text-xs text-white">{duration ? `${duration}s` : '—'}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Tag className="w-4 h-4 text-zinc-500" />
            <div>
              <p className="text-[10px] text-zinc-500 uppercase tracking-wider">Priority</p>
              <p className="text-xs text-white capitalize">{task.priority}</p>
            </div>
          </div>
        </div>

        {task.tags.length > 0 && (
          <div className="flex gap-2 mt-4">
            {task.tags.map((tag) => (
              <span key={tag} className="text-xs text-zinc-400 bg-white/5 px-2.5 py-1 rounded-full border border-surface-border">
                {tag}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Steps */}
      <div className="bg-surface-card border border-surface-border rounded-xl p-6">
        <h2 className="text-lg font-semibold text-white mb-6">Execution Steps</h2>
        <StepTimeline steps={task.steps} />
      </div>

      {/* Logs placeholder */}
      <div className="bg-surface-card border border-surface-border rounded-xl p-6">
        <h2 className="text-lg font-semibold text-white mb-4">Logs</h2>
        <div className="bg-surface rounded-lg border border-surface-border p-4 font-mono text-xs text-zinc-400 space-y-1 max-h-48 overflow-y-auto">
          <p><span className="text-zinc-600">[22:31:00]</span> <span className="text-blue-400">INFO</span> Task {task.id} started</p>
          <p><span className="text-zinc-600">[22:31:00]</span> <span className="text-blue-400">INFO</span> Using profile: {task.profile}</p>
          <p><span className="text-zinc-600">[22:31:01]</span> <span className="text-blue-400">INFO</span> Browser launched</p>
          <p><span className="text-zinc-600">[22:31:02]</span> <span className="text-blue-400">INFO</span> Navigating to {task.url}</p>
          {task.steps.map((step) => (
            <p key={step.id}>
              <span className="text-zinc-600">[—]</span>
              {' '}
              <span className={step.status === 'failed' ? 'text-red-400' : step.status === 'done' ? 'text-emerald-400' : 'text-zinc-500'}>
                {step.status.toUpperCase()}
              </span>
              {' '}{step.description}
              {step.error && <span className="text-red-400"> — {step.error}</span>}
            </p>
          ))}
        </div>
      </div>
    </div>
  );
}
