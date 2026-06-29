import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../lib/api';
import type { Application } from '../types';
import { Plus, FileText } from 'lucide-react';

export default function ApplicationsPage() {
  const [apps, setApps] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<Application[]>('/applications').then(({ data }) => setApps(data)).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-center py-16 text-[var(--color-text-muted)]">Loading...</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Applications</h1>
        <Link to="/grants" className="flex items-center gap-1 px-4 py-2 bg-[var(--color-primary)] text-white rounded-lg hover:bg-[var(--color-primary-hover)]">
          <Plus className="w-4 h-4" /> New Application
        </Link>
      </div>

      {apps.length === 0 ? (
        <div className="text-center py-16">
          <FileText className="w-12 h-12 text-[var(--color-text-muted)] mx-auto mb-4" />
          <p className="text-[var(--color-text-muted)]">No applications yet. Save a grant and start drafting.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {apps.map((app) => (
            <Link key={app.id} to={`/applications/${app.id}`}
              className="bg-white p-5 rounded-xl border border-[var(--color-border)] block hover:shadow-md transition-shadow">
              <div className="flex justify-between items-center">
                <div>
                  <h3 className="font-semibold text-lg">{app.title || 'Untitled Draft'}</h3>
                  <div className="text-sm text-[var(--color-text-muted)] mt-1">
                    Last updated: {new Date(app.updated_at).toLocaleDateString()}
                  </div>
                  {app.content && (
                    <div className="flex gap-2 mt-2">
                      {Object.keys(app.content).map((section) => (
                        <span key={section} className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded">{section}</span>
                      ))}
                    </div>
                  )}
                </div>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${app.status === 'draft' ? 'bg-yellow-100 text-yellow-700' : 'bg-green-100 text-green-700'}`}>
                  {app.status}
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
