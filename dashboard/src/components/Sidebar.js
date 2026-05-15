import { NavLink } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { navForRole } from "../auth/roles";
import {
  LayoutDashboard, Map, Radio, BrainCircuit,
  ShieldCheck, FileText, Settings, LogOut
} from "lucide-react";

// Maps route paths to icons
const ICON_MAP = {
  "/dashboard":      <LayoutDashboard size={18} />,
  "/map":            <Map size={18} />,
  "/equipments":     <Radio size={18} />,
  "/moderation":     <ShieldCheck size={18} />,
  "/rapports":       <FileText size={18} />,
  "/administration": <Settings size={18} />,
};

export default function Sidebar() {
  const { role, logout } = useAuth();
  const liens = navForRole(role);

  return (
    <div className="sidebar">
      <div className="sidebar-brand">
        <div className="sidebar-logo">TT</div>
        <div>
          <div className="sidebar-title">NOC Platform</div>
          <div className="sidebar-subtitle">Tunisie Télécom</div>
        </div>
      </div>

      <div className="sidebar-section-label">Navigation</div>
      <nav className="sidebar-nav">
        {liens.map((lien) => (
          <NavLink
            key={lien.to}
            to={lien.to}
            className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
          >
            <span className="nav-icon">{ICON_MAP[lien.to]}</span>
            <span>{lien.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <button className="sidebar-logout-btn" onClick={logout}>
          <LogOut size={16} />
          <span>Déconnexion</span>
        </button>
      </div>
    </div>
  );
}