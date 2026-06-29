import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../lib/api';
import type { UserGrant, Application } from '../types';
import { Clock, FileText, AlertTriangle } from 'lucide-react';

const STATUS_COLORS: Record<string, string> = {
  saved: 'bg-gray-100 text-gray-700',
  applying: 'bg-blue-100 text-blue-700',
  submitted: 'bg-green-100 text-green-700',
  awarded: 'bg-emerald-100 text-emerald-700',
  rejected: 'bg-red-100 text-red-700',
};

export default function DashboardPage() {
  const [grants, setGrants] = useState<UserGrant[]>([]);
  const [apps, setApps] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get<UserGrant[]>('/grants/saved/list'),
      api.get<Application[]>('/applications'),
    ]).then(([gRes, aRes]) => {
      setGrants(gRes.data);
      setApps(aRes.data);
    }).finally(() => setLoading(false));
  }, []);

  const upcomingDeadlines = grants
    .filter((g) => g.grant?.deadline)
    .sort((a, b) => new Date(a.grant!.deadline!).getTime() - new Date(b.grant!.deadline!).getTime())
    .slice(0, 5);

  const daysUntil = (dateStr: string) => {
    const diff = new Date(dateStr).getTime() - Date.now();
    return Math.ceil(diff / (1000 * 60 * 60 * 24));
  };

  if (loading) return <div className="text-center py-16 text-[var(--color-text-muted)]">Loading...</div>;

  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold">Dashboard</h1>

      <div className="grid md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-xl border border-[var(--color-border)]">
          <div className="text-3xl font-bold text-[var(--color-primary)]">{grants.length}</div>
          <div className="text-[var(--color-text-muted)]">Saved Grants</div>
        </div>
        <div className="bg-white p-6 rounded-xl border border-[var(--color-border)]">
          <div className="text-3xl font-bold text-[var(--color-primary)]">{apps.length}</div>
          <div className="text-[var(--color-text-muted)]">Applications</div>
        </div>
        <div className="bg-white p-6 rounded-xl border border-[var(--color-border)]">
          <div className="text-3xl font-bold text-[var(--color-warning)]">{upcomingDeadlines.length}</div>
          <div className="text-[var(--color-text-muted)]">Upcoming Deadlines</div>
        </div>
      </div>

      <section>
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <Clock className="w-5 h-5" /> Upcoming Deadlines
        </h2>
        {upcomingDeadlines.length === 0 ? (
          <p className="text-[var(--color-text-muted)]">No upcoming deadlines. <Link to="/grants" className="text-[var(--color-primary)]">Search for grants</Link></p>
        ) : (
          <div className="space-y-3">
            {upcomingDeadlines.map((ug) => {
              const days = daysUntil(ug.grant!.deadline!);
              return (
                <div key={ug.id} className="bg-white p-4 rounded-lg border border-[var(--color-border)] flex justify-between items-center">
                  <div>
                    <div className="font-medium">{ug.grant?.title}</div>
                    <div className="text-sm text-[var(--color-text-muted)]">{ug.grant?.agency}</div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${STATUS_COLORS[ug.status]}`}>{ug.status}</span>
                    <span className={`text-sm font-medium ${days <= 3 ? 'text-[var(--color-danger)]' : days <= 7 ? 'text-[var(--color-warning)]' : 'text-[var(--color-text-muted)]'}`}>
                      {days <= 0 ? 'Past due' : `${days}d left`}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>

      <section>
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <FileText className="w-5 h-5" /> Recent Applications
        </h2>
        {apps.length === 0 ? (
          <p className="text-[var(--color-text-muted)]">No applications yet.</p>
        ) : (
          <div className="space-y-3">
            {apps.slice(0, 5).map((app) => (
              <Link key={app.id} to={`/applications/${app.id}`}
                className="bg-white p-4 rounded-lg border border-[var(--color-border)] block hover:shadow-md transition-shadow">
                <div className="flex justify-between items-center">
                  <div>
                    <div className="font-medium">{app.title || 'Untitled Draft'}</div>
                    <div className="text-sm text-[var(--color-text-muted)]">
                      Updated {new Date(app.updated_at).toLocaleDateString()}
                    </div>
                  </div>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${app.status === 'draft' ? 'bg-yellow-100 text-yellow-700' : 'bg-green-100 text-green-700'}`}>
                    {app.status}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
