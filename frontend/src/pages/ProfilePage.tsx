import { useEffect, useState } from 'react';
import api from '../lib/api';
import { useAuthStore } from '../stores/authStore';
import type { UserProfile } from '../types';
import { RefreshCw } from 'lucide-react';

export default function ProfilePage() {
  const { user, updateUser } = useAuthStore();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [name, setName] = useState(user?.name || '');
  const [institution, setInstitution] = useState(user?.institution || '');
  const [scholarUrl, setScholarUrl] = useState(user?.scholar_profile_url || '');
  const [orcid, setOrcid] = useState('');
  const [interests, setInterests] = useState('');
  const [cvText, setCvText] = useState('');
  const [saving, setSaving] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    api.get<UserProfile>('/profile/extended').then(({ data }) => {
      setProfile(data);
      setOrcid(data.orcid || '');
      setInterests(data.research_interests?.join(', ') || '');
      setCvText(data.cv_text || '');
    }).catch(() => {});
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setMessage('');
    try {
      const { data } = await api.put('/profile', {
        name, institution,
        scholar_profile_url: scholarUrl,
        orcid,
        research_interests: interests.split(',').map((s) => s.trim()).filter(Boolean),
        cv_text: cvText,
      });
      updateUser(data);
      setMessage('Profile updated');
    } catch {
      setMessage('Update failed');
    } finally {
      setSaving(false);
    }
  };

  const handleScholarSync = async () => {
    setSyncing(true);
    try {
      await api.post('/profile/sync-scholar');
      const { data } = await api.get<UserProfile>('/profile/extended');
      setProfile(data);
      setMessage('Scholar profile synced');
    } catch {
      setMessage('Sync failed');
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-3xl font-bold">Profile</h1>

      {message && <div className="bg-blue-50 text-[var(--color-primary)] p-3 rounded-lg text-sm">{message}</div>}

      <form onSubmit={handleSave} className="bg-white p-6 rounded-xl border border-[var(--color-border)] space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">Name</label>
          <input type="text" value={name} onChange={(e) => setName(e.target.value)}
            className="w-full px-3 py-2 border border-[var(--color-border)] rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]" />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Institution</label>
          <input type="text" value={institution} onChange={(e) => setInstitution(e.target.value)}
            className="w-full px-3 py-2 border border-[var(--color-border)] rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]" />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">ORCID</label>
          <input type="text" value={orcid} onChange={(e) => setOrcid(e.target.value)} placeholder="0000-0000-0000-0000"
            className="w-full px-3 py-2 border border-[var(--color-border)] rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]" />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Google Scholar Profile URL</label>
          <div className="flex gap-2">
            <input type="url" value={scholarUrl} onChange={(e) => setScholarUrl(e.target.value)}
              placeholder="https://scholar.google.com/citations?user=..."
              className="flex-1 px-3 py-2 border border-[var(--color-border)] rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]" />
            <button type="button" onClick={handleScholarSync} disabled={syncing || !scholarUrl}
              className="flex items-center gap-1 px-3 py-2 border border-[var(--color-border)] rounded-lg hover:bg-gray-50 disabled:opacity-50">
              <RefreshCw className={`w-4 h-4 ${syncing ? 'animate-spin' : ''}`} /> Sync
            </button>
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Research Interests (comma-separated)</label>
          <input type="text" value={interests} onChange={(e) => setInterests(e.target.value)}
            placeholder="machine learning, natural language processing"
            className="w-full px-3 py-2 border border-[var(--color-border)] rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]" />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">CV / Bio (plain text)</label>
          <textarea value={cvText} onChange={(e) => setCvText(e.target.value)} rows={5}
            className="w-full px-3 py-2 border border-[var(--color-border)] rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)] resize-y" />
        </div>
        <button type="submit" disabled={saving}
          className="w-full py-2 bg-[var(--color-primary)] text-white rounded-lg hover:bg-[var(--color-primary-hover)] disabled:opacity-50">
          {saving ? 'Saving...' : 'Save Profile'}
        </button>
      </form>

      {profile && (profile.h_index || profile.citation_count) && (
        <div className="bg-white p-6 rounded-xl border border-[var(--color-border)]">
          <h2 className="font-semibold text-lg mb-3">Scholar Stats</h2>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-[var(--color-primary)]">{profile.h_index ?? '-'}</div>
              <div className="text-sm text-[var(--color-text-muted)]">h-index</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-[var(--color-primary)]">{profile.citation_count ?? '-'}</div>
              <div className="text-sm text-[var(--color-text-muted)]">Citations</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-[var(--color-primary)]">
                {Array.isArray(profile.publications) ? profile.publications.length : '-'}
              </div>
              <div className="text-sm text-[var(--color-text-muted)]">Publications</div>
            </div>
          </div>
          {profile.last_synced_at && (
            <div className="text-xs text-[var(--color-text-muted)] mt-3">
              Last synced: {new Date(profile.last_synced_at).toLocaleString()}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
