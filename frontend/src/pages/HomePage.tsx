import { Link } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { Search, FileText, BookOpen, Bell } from 'lucide-react';

export default function HomePage() {
  const { isAuthenticated } = useAuthStore();

  return (
    <div className="space-y-16">
      <section className="text-center py-16">
        <h1 className="text-5xl font-bold text-[var(--color-text)] mb-4">
          Discover Research Funding with AI
        </h1>
        <p className="text-xl text-[var(--color-text-muted)] max-w-2xl mx-auto mb-8">
          GrantAssist AI helps researchers find global funding opportunities, manage academic profiles,
          and draft compelling grant applications using AI.
        </p>
        {!isAuthenticated && (
          <div className="flex gap-4 justify-center">
            <Link to="/register" className="px-6 py-3 bg-[var(--color-primary)] text-white rounded-lg text-lg hover:bg-[var(--color-primary-hover)] transition-colors">
              Get Started Free
            </Link>
            <Link to="/login" className="px-6 py-3 border border-[var(--color-border)] rounded-lg text-lg hover:bg-gray-50 transition-colors">
              Sign In
            </Link>
          </div>
        )}
        {isAuthenticated && (
          <Link to="/dashboard" className="px-6 py-3 bg-[var(--color-primary)] text-white rounded-lg text-lg hover:bg-[var(--color-primary-hover)] transition-colors inline-block">
            Go to Dashboard
          </Link>
        )}
      </section>

      <section className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[
          { icon: Search, title: 'Grant Discovery', desc: 'Search grants from Grants.gov, FWF, and more with semantic search.' },
          { icon: BookOpen, title: 'Literature Search', desc: 'Query OpenAlex, Crossref, Semantic Scholar, and arXiv in parallel.' },
          { icon: FileText, title: 'AI Drafting', desc: 'Generate proposal sections with LLM assistance and auto-references.' },
          { icon: Bell, title: 'Smart Alerts', desc: 'Get daily email digests of new grants matching your interests.' },
        ].map(({ icon: Icon, title, desc }) => (
          <div key={title} className="bg-white p-6 rounded-xl border border-[var(--color-border)] hover:shadow-lg transition-shadow">
            <Icon className="w-10 h-10 text-[var(--color-primary)] mb-4" />
            <h3 className="font-semibold text-lg mb-2">{title}</h3>
            <p className="text-[var(--color-text-muted)] text-sm">{desc}</p>
          </div>
        ))}
      </section>
    </div>
  );
}
