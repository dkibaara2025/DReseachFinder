export interface User {
  id: string;
  email: string;
  name: string | null;
  institution: string | null;
  scholar_profile_url: string | null;
  created_at: string;
}

export interface UserProfile {
  id: string;
  user_id: string;
  research_interests: string[] | null;
  publications: Record<string, unknown> | null;
  orcid: string | null;
  cv_text: string | null;
  h_index: number | null;
  citation_count: number | null;
  last_synced_at: string | null;
}

export interface Grant {
  id: string;
  title: string;
  description: string | null;
  agency: string | null;
  award_amount: string | null;
  deadline: string | null;
  eligibility: string | null;
  category: string | null;
  source: string | null;
  url: string | null;
  fetched_at: string;
}

export interface UserGrant {
  id: string;
  user_id: string;
  grant_id: string;
  status: 'saved' | 'applying' | 'submitted' | 'awarded' | 'rejected';
  notes: string | null;
  saved_at: string;
  grant: Grant | null;
}

export interface Application {
  id: string;
  user_id: string;
  grant_id: string;
  title: string | null;
  content: Record<string, string> | null;
  references_data: Record<string, unknown> | null;
  status: 'draft' | 'submitted';
  created_at: string;
  updated_at: string;
  pdf_url: string | null;
}

export interface PaperResult {
  title: string;
  authors: string[];
  year: number | null;
  doi: string | null;
  arxiv_id: string | null;
  pmid: string | null;
  abstract: string | null;
  citation_count: number;
  source: string;
  url: string | null;
}

export interface AlertSubscription {
  id: string;
  keywords: string[];
  is_active: boolean;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}
