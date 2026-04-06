import { FormEvent, useEffect, useState } from "react";
import {
  clearSession,
  createProfile,
  fetchInternships,
  fetchMetros,
  fetchProfiles,
  getStoredUser,
  loginUser,
  persistSession,
  registerUser
} from "./api";
import type { Internship, Metro, Profile, User } from "./types";

const emptyMessage = "Pick a metro and search across live internship sources.";

export default function App() {
  const [metros, setMetros] = useState<Metro[]>([]);
  const [selectedMetro, setSelectedMetro] = useState("");
  const [profileMetro, setProfileMetro] = useState("");
  const [keyword, setKeyword] = useState("");
  const [internships, setInternships] = useState<Internship[]>([]);
  const [scraperNotice, setScraperNotice] = useState("");
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [user, setUser] = useState<User | null>(() => getStoredUser());
  const [authMode, setAuthMode] = useState<"login" | "register">("register");
  const [authError, setAuthError] = useState("");
  const [dashboardError, setDashboardError] = useState("");
  const [backendNotice, setBackendNotice] = useState("");
  const [searchMessage, setSearchMessage] = useState(emptyMessage);
  const [isSearching, setIsSearching] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isAuthenticating, setIsAuthenticating] = useState(false);

  useEffect(() => {
    async function loadMetros() {
      try {
        const metroList = await fetchMetros();
        setMetros(metroList);
        setBackendNotice("");
        if (metroList.length > 0) {
          setSelectedMetro((current) => current || metroList[0].slug);
          setProfileMetro((current) => current || metroList[0].slug);
        }
      } catch (requestError) {
        setDashboardError(requestError instanceof Error ? requestError.message : "Unable to load metro areas.");
      }
    }

    void loadMetros();
  }, []);

  useEffect(() => {
    if (!user) {
      setProfiles([]);
      return;
    }

    async function loadProfiles() {
      try {
        const profileList = await fetchProfiles();
        setProfiles(profileList);
        setBackendNotice("");
      } catch (requestError) {
        setDashboardError(requestError instanceof Error ? requestError.message : "Unable to load profiles.");
        setBackendNotice("The backend is not reachable or you are not signed in yet. Metro selection still works from a built-in list.");
      }
    }

    void loadProfiles();
  }, [user]);

  async function handleAuth(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const fullName = String(formData.get("full_name") ?? "");
    const email = String(formData.get("email") ?? "");
    const password = String(formData.get("password") ?? "");

    setAuthError("");
    setIsAuthenticating(true);

    try {
      const session =
        authMode === "register" ? await registerUser(fullName, email, password) : await loginUser(email, password);
      persistSession(session);
      setUser(session.user);
      setDashboardError("");
      event.currentTarget.reset();
    } catch (requestError) {
      setAuthError(requestError instanceof Error ? requestError.message : "Authentication failed.");
    } finally {
      setIsAuthenticating(false);
    }
  }

  async function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedMetro) {
      setDashboardError("Please choose a metro area first.");
      return;
    }

    setDashboardError("");
    setSearchMessage("Scanning internships across Greenhouse and Lever...");
    setIsSearching(true);

    try {
      const results = await fetchInternships(selectedMetro, keyword);
      setInternships(results.results);
      setBackendNotice("");
      setSearchMessage(results.results.length > 0 ? `Ranked ${results.results.length} internships for this metro.` : "No internships matched yet. Try another metro or keyword.");
      setScraperNotice(
        results.diagnostics.usedFallback
          ? "Live job boards were unreachable, so these results are from fallback sample internship data."
          : ""
      );
    } catch (requestError) {
      setDashboardError(requestError instanceof Error ? requestError.message : "Search failed.");
      setSearchMessage(emptyMessage);
      setScraperNotice("");
      setBackendNotice("The frontend could not reach the backend search API. Check that FastAPI is running on http://127.0.0.1:8000.");
    } finally {
      setIsSearching(false);
    }
  }

  async function handleCreateProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);
    setDashboardError("");
    setIsSubmitting(true);

    try {
      const profile = await createProfile(formData);
      setProfiles((current) => [profile, ...current]);
      form.reset();
      setProfileMetro(selectedMetro);
    } catch (requestError) {
      setDashboardError(requestError instanceof Error ? requestError.message : "Profile creation failed.");
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleSignOut() {
    clearSession();
    setUser(null);
    setProfiles([]);
  }

  const averageGpa = profiles.length > 0 ? (profiles.reduce((sum, profile) => sum + profile.gpa, 0) / profiles.length).toFixed(2) : "0.00";

  return (
    <div className="app-shell">
      <div className="backdrop backdrop-one" />
      <div className="backdrop backdrop-two" />

      <section className="hero-band">
        <div className="hero-copy">
          <p className="eyebrow">Intern intelligence for students</p>
          <h1>Search by metro, store application documents, and keep your internship pipeline in motion.</h1>
          <p className="hero-text">
            InternMatch now includes student accounts, SQLite-backed profiles, and a multi-source Python scraper that ranks internship roles across major job boards.
          </p>

          <div className="hero-metrics">
            <div className="metric-tile">
              <span className="metric-value">{metros.length}</span>
              <span className="metric-label">metros ready</span>
            </div>
            <div className="metric-tile">
              <span className="metric-value">{internships.length}</span>
              <span className="metric-label">roles ranked</span>
            </div>
            <div className="metric-tile">
              <span className="metric-value">{profiles.length}</span>
              <span className="metric-label">saved profiles</span>
            </div>
          </div>
        </div>

        <aside className="auth-panel">
          <div className="auth-header">
            <p className="eyebrow">Student access</p>
            <h2>{user ? `Welcome back, ${user.fullName.split(" ")[0]}` : "Create your workspace"}</h2>
          </div>

          {user ? (
            <div className="signed-in-card">
              <p>{user.email}</p>
              <p>Profiles saved: {profiles.length}</p>
              <button className="ghost-button" onClick={handleSignOut} type="button">
                Sign out
              </button>
            </div>
          ) : (
            <form className="auth-form" onSubmit={handleAuth}>
              {authMode === "register" ? (
                <label>
                  Full name
                  <input name="full_name" type="text" placeholder="Jordan Lee" required />
                </label>
              ) : null}

              <label>
                Email
                <input name="email" type="email" placeholder="jordan@example.com" required />
              </label>

              <label>
                Password
                <input name="password" type="password" placeholder="At least 8 characters" required />
              </label>

              {authError ? <p className="error-text">{authError}</p> : null}

              <button type="submit" disabled={isAuthenticating}>
                {isAuthenticating ? "Working..." : authMode === "register" ? "Create account" : "Sign in"}
              </button>

              <button
                className="ghost-button"
                onClick={() => setAuthMode((current) => (current === "register" ? "login" : "register"))}
                type="button"
              >
                {authMode === "register" ? "Already have an account?" : "Need an account?"}
              </button>
            </form>
          )}
        </aside>
      </section>

      <main className="dashboard-grid">
        <section className="card search-card">
          <div className="card-heading">
            <p className="eyebrow">Opportunity radar</p>
            <h2>Search internships by metro area</h2>
          </div>

          <form className="search-form" onSubmit={handleSearch}>
            <label>
              Metro area
              <select value={selectedMetro} onChange={(event) => setSelectedMetro(event.target.value)} required>
                <option value="" disabled>
                  Select a metro area
                </option>
                {metros.map((metro) => (
                  <option key={metro.slug} value={metro.slug}>
                    {metro.name}
                  </option>
                ))}
              </select>
            </label>

            <label>
              Focus area
              <input
                type="text"
                value={keyword}
                onChange={(event) => setKeyword(event.target.value)}
                placeholder="Software, data, product, design..."
              />
            </label>

            <button type="submit" disabled={isSearching}>
              {isSearching ? "Scanning..." : "Run search"}
            </button>
          </form>

          <p className="status-text">{searchMessage}</p>
          {backendNotice ? <p className="status-text">{backendNotice}</p> : null}
          {scraperNotice ? <p className="status-text">{scraperNotice}</p> : null}
          {dashboardError ? <p className="error-text">{dashboardError}</p> : null}

          <div className="results-list">
            {internships.map((internship) => (
              <article className="result-card" key={internship.id}>
                <div className="result-topline">
                  <span className="result-source">{internship.source}</span>
                  <span className="result-score">Score {internship.score}</span>
                </div>
                <h3>{internship.title}</h3>
                <p className="result-company">{internship.company}</p>
                <p className="result-meta">
                  {internship.location} · {internship.department}
                </p>
                <a href={internship.url} rel="noreferrer" target="_blank">
                  Open listing
                </a>
              </article>
            ))}
          </div>
        </section>

        <section className="card profile-card-shell">
          <div className="card-heading">
            <p className="eyebrow">Application vault</p>
            <h2>Save a ready-to-send profile</h2>
          </div>

          <div className="mini-stats">
            <div>
              <span className="mini-stat-label">Avg GPA</span>
              <strong>{averageGpa}</strong>
            </div>
            <div>
              <span className="mini-stat-label">Best-fit metro</span>
              <strong>{metros.find((metro) => metro.slug === selectedMetro)?.name ?? "Not selected"}</strong>
            </div>
          </div>

          {user ? (
            <form className="profile-form" onSubmit={handleCreateProfile}>
              <label>
                Target role
                <input type="text" name="target_role" placeholder="Software Engineering Intern" required />
              </label>

              <label>
                GPA
                <input type="number" name="gpa" min="0" max="4" step="0.01" placeholder="3.75" required />
              </label>

              <label>
                Preferred metro area
                <select name="metro_slug" value={profileMetro} onChange={(event) => setProfileMetro(event.target.value)} required>
                  <option value="" disabled>
                    Select a metro area
                  </option>
                  {metros.map((metro) => (
                    <option key={metro.slug} value={metro.slug}>
                      {metro.name}
                    </option>
                  ))}
                </select>
              </label>

              <label>
                Resume
                <input type="file" name="resume" accept=".pdf,.doc,.docx" required />
              </label>

              <label>
                Transcript
                <input type="file" name="transcript" accept=".pdf,.png,.jpg,.jpeg" required />
              </label>

              <button type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Saving..." : "Save profile"}
              </button>
            </form>
          ) : (
            <p className="status-text">Create an account first to upload resumes and transcripts.</p>
          )}
        </section>

        <section className="card profile-list-card">
          <div className="card-heading">
            <p className="eyebrow">Saved assets</p>
            <h2>Your profile snapshots</h2>
          </div>

          <div className="profile-list">
            {profiles.length === 0 ? (
              <p className="status-text">No saved profiles yet.</p>
            ) : (
              profiles.map((profile) => (
                <article className="profile-record" key={profile.id}>
                  <div>
                    <h3>{profile.targetRole}</h3>
                    <p>
                      {profile.metroName} · GPA {profile.gpa.toFixed(2)}
                    </p>
                  </div>
                  <div className="profile-links">
                    <a href={profile.resumeUrl} rel="noreferrer" target="_blank">
                      Resume
                    </a>
                    <a href={profile.transcriptUrl} rel="noreferrer" target="_blank">
                      Transcript
                    </a>
                  </div>
                </article>
              ))
            )}
          </div>
        </section>
      </main>
    </div>
  );
}
