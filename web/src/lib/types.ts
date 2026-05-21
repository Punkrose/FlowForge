export type TaskStatus = 'running' | 'done' | 'failed' | 'blocked' | 'queued' | 'paused';

export type StepType = 'navigate' | 'click' | 'type' | 'screenshot' | 'extract' | 'wait' | 'scroll' | 'evaluate';

export interface TaskStep {
  id: string;
  type: StepType;
  description: string;
  status: 'pending' | 'running' | 'done' | 'failed' | 'skipped';
  startedAt?: string;
  completedAt?: string;
  duration?: number;
  screenshot?: string;
  error?: string;
  output?: string;
}

export interface Task {
  id: string;
  name: string;
  description: string;
  status: TaskStatus;
  profile: string;
  url: string;
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
  steps: TaskStep[];
  currentStep?: number;
  tags: string[];
  priority: 'low' | 'medium' | 'high';
}

export interface BrowserProfile {
  id: string;
  name: string;
  userAgent: string;
  viewport: { width: number; height: number };
  proxy?: string;
  cookies: number;
  lastUsed: string;
  status: 'active' | 'idle' | 'error';
}

export interface DashboardStats {
  totalTasks: number;
  runningTasks: number;
  completedTasks: number;
  failedTasks: number;
  successRate: number;
  avgDuration: number;
  activeProfiles: number;
  tasksToday: number;
}

export interface ApiConfig {
  baseUrl: string;
  model: string;
  apiKey: string;
  maxConcurrency: number;
  screenshotQuality: number;
  timeout: number;
  retryCount: number;
}
