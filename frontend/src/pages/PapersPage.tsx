import { useState } from 'react';
import api from '../lib/api';
import type { PaperResult } from '../types';
import { Search, ExternalLink, Quote } from 'lucide-react';

export default function PapersPage() {
  const [keyword, setKeyword] = useState('');
  const [papers, setPapers] = useState<PaperResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedPapers, setSelectedPapers] = useState<Set<number>>(new Set());
  const [citations, setCitations] = useState<string[]>([]);
  const [citationFormat, setCitationFormat] = useState('apa');

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!keyword.trim()) return;
    setLoading(true);
    try {
      const { data } = await api.get<PaperResult[]>('/papers', { params: { keyword } });
      setPapers(data);
      setSelectedPapers(new Set());
      setCitations([]);
    } catch {
      // error
    } finally {
      setLoading(false);
    }
  };

  const togglePaper = (idx: number) => {
    setSelectedPapers((prev) => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx);
      else next.add(idx);
      return next;
    });
  };

  const generateCitations = async () => {
    const identifiers = Array.from(selectedPapers)
      .map((i) => papers[i]?.doi || papers[i]?.arxiv_id || '')
      .filter(Boolean);
    if (identifiers.length === 0) return;
    try {
      const { data } = await api.post('/references', { identifiers, format: citationFormat });
      setCitations(data.map((r: { formatted_citation: string }) => r.formatted_citation));
    } catch {
      // error
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Search Academic Papers</h1>

      <form onSubmit={handleSearch} className="flex gap-3">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-text-muted)]" />
          <input type="text" value={keyword} onChange={(e) => setKeyword(e.target.value)} placeholder="Search papers..."
            className="w-full pl-10 pr-3 py-2 border border-[var(--color-border)] rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]" />
        </div>
        <button type="submit" disabled={loading}
          className="px-6 py-2 bg-[var(--color-primary)] text-white rounded-lg hover:bg-[var(--color-primary-hover)] disabled:opacity-50">
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>

      {selectedPapers.size > 0 && (
        <div className="flex items-center gap-3 bg-blue-50 p-3 rounded-lg">
          <span className="text-sm font-medium">{selectedPapers.size} selected</span>
          <select value={citationFormat} onChange={(e) => setCitationFormat(e.target.value)}
            className="px-2 py-1 border border-[var(--color-border)] rounded text-sm">
            <option value="apa">APA</option>
            <option value="mla">MLA</option>
            <option value="chicago">Chicago</option>
            <option value="bibtex">BibTeX</option>
          </select>
          <button onClick={generateCitations} className="px-3 py-1 bg-[var(--color-primary)] text-white rounded text-sm flex items-center gap-1">
            <Quote className="w-3 h-3" /> Generate Citations
          </button>
        </div>
      )}

      {citations.length > 0 && (
        <div className="bg-white p-4 rounded-xl border border-[var(--color-border)]">
          <h3 className="font-semibold mb-2">Formatted Citations</h3>
          <div className="space-y-2">
            {citations.map((c, i) => (
              <pre key={i} className="text-sm bg-gray-50 p-2 rounded whitespace-pre-wrap">{c}</pre>
            ))}
          </div>
        </div>
      )}

      <div className="space-y-3">
        {papers.map((paper, idx) => (
          <div key={idx} onClick={() => togglePaper(idx)}
            className={`bg-white p-4 rounded-lg border cursor-pointer transition-colors ${selectedPapers.has(idx) ? 'border-[var(--color-primary)] bg-blue-50' : 'border-[var(--color-border)] hover:border-gray-300'}`}>
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <h3 className="font-medium">{paper.title}</h3>
                <div className="text-sm text-[var(--color-text-muted)] mt-1">
                  {paper.authors.slice(0, 3).join(', ')}
                  {paper.authors.length > 3 && ' et al.'}
                  {paper.year && ` (${paper.year})`}
                </div>
                {paper.abstract && (
                  <p className="text-sm text-[var(--color-text-muted)] mt-2 line-clamp-2">{paper.abstract}</p>
                )}
                <div className="flex gap-3 mt-2 text-xs text-[var(--color-text-muted)]">
                  <span>Citations: {paper.citation_count}</span>
                  <span className="px-1.5 py-0.5 bg-gray-100 rounded">{paper.source}</span>
                  {paper.doi && <span>DOI: {paper.doi}</span>}
                </div>
              </div>
              {paper.url && (
                <a href={paper.url} target="_blank" rel="noopener noreferrer"
                  onClick={(e) => e.stopPropagation()}
                  className="p-2 rounded-lg border border-[var(--color-border)] hover:bg-gray-50 ml-3">
                  <ExternalLink className="w-4 h-4" />
                </a>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
