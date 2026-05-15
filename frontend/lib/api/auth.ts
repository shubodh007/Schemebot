import { api } from "./client";

export interface UserResponse {
  id: string;
  email: string;
  email_verified: boolean;
  role: string;
  status: string;
  created_at: string;
}

export interface ProfileResponse {
  id: string;
  user_id: string;
  full_name: string;
  phone: string | null;
  date_of_birth: string | null;
  gender: string | null;
  caste_category: string | null;
  disability_status: string;
  disability_percent: number | null;
  annual_income: number | null;
  state_code: string | null;
  district: string | null;
  occupation: string | null;
  education_level: string | null;
  is_farmer: boolean;
  is_bpl: boolean;
  marital_status: string | null;
  preferred_language: string;
  profile_complete: boolean;
}

export interface AuthMeResponse {
  user: UserResponse;
  profile: ProfileResponse;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: UserResponse;
  profile: ProfileResponse;
}

export const authApi = {
  register: (data: { email: string; password: string; full_name: string }) =>
    api.post<{ user: UserResponse; message: string }>("/auth/register", data),

  login: (data: { email: string; password: string }) =>
    api.post<LoginResponse>("/auth/login", data),

  refresh: () => api.post<{ access_token: string }>("/auth/refresh"),

  logout: () => api.post<void>("/auth/logout"),

  getMe: () => api.get<AuthMeResponse>("/auth/me"),

  updateProfile: (data: Partial<ProfileResponse>) =>
    api.patch<{ profile: ProfileResponse }>("/auth/profile", data),
};
