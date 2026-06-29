import { useState } from 'react';
import api from '../lib/api';
import type { Grant } from '../types';
import { Search, ExternalLink, Bookmark } from 'lucide-react';

export default function GrantsPage() {
  const [keyword, setKeyword] = useState('');
  const [source, setSource] = useState('');
  const [grants, setGrants] = useState<Grant[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [savedIds, setSavedIds] = useState<Set<string>>(new Set());

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const params: Record<string, string> = {};
      if (keyword) params.keyword = keyword;
      if (source) params.source = source;
      const { data } = await api.get<Grant[]>('/grants', { params });
      setGrants(data);
    } catch {
      setError('Search failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const saveGrant = async (grantId: string) => {
    try {
      await api.post('/grants/save', { grant_id: grantId });
      setSavedIds((prev) => new Set(prev).add(grantId));
    } catch {
      // already saved or error
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Search Grants</h1>

      <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-3">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-text-muted)]" />
          <input type="text" value={keyword} onChange={(e) => setKeyword(e.target.value)} placeholder="Search grants..."
            className="w-full pl-10 pr-3 py-2 border border-[var(--color-border)] rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]" />
        </div>
        <select value={source} onChange={(e) => setSource(e.target.value)}
          className="px-3 py-2 border border-[var(--color-border)] rounded-lg">
          <option value="">All Sources</option>
          <option value="grants.gov">Grants.gov</option>
          <option value="fwf">FWF</option>
        </select>
        <button type="submit" disabled={loading}
          className="px-6 py-2 bg-[var(--color-primary)] text-white rounded-lg hover:bg-[var(--color-primary-hover)] disabled:opacity-50">
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>

      {error && <div className="bg-red-50 text-red-600 p-3 rounded-lg text-sm">{error}</div>}

      <div className="space-y-4">
        {grants.map((grant) => (
          <div key={grant.id} className="bg-white p-6 rounded-xl border border-[var(--color-border)]">
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <h3 className="font-semibold text-lg mb-1">{grant.title}</h3>
                <div className="flex flex-wrap gap-3 text-sm text-[var(--color-text-muted)] mb-2">
                  {grant.agency && <span>{grant.agency}</span>}
                  {grant.award_amount && <span>Award: {grant.award_amount}</span>}
                  {grant.deadline && <span>Deadline: {new Date(grant.deadline).toLocaleDateString()}</span>}
                  {grant.source && <span className="px-2 py-0.5 bg-gray-100 rounded text-xs">{grant.source}</span>}
                </div>
                {grant.description && (
                  <p className="text-sm text-[var(--color-text-muted)] line-clamp-2">{grant.description}</p>
                )}
              </div>
              <div className="flex gap-2 ml-4">
                <button onClick={() => saveGrant(grant.id)} disabled={savedIds.has(grant.id)}
                  className={`p-2 rounded-lg border ${savedIds.has(grant.id) ? 'bg-blue-50 border-blue-200 text-[var(--color-primary)]' : 'border-[var(--color-border)] hover:bg-gray-50'}`}>
                  <Bookmark className="w-4 h-4" />
                </button>
                {grant.url && (
                  <a href={grant.url} target="_blank" rel="noopener noreferrer"
                    className="p-2 rounded-lg border border-[var(--color-border)] hover:bg-gray-50">
                    <ExternalLink className="w-4 h-4" />
                  </a>
                )}
              </div>
            </div>
          </div>
        ))}
        {!loading && grants.length === 0 && (
          <div className="text-center py-12 text-[var(--color-text-muted)]">
            Search for grants to get started
          </div>
        )}
      </div>
    </div>
  );
}
