import { Link } from 'react-router-dom';
import { Clock, ArrowRight } from 'lucide-react';
import { Task } from '../lib/types';
import StatusBadge from './StatusBadge';

export default function TaskCard({ task }: { task: Task }) {
  const timeAgo = (dateStr: string) => {
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    return `${Math.floor(hrs / 24)}d ago`;
  };

  return (
    <Link
      to={`/tasks/${task.id}`}
      className="group block bg-surface-card border border-surface-border rounded-xl p-4 hover:border-accent-purple/30 hover:shadow-lg hover:shadow-accent-purple/5 transition-all duration-300"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold text-white truncate group-hover:text-accent-purple transition-colors">
            {task.name}
          </h3>
          <p className="text-xs text-zinc-500 mt-0.5 truncate">{task.description}</p>
        </div>
        <ArrowRight className="w-4 h-4 text-zinc-600 group-hover:text-accent-purple transition-all group-hover:translate-x-0.5 ml-3 flex-shrink-0 mt-0.5" />
      </div>

      <div className="flex items-center justify-between mt-4">
        <div className="flex items-center gap-3">
          <StatusBadge status={task.status} />
          {task.priority === 'high' && (
            <span className="text-[10px] uppercase tracking-wider font-semibold text-red-400 bg-red-500/10 px-1.5 py-0.5 rounded">
              high
            </span>
          )}
        </div>
        <div className="flex items-center gap-1.5 text-zinc-500">
          <Clock className="w-3 h-3" />
          <span className="text-xs">{timeAgo(task.createdAt)}</span>
        </div>
      </div>

      {task.tags.length > 0 && (
        <div className="flex gap-1.5 mt-3">
          {task.tags.map((tag) => (
            <span key={tag} className="text-[10px] text-zinc-500 bg-white/5 px-2 py-0.5 rounded-full">
              {tag}
            </span>
          ))}
        </div>
      )}
    </Link>
  );
}
