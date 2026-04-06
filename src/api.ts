import type { AuthResponse, Internship, InternshipDiagnostics, Metro, Profile } from "./types";

const API_BASE = "/api";
const FILE_BASE = "";
const TOKEN_KEY = "internmatch-token";
const USER_KEY = "internmatch-user";
const FALLBACK_METROS: Metro[] = [
  { slug: "atlanta", name: "Atlanta" },
  { slug: "austin", name: "Austin" },
  { slug: "boston", name: "Boston" },
  { slug: "chicago", name: "Chicago" },
  { slug: "dallas", name: "Dallas-Fort Worth" },
  { slug: "denver", name: "Denver" },
  { slug: "houston", name: "Houston" },
  { slug: "los-angeles", name: "Los Angeles" },
  { slug: "miami", name: "Miami" },
  { slug: "new-york", name: "New York City" },
  { slug: "philadelphia", name: "Philadelphia" },
  { slug: "phoenix", name: "Phoenix" },
  { slug: "raleigh", name: "Raleigh-Durham" },
  { slug: "san-francisco", name: "San Francisco Bay Area" },
  { slug: "seattle", name: "Seattle" },
  { slug: "washington-dc", name: "Washington, DC" }
];

function getToken(): string | null {
  return window.localStorage.getItem(TOKEN_KEY);
}

function authHeaders(): HeadersInit {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export function getStoredUser() {
  const stored = window.localStorage.getItem(USER_KEY);
  return stored ? JSON.parse(stored) : null;
}

export function persistSession(payload: AuthResponse) {
  window.localStorage.setItem(TOKEN_KEY, payload.token);
  window.localStorage.setItem(USER_KEY, JSON.stringify(payload.user));
}

export function clearSession() {
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(USER_KEY);
}

export async function registerUser(fullName: string, email: string, password: string): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ full_name: fullName, email, password })
  });
  if (!response.ok) {
    throw new Error((await response.json()).detail ?? "Unable to create account.");
  }
  return response.json();
}

export async function loginUser(email: string, password: string): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  });
  if (!response.ok) {
    throw new Error((await response.json()).detail ?? "Unable to sign in.");
  }
  return response.json();
}

export async function fetchMetros(): Promise<Metro[]> {
  try {
    const response = await fetch(`${API_BASE}/metros`);
    if (!response.ok) {
      throw new Error("Unable to load metro areas.");
    }
    const data = await response.json();
    return data.metros;
  } catch {
    return FALLBACK_METROS;
  }
}

export async function fetchInternships(metro: string, keyword: string): Promise<{ results: Internship[]; diagnostics: InternshipDiagnostics }> {
  const params = new URLSearchParams({ metro, keyword });
  const response = await fetch(`${API_BASE}/internships?${params.toString()}`);
  if (!response.ok) {
    throw new Error("Unable to load internships.");
  }
  const data = await response.json();
  return {
    results: data.results,
    diagnostics: data.diagnostics ?? { errors: [], usedFallback: false }
  };
}

export async function fetchProfiles(): Promise<Profile[]> {
  const response = await fetch(`${API_BASE}/profiles`, {
    headers: authHeaders()
  });
  if (!response.ok) {
    throw new Error("Unable to load profiles.");
  }
  const data = await response.json();
  return data.profiles.map((profile: Profile) => ({
    ...profile,
    resumeUrl: `${FILE_BASE}${profile.resumeUrl}`,
    transcriptUrl: `${FILE_BASE}${profile.transcriptUrl}`
  }));
}

export async function createProfile(formData: FormData): Promise<Profile> {
  const response = await fetch(`${API_BASE}/profiles`, {
    method: "POST",
    headers: authHeaders(),
    body: formData
  });

  if (!response.ok) {
    const detail = await response.json().catch(() => null);
    throw new Error(detail?.detail ?? "Unable to create profile.");
  }

  const data = await response.json();
  return {
    ...data.profile,
    resumeUrl: `${FILE_BASE}${data.profile.resumeUrl}`,
    transcriptUrl: `${FILE_BASE}${data.profile.transcriptUrl}`
  };
}
