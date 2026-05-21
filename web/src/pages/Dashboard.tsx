import { useEffect, useState } from 'react';
import { Activity, CheckCircle2, XCircle, PlayCircle, Globe, TrendingUp, Clock, BarChart3 } from 'lucide-react';
import { api } from '../lib/api';
import { DashboardStats, Task } from '../lib/types';
import TaskCard from '../components/TaskCard';

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);

  useEffect(() => {
    api.getStats().then(setStats);
    api.getTasks().then((t) => setTasks(t.slice(0, 4)));
  }, []);

  if (!stats) return <div className="animate-pulse text-zinc-500 p-8">Loading dashboard…</div>;

  const statCards = [
    { label: 'Total Tasks', value: stats.totalTasks, icon: BarChart3, color: 'from-accent-purple to-accent-blue' },
    { label: 'Running', value: stats.runningTasks, icon: PlayCircle, color: 'from-blue-500 to-cyan-500' },
    { label: 'Completed', value: stats.completedTasks, icon: CheckCircle2, color: 'from-emerald-500 to-teal-500' },
    { label: 'Failed', value: stats.failedTasks, icon: XCircle, color: 'from-red-500 to-orange-500' },
    { label: 'Success Rate', value: `${stats.successRate}%`, icon: TrendingUp, color: 'from-emerald-400 to-green-500' },
    { label: 'Avg Duration', value: `${stats.avgDuration}s`, icon: Clock, color: 'from-violet-500 to-purple-500' },
    { label: 'Active Profiles', value: stats.activeProfiles, icon: Globe, color: 'from-amber-500 to-yellow-500' },
    { label: 'Today', value: stats.tasksToday, icon: Activity, color: 'from-pink-500 to-rose-500' },
  ];

  return (
    <div className="animate-fade-in space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Dashboard</h1>
        <p className="text-sm text-zinc-500 mt-1">Overview of your browser automation tasks</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map(({ label, value, icon: Icon, color }) => (
          <div
            key={label}
            className="bg-surface-card border border-surface-border rounded-xl p-4 hover:border-white/10 transition-all duration-300 group"
          >
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-medium text-zinc-500 uppercase tracking-wider">{label}</span>
              <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${color} bg-opacity-10 flex items-center justify-center opacity-60 group-hover:opacity-100 transition-opacity`}>
                <Icon className="w-4 h-4 text-white" />
              </div>
            </div>
            <div className="text-2xl font-bold text-white">{value}</div>
          </div>
        ))}
      </div>

      {/* Recent Tasks */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-white">Recent Tasks</h2>
          <a href="/tasks" className="text-xs text-accent-purple hover:text-accent-blue transition-colors">
            View all →
          </a>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {tasks.map((task) => (
            <TaskCard key={task.id} task={task} />
          ))}
        </div>
      </div>

      {/* Activity Chart Placeholder */}
      <div className="bg-surface-card border border-surface-border rounded-xl p-6">
        <h3 className="text-sm font-semibold text-white mb-4">Task Activity (7 days)</h3>
        <div className="flex items-end gap-2 h-32">
          {[3, 7, 5, 12, 8, 15, 12].map((val, i) => (
            <div key={i} className="flex-1 flex flex-col items-center gap-1">
              <div
                className="w-full rounded-t-md bg-gradient-to-t from-accent-purple/60 to-accent-blue/40 transition-all duration-500 hover:from-accent-purple hover:to-accent-blue"
                style={{ height: `${(val / 15) * 100}%` }}
              />
              <span className="text-[10px] text-zinc-500">
                {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][i]}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
