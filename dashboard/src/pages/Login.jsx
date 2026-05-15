import { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { User, Lock, Eye, EyeOff, Wifi, AlertCircle, Loader } from "lucide-react";
import { useAuth } from "../auth/AuthContext";
import "./LoginPage.css";

const DEMO_ACCOUNTS = [
  { role: "Admin", user: "admin", pass: "admin123", color: "#2563eb" },
  { role: "Ingénieur", user: "ingenieur", pass: "ing123", color: "#7c3aed" },
  { role: "technicien", user: "technicien", pass: "tech123", color: "#d758faff" },

];

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPass, setShowPass] = useState(false);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [mounted, setMounted] = useState(false);

  const { login, estConnecte } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const redirect = location.state?.from?.pathname || "/dashboard";

  useEffect(() => {
    const t = setTimeout(() => setMounted(true), 50);
    return () => clearTimeout(t);
  }, []);

  useEffect(() => {
    if (estConnecte) navigate(redirect, { replace: true });
  }, [estConnecte, redirect, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!username.trim() || !password) {
      setError("Veuillez remplir tous les champs.");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      await login(username.trim(), password);
      navigate(redirect, { replace: true });
    } catch (err) {
      setError(err.message || "Identifiants incorrects. Vérifiez vos accès.");
    } finally {
      setLoading(false);
    }
  };

  const fillDemo = (user, pass) => {
    setUsername(user);
    setPassword(pass);
    setError(null);
  };

  return (
    <div className="login-bg">
      {/* Subtle background circles */}
      <div className="login-circle login-circle-1" />
      <div className="login-circle login-circle-2" />
      <div className="login-circle login-circle-3" />

      <div className={`login-card-wrap${mounted ? " login-visible" : ""}`}>

        {/* ── PFE Header ── */}
        <div className="login-pfe-header">
          <div className="login-pfe-logo">
            <Wifi size={28} color="#2563eb" strokeWidth={2.5} />
          </div>
          <div className="login-pfe-badge">PROJET PFE</div>
          <h1 className="login-pfe-names">Malek Maadi &amp; Abir Said</h1>
          <p className="login-pfe-subtitle">
            Plateforme intelligente de supervision réseau télécom basée IA &amp; SIG
          </p>
        </div>

        {/* ── Login Card ── */}
        <div className="login-card">

          <div className="login-card-head">
            <h2 className="login-card-title">Connexion</h2>
            <p className="login-card-sub">Accès réservé au personnel autorisé</p>
          </div>

          <form onSubmit={handleSubmit} className="login-form" noValidate>

            {/* Username */}
            <div className="login-field">
              <label className="login-label" htmlFor="login-user">Identifiant</label>
              <div className="login-input-wrap">
                <User size={16} className="login-input-icon" />
                <input
                  id="login-user"
                  type="text"
                  className="login-input"
                  placeholder="ex : admin"
                  autoComplete="username"
                  value={username}
                  onChange={(e) => { setUsername(e.target.value); setError(null); }}
                  disabled={loading}
                />
              </div>
            </div>

            {/* Password */}
            <div className="login-field">
              <label className="login-label" htmlFor="login-pass">Mot de passe</label>
              <div className="login-input-wrap">
                <Lock size={16} className="login-input-icon" />
                <input
                  id="login-pass"
                  type={showPass ? "text" : "password"}
                  className="login-input"
                  placeholder="••••••••"
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => { setPassword(e.target.value); setError(null); }}
                  disabled={loading}
                />
                <button
                  type="button"
                  className="login-eye-btn"
                  onClick={() => setShowPass((v) => !v)}
                  tabIndex={-1}
                  aria-label={showPass ? "Masquer" : "Afficher"}
                >
                  {showPass ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>
            </div>

            {/* Error */}
            {error && (
              <div className="login-error" role="alert">
                <AlertCircle size={15} />
                <span>{error}</span>
              </div>
            )}

            {/* Submit */}
            <button type="submit" className="login-submit-btn" disabled={loading}>
              {loading ? (
                <><Loader size={16} className="login-spinner" /> Authentification…</>
              ) : (
                "Se connecter"
              )}
            </button>
          </form>

          {/* Demo accounts */}
          <div className="login-demo-section">
            <div className="login-demo-label">Comptes de démonstration</div>
            <div className="login-demo-chips">
              {DEMO_ACCOUNTS.map((a) => (
                <button
                  key={a.user}
                  type="button"
                  className="login-demo-chip"
                  onClick={() => fillDemo(a.user, a.pass)}
                  style={{ "--chip-color": a.color }}
                >
                  <span className="login-demo-role" style={{ color: a.color }}>{a.role}</span>
                  <span className="login-demo-creds">{a.user} / {a.pass}</span>
                </button>
              ))}
            </div>
            <p className="login-demo-hint">Cliquez pour remplir automatiquement.</p>
          </div>

        </div>

        {/* Footer */}
        <p className="login-footer">
          Licence 3ème année — Réseaux &amp; Télécommunications · 2025–2026
        </p>
      </div>
    </div>
  );
}
