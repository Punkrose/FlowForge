import { Task, BrowserProfile, DashboardStats, ApiConfig } from './types';

const API_BASE = '/api';

async function fetchJson<T>(url: string): Promise<T> {
  try {
    const res = await fetch(`${API_BASE}${url}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch {
    return null as unknown as T;
  }
}

// ─── Mock Data ───────────────────────────────────────────────────────────────

const mockTasks: Task[] = [
  {
    id: 'tsk_001',
    name: 'Scrape product listings',
    description: 'Navigate to e-commerce site and extract all product details from the catalog page',
    status: 'running',
    profile: 'Chrome - US',
    url: 'https://example-shop.com/catalog',
    createdAt: '2026-05-21T22:30:00Z',
    startedAt: '2026-05-21T22:31:00Z',
    currentStep: 2,
    tags: ['scraping', 'e-commerce'],
    priority: 'high',
    steps: [
      { id: 's1', type: 'navigate', description: 'Navigate to catalog page', status: 'done', startedAt: '2026-05-21T22:31:00Z', completedAt: '2026-05-21T22:31:03Z', duration: 3 },
      { id: 's2', type: 'wait', description: 'Wait for products to load', status: 'done', startedAt: '2026-05-21T22:31:03Z', completedAt: '2026-05-21T22:31:05Z', duration: 2 },
      { id: 's3', type: 'screenshot', description: 'Capture product grid', status: 'running', startedAt: '2026-05-21T22:31:05Z' },
      { id: 's4', type: 'extract', description: 'Extract product data', status: 'pending' },
      { id: 's5', type: 'click', description: 'Click next page', status: 'pending' },
    ],
  },
  {
    id: 'tsk_002',
    name: 'Login flow test',
    description: 'Test the authentication flow with multiple credential sets',
    status: 'done',
    profile: 'Firefox - EU',
    url: 'https://app.example.com/login',
    createdAt: '2026-05-21T20:00:00Z',
    startedAt: '2026-05-21T20:01:00Z',
    completedAt: '2026-05-21T20:03:45Z',
    tags: ['testing', 'auth'],
    priority: 'medium',
    steps: [
      { id: 's1', type: 'navigate', description: 'Navigate to login page', status: 'done', startedAt: '2026-05-21T20:01:00Z', completedAt: '2026-05-21T20:01:02Z', duration: 2 },
      { id: 's2', type: 'type', description: 'Enter credentials', status: 'done', startedAt: '2026-05-21T20:01:02Z', completedAt: '2026-05-21T20:01:05Z', duration: 3 },
      { id: 's3', type: 'click', description: 'Click login button', status: 'done', startedAt: '2026-05-21T20:01:05Z', completedAt: '2026-05-21T20:01:06Z', duration: 1 },
      { id: 's4', type: 'screenshot', description: 'Capture dashboard', status: 'done', startedAt: '2026-05-21T20:01:06Z', completedAt: '2026-05-21T20:01:07Z', duration: 1 },
    ],
  },
  {
    id: 'tsk_003',
    name: 'Price monitoring',
    description: 'Monitor competitor pricing across 50 product pages',
    status: 'failed',
    profile: 'Chrome - US',
    url: 'https://competitor.com/prices',
    createdAt: '2026-05-21T18:00:00Z',
    startedAt: '2026-05-21T18:01:00Z',
    completedAt: '2026-05-21T18:05:00Z',
    tags: ['monitoring', 'pricing'],
    priority: 'high',
    steps: [
      { id: 's1', type: 'navigate', description: 'Navigate to price page', status: 'done', duration: 2 },
      { id: 's2', type: 'evaluate', description: 'Check for CAPTCHA', status: 'done', duration: 1 },
      { id: 's3', type: 'extract', description: 'Extract pricing data', status: 'failed', error: 'CAPTCHA detected — blocked by anti-bot system' },
    ],
  },
  {
    id: 'tsk_004',
    name: 'Form submission test',
    description: 'Fill and submit contact form with test data',
    status: 'queued',
    profile: 'Chrome - APAC',
    url: 'https://example.com/contact',
    createdAt: '2026-05-21T23:00:00Z',
    tags: ['testing', 'forms'],
    priority: 'low',
    steps: [
      { id: 's1', type: 'navigate', description: 'Navigate to contact page', status: 'pending' },
      { id: 's2', type: 'type', description: 'Fill form fields', status: 'pending' },
      { id: 's3', type: 'click', description: 'Submit form', status: 'pending' },
    ],
  },
  {
    id: 'tsk_005',
    name: 'Screenshot gallery build',
    description: 'Capture screenshots of 20 landing pages for design reference',
    status: 'done',
    profile: 'Firefox - US',
    url: 'https://gallery.example.com',
    createdAt: '2026-05-20T14:00:00Z',
    startedAt: '2026-05-20T14:01:00Z',
    completedAt: '2026-05-20T14:15:00Z',
    tags: ['screenshots', 'design'],
    priority: 'medium',
    steps: [
      { id: 's1', type: 'navigate', description: 'Navigate to first page', status: 'done', duration: 2 },
      { id: 's2', type: 'screenshot', description: 'Capture full page', status: 'done', duration: 4 },
      { id: 's3', type: 'scroll', description: 'Scroll to footer', status: 'done', duration: 2 },
      { id: 's4', type: 'screenshot', description: 'Capture footer section', status: 'done', duration: 3 },
    ],
  },
  {
    id: 'tsk_006',
    name: 'Blocked by CAPTCHA',
    description: 'Attempt to access gated content behind CAPTCHA verification',
    status: 'blocked',
    profile: 'Chrome - EU',
    url: 'https://secure-site.com/gated',
    createdAt: '2026-05-21T16:00:00Z',
    startedAt: '2026-05-21T16:01:00Z',
    tags: ['scraping', 'blocked'],
    priority: 'medium',
    steps: [
      { id: 's1', type: 'navigate', description: 'Navigate to gated page', status: 'done', duration: 3 },
      { id: 's2', type: 'screenshot', description: 'Capture CAPTCHA challenge', status: 'done', duration: 1 },
      { id: 's3', type: 'evaluate', description: 'Attempt CAPTCHA solve', status: 'failed', error: 'reCAPTCHA v3 detected — requires human interaction' },
    ],
  },
];

const mockProfiles: BrowserProfile[] = [
  { id: 'prof_001', name: 'Chrome - US', userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', viewport: { width: 1920, height: 1080 }, cookies: 24, lastUsed: '2026-05-21T22:31:00Z', status: 'active' },
  { id: 'prof_002', name: 'Firefox - EU', userAgent: 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/109.0', viewport: { width: 1366, height: 768 }, proxy: 'eu-proxy.flowforge.io:8080', cookies: 12, lastUsed: '2026-05-21T20:01:00Z', status: 'idle' },
  { id: 'prof_003', name: 'Chrome - APAC', userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36', viewport: { width: 1440, height: 900 }, proxy: 'apac-proxy.flowforge.io:8080', cookies: 8, lastUsed: '2026-05-21T12:00:00Z', status: 'idle' },
  { id: 'prof_004', name: 'Safari - Mobile', userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15', viewport: { width: 390, height: 844 }, cookies: 5, lastUsed: '2026-05-19T10:00:00Z', status: 'idle' },
  { id: 'prof_005', name: 'Chrome - EU', userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', viewport: { width: 1920, height: 1080 }, proxy: 'eu-proxy.flowforge.io:8080', cookies: 31, lastUsed: '2026-05-21T16:01:00Z', status: 'error' },
];

const mockStats: DashboardStats = {
  totalTasks: 142,
  runningTasks: 3,
  completedTasks: 128,
  failedTasks: 8,
  successRate: 94.1,
  avgDuration: 4.2,
  activeProfiles: 4,
  tasksToday: 12,
};

// ─── Public API ──────────────────────────────────────────────────────────────

export const api = {
  async getStats(): Promise<DashboardStats> {
    const data = await fetchJson<DashboardStats>('/stats');
    return data ?? mockStats;
  },

  async getTasks(): Promise<Task[]> {
    const data = await fetchJson<Task[]>('/tasks');
    return data ?? mockTasks;
  },

  async getTask(id: string): Promise<Task | null> {
    const data = await fetchJson<Task>(`/tasks/${id}`);
    return data ?? mockTasks.find((t) => t.id === id) ?? null;
  },

  async createTask(input: Partial<Task>): Promise<Task> {
    try {
      const res = await fetch(`${API_BASE}/tasks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(input),
      });
      if (res.ok) return await res.json();
    } catch { /* fall through */ }
    // mock response
    return {
      id: `tsk_${Date.now()}`,
      name: input.name ?? 'Untitled task',
      description: input.description ?? '',
      status: 'queued',
      profile: input.profile ?? 'Chrome - US',
      url: input.url ?? '',
      createdAt: new Date().toISOString(),
      tags: input.tags ?? [],
      priority: input.priority ?? 'medium',
      steps: [],
    };
  },

  async getProfiles(): Promise<BrowserProfile[]> {
    const data = await fetchJson<BrowserProfile[]>('/profiles');
    return data ?? mockProfiles;
  },

  async getConfig(): Promise<ApiConfig> {
    const data = await fetchJson<ApiConfig>('/config');
    return data ?? {
      baseUrl: 'http://localhost:8080',
      model: 'gpt-4o',
      apiKey: '',
      maxConcurrency: 5,
      screenshotQuality: 80,
      timeout: 30,
      retryCount: 3,
    };
  },

  async saveConfig(config: ApiConfig): Promise<void> {
    try {
      await fetch(`${API_BASE}/config`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });
    } catch { /* ignore */ }
  },
};
