import { useEffect, useState } from 'react';
import api from '../lib/api';
import type { AlertSubscription } from '../types';
import { Bell, Plus, Trash2 } from 'lucide-react';

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<AlertSubscription[]>([]);
  const [keywords, setKeywords] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<AlertSubscription[]>('/alerts').then(({ data }) => setAlerts(data)).finally(() => setLoading(false));
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    const kws = keywords.split(',').map((s) => s.trim()).filter(Boolean);
    if (kws.length === 0) return;
    try {
      const { data } = await api.post<AlertSubscription>('/alerts', { keywords: kws });
      setAlerts((prev) => [...prev, data]);
      setKeywords('');
    } catch {
      // error
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await api.delete(`/alerts/${id}`);
      setAlerts((prev) => prev.filter((a) => a.id !== id));
    } catch {
      // error
    }
  };

  if (loading) return <div className="text-center py-16 text-[var(--color-text-muted)]">Loading...</div>;

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-3xl font-bold">Grant Alerts</h1>
      <p className="text-[var(--color-text-muted)]">Subscribe to keywords and receive daily email digests of matching grants.</p>

      <form onSubmit={handleCreate} className="flex gap-3">
        <input type="text" value={keywords} onChange={(e) => setKeywords(e.target.value)}
          placeholder="Enter keywords, separated by commas"
          className="flex-1 px-3 py-2 border border-[var(--color-border)] rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]" />
        <button type="submit" className="flex items-center gap-1 px-4 py-2 bg-[var(--color-primary)] text-white rounded-lg hover:bg-[var(--color-primary-hover)]">
          <Plus className="w-4 h-4" /> Add
        </button>
      </form>

      <div className="space-y-3">
        {alerts.length === 0 ? (
          <div className="text-center py-12">
            <Bell className="w-12 h-12 text-[var(--color-text-muted)] mx-auto mb-4" />
            <p className="text-[var(--color-text-muted)]">No alert subscriptions yet.</p>
          </div>
        ) : (
          alerts.map((alert) => (
            <div key={alert.id} className="bg-white p-4 rounded-lg border border-[var(--color-border)] flex justify-between items-center">
              <div>
                <div className="flex flex-wrap gap-2">
                  {alert.keywords.map((kw) => (
                    <span key={kw} className="px-2 py-1 bg-blue-100 text-[var(--color-primary)] rounded text-sm">{kw}</span>
                  ))}
                </div>
                <span className={`text-xs mt-1 inline-block ${alert.is_active ? 'text-[var(--color-success)]' : 'text-[var(--color-text-muted)]'}`}>
                  {alert.is_active ? 'Active' : 'Paused'}
                </span>
              </div>
              <button onClick={() => handleDelete(alert.id)}
                className="p-2 text-[var(--color-text-muted)] hover:text-[var(--color-danger)] rounded-lg hover:bg-red-50">
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
