import { api } from "./client";

export interface SchemeCard {
  id: string;
  title: string;
  title_hi?: string;
  title_te?: string;
  slug: string;
  description: string;
  level: string;
  state_code?: string;
  status: string;
  tags: string[];
  created_at: string;
}

export interface SchemeDetail {
  id: string;
  title: string;
  title_hi?: string;
  title_te?: string;
  slug: string;
  description: string;
  description_hi?: string;
  description_te?: string;
  ministry?: string;
  department?: string;
  level: string;
  state_code?: string;
  application_url?: string;
  guidelines_url?: string;
  tags: string[];
  eligibility_rules?: EligibilityRule[];
}

export interface EligibilityRule {
  id: string;
  field_name: string;
  operator: string;
  value: unknown;
  is_mandatory: boolean;
  description?: string;
}

export interface EligibilityMatch {
  scheme: SchemeCard;
  score: number;
  eligible: boolean;
  matching_rules: string[];
  failing_rules: string[];
  missing_fields: string[];
}

export interface Category {
  id: string;
  name: string;
  slug: string;
  icon_name?: string;
  scheme_count: number;
}

export const schemesApi = {
  list: (params?: {
    query?: string;
    category_id?: string;
    level?: string;
    state_code?: string;
    page?: number;
    limit?: number;
  }) => api.get<{ schemes: SchemeCard[]; total: number; page: number; has_more: boolean }>("/schemes", { params: params as Record<string, string | number | boolean | undefined> }),

  get: (id: string) => api.get<{ scheme: SchemeDetail }>(`/schemes/${id}`),

  categories: () => api.get<Category[]>("/schemes/categories"),

  checkEligibility: (data?: { profile_override?: Record<string, unknown> }) =>
    api.post<{ matches: EligibilityMatch[]; checked_at: string; profile_completeness: number }>("/schemes/eligibility-check", data),

  getEligibility: (id: string) =>
    api.get<{ eligible: boolean; score: number; reasons: string[]; missing_fields: string[] }>(`/schemes/${id}/eligibility`),

  save: (id: string, data?: { notes?: string }) =>
    api.post(`/schemes/${id}/save`, data),

  unsave: (id: string) => api.delete(`/schemes/${id}/save`),

  saved: () => api.get<{ saved: unknown[] }>("/schemes/saved/list"),

  compare: (data: { scheme_ids: string[]; name?: string }) =>
    api.post("/schemes/compare", data),
};
