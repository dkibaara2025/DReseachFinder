import { useEffect, useState, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import api from '../lib/api';
import type { Application } from '../types';
import { Sparkles, Save, Download } from 'lucide-react';

const SECTIONS = ['background', 'goals', 'methodology', 'outcomes', 'references'] as const;

export default function ApplicationDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [app, setApp] = useState<Application | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [editContent, setEditContent] = useState<Record<string, string>>({});

  useEffect(() => {
    api.get<Application>(`/applications/${id}`).then(({ data }) => {
      setApp(data);
      setEditContent(data.content || {});
    }).finally(() => setLoading(false));
  }, [id]);

  // Auto-save every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      if (app && Object.keys(editContent).length > 0) {
        api.put(`/applications/${id}`, { content: editContent }).catch(() => {});
      }
    }, 30000);
    return () => clearInterval(interval);
  }, [id, app, editContent]);

  const generateSection = async (section: string) => {
    setGenerating(section);
    try {
      const { data } = await api.post(`/applications/${id}/generate`, { section });
      setEditContent((prev) => ({ ...prev, [section]: data.content }));
    } catch {
      // error
    } finally {
      setGenerating(null);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const { data } = await api.put<Application>(`/applications/${id}`, { content: editContent });
      setApp(data);
    } finally {
      setSaving(false);
    }
  };

  const handleExport = async () => {
    try {
      const { data } = await api.get(`/applications/${id}/export`);
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `application-${id}.json`;
      a.click();
    } catch {
      // error
    }
  };

  if (loading) return <div className="text-center py-16 text-[var(--color-text-muted)]">Loading...</div>;
  if (!app) return <div className="text-center py-16 text-[var(--color-danger)]">Application not found</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">{app.title || 'Untitled Draft'}</h1>
        <div className="flex gap-2">
          <button onClick={handleSave} disabled={saving}
            className="flex items-center gap-1 px-4 py-2 border border-[var(--color-border)] rounded-lg hover:bg-gray-50">
            <Save className="w-4 h-4" /> {saving ? 'Saving...' : 'Save'}
          </button>
          <button onClick={handleExport}
            className="flex items-center gap-1 px-4 py-2 bg-[var(--color-primary)] text-white rounded-lg hover:bg-[var(--color-primary-hover)]">
            <Download className="w-4 h-4" /> Export
          </button>
        </div>
      </div>

      <div className="space-y-6">
        {SECTIONS.map((section) => (
          <div key={section} className="bg-white rounded-xl border border-[var(--color-border)] overflow-hidden">
            <div className="flex justify-between items-center p-4 border-b border-[var(--color-border)] bg-gray-50">
              <h3 className="font-semibold capitalize">{section}</h3>
              <button onClick={() => generateSection(section)} disabled={generating === section}
                className="flex items-center gap-1 px-3 py-1 bg-purple-100 text-purple-700 rounded-lg hover:bg-purple-200 disabled:opacity-50 text-sm">
                <Sparkles className="w-3 h-3" />
                {generating === section ? 'Generating...' : 'AI Generate'}
              </button>
            </div>
            <div className="p-4">
              <textarea
                value={editContent[section] || ''}
                onChange={(e) => setEditContent((prev) => ({ ...prev, [section]: e.target.value }))}
                placeholder={`Write the ${section} section...`}
                rows={8}
                className="w-full border border-[var(--color-border)] rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)] resize-y"
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
