export type Metro = {
  slug: string;
  name: string;
};

export type User = {
  id: number;
  fullName: string;
  email: string;
  createdAt: string;
};

export type Internship = {
  id: string;
  company: string;
  title: string;
  department: string;
  location: string;
  url: string;
  updatedAt?: string;
  isRemote: boolean;
  source: string;
  score: number;
};

export type InternshipDiagnostics = {
  errors: string[];
  usedFallback: boolean;
};

export type Profile = {
  id: number;
  targetRole: string;
  gpa: number;
  metroSlug: string;
  metroName: string;
  resumeUrl: string;
  transcriptUrl: string;
  createdAt: string;
};

export type AuthResponse = {
  token: string;
  user: User;
};
