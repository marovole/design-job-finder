"use client";

import { useQuery, useMutation } from "convex/react";
import { api } from "@/convex/_generated/api";
import { useState } from "react";
import { useAuth } from "@convex-dev/auth/react";

export default function Home() {
  const { signIn, signOut, isAuthenticated } = useAuth();
  const profile = useQuery(api.functions.profile.getProfile);
  const projects = useQuery(api.functions.projects.getProjects, { limit: 10 });
  const stats = useQuery(api.functions.projects.getProjectStats);
  const searchProjects = useMutation(api.functions.search.searchProjects);
  const generateEmail = useMutation(api.functions.emails.generateEmail);
  const generateEmailWithAI = useMutation(api.functions.emails.generateEmailWithAI);

  const [searchQuery, setSearchQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const [generatingAI, setGeneratingAI] = useState<string | null>(null);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setSearching(true);
    try {
      await searchProjects({
        query: searchQuery,
        platforms: ["fiverr", "upwork", "dribbble"],
      });
    } catch (error) {
      console.error("Search failed:", error);
    }
    setSearching(false);
  };

  if (!isAuthenticated) {
    return (
      <div className="container" style={{ padding: "4rem 1rem", textAlign: "center" }}>
        <h1 style={{ fontSize: "2rem", marginBottom: "1rem" }}>PM Job Finder</h1>
        <p className="text-muted" style={{ marginBottom: "2rem" }}>
          Find overseas PM and design jobs with AI-powered matching
        </p>
        <div className="flex" style={{ justifyContent: "center" }}>
          <button className="btn btn-primary" onClick={() => signIn("github")}>
            Sign in with GitHub
          </button>
          <button className="btn btn-secondary" onClick={() => signIn("google")}>
            Sign in with Google
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="container" style={{ padding: "2rem 1rem" }}>
      <header className="flex justify-between items-center mb-8">
        <div>
          <h1>PM Job Finder</h1>
          {profile && <p className="text-muted">Welcome, {profile.nameEn}</p>}
        </div>
        <button className="btn btn-secondary" onClick={() => signOut()}>
          Sign out
        </button>
      </header>

      {/* Stats */}
      {stats && (
        <div className="grid" style={{ gridTemplateColumns: "repeat(4, 1fr)", marginBottom: "2rem" }}>
          <div className="card">
            <p className="text-sm text-muted">Total Projects</p>
            <p className="font-bold" style={{ fontSize: "1.5rem" }}>{stats.total}</p>
          </div>
          <div className="card">
            <p className="text-sm text-muted">Avg Match Score</p>
            <p className="font-bold" style={{ fontSize: "1.5rem" }}>{stats.avgScore.toFixed(0)}</p>
          </div>
          <div className="card">
            <p className="text-sm text-muted">Emails Generated</p>
            <p className="font-bold" style={{ fontSize: "1.5rem" }}>{stats.withEmail}</p>
          </div>
          <div className="card">
            <p className="text-sm text-muted">Validated Contacts</p>
            <p className="font-bold" style={{ fontSize: "1.5rem" }}>{stats.validated}</p>
          </div>
        </div>
      )}

      {/* Search */}
      <div className="card mb-8">
        <h2 className="mb-4">Search Projects</h2>
        <div className="flex">
          <input
            className="input"
            placeholder="UX designer, dashboard, analytics..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          />
          <button
            className="btn btn-primary"
            onClick={handleSearch}
            disabled={searching}
          >
            {searching ? "Searching..." : "Search"}
          </button>
        </div>
      </div>

      {/* Projects List */}
      <div className="card">
        <h2 className="mb-4">Recent Projects</h2>
        {projects && projects.projects.length > 0 ? (
          <div className="grid" style={{ gap: "1rem" }}>
            {projects.projects.map((project: any) => (
              <div
                key={project._id}
                style={{
                  padding: "1rem",
                  border: "1px solid var(--border)",
                  borderRadius: "0.5rem",
                }}
              >
                <div className="flex justify-between items-center mb-2">
                  <span className="badge badge-success">{project.platform}</span>
                  {project.matchScore !== undefined && (
                    <span
                      className={`badge ${
                        project.matchScore >= 80
                          ? "badge-success"
                          : project.matchScore >= 60
                          ? "badge-warning"
                          : "badge-error"
                      }`}
                    >
                      Score: {project.matchScore}
                    </span>
                  )}
                </div>
                <h3>{project.title}</h3>
                <p className="text-sm text-muted" style={{ marginTop: "0.5rem" }}>
                  {project.description?.substring(0, 150)}...
                </p>
                <div className="flex" style={{ marginTop: "1rem", gap: "0.5rem" }}>
                  <button
                    className="btn btn-secondary text-sm"
                    onClick={() => generateEmail({ projectId: project._id })}
                  >
                    Template Email
                  </button>
                  <button
                    className="btn btn-primary text-sm"
                    onClick={async () => {
                      setGeneratingAI(project._id);
                      try {
                        await generateEmailWithAI({ projectId: project._id });
                      } catch (e) {
                        console.error("AI generation failed:", e);
                      }
                      setGeneratingAI(null);
                    }}
                    disabled={generatingAI === project._id}
                  >
                    {generatingAI === project._id ? "Generating..." : "AI Email"}
                  </button>
                  {project.projectUrl && (
                    <a
                      className="btn btn-secondary text-sm"
                      href={project.projectUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      View
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-muted">No projects yet. Search to find opportunities!</p>
        )}
      </div>
    </div>
  );
}
