/*
 * roles.js  —  Définition des 4 rôles RBAC et de la navigation
 *
 * Rôles de la plateforme NOC Tunisie Télécom :
 *
 *   administrateur     : accès complet (toutes les pages + CRUD antennes)
 *   ingenieur_reseau   : accès technique (antennes, analytics, rapports)
 *   ingenieur_reseau     : supervision temps réel (dashboard, incidents, rapports)
 *   technicien_terrain : accès consultation (dashboard, carte, antennes)
 */

// =============================================================
// Les rôles RBAC de la plateforme
// =============================================================
export const ROLE = {
  ADMIN:       "administrateur",
  INGENIEUR:   "ingenieur_reseau",
  TECHNICIEN:  "technicien_terrain",
};

// Libellés affichables pour chaque rôle
export const ROLE_LABELS = {
  administrateur:     { label: "Administrateur",     color: "#7c3aed" },
  ingenieur_reseau:   { label: "Ingénieur Réseau",   color: "#2563eb" },
  technicien_terrain: { label: "Technicien Terrain", color: "#d97706" },
};

// =============================================================
// Menu de navigation avec permissions par rôle
// =============================================================
export const MENU_NAVIGATION = [
  {
    to:    "/dashboard",
    label: "Tableau de bord",
    roles: [ROLE.ADMIN, ROLE.INGENIEUR, ROLE.TECHNICIEN],
  },
  {
    to:    "/map",
    label: "Carte réseau",
    roles: [ROLE.ADMIN, ROLE.INGENIEUR, ROLE.TECHNICIEN],
  },
  {
    to:    "/equipments",
    label: "Antennes",
    roles: [ROLE.ADMIN, ROLE.INGENIEUR, ROLE.TECHNICIEN],
  },
  {
    to:    "/moderation",
    label: "Incidents",
    roles: [ROLE.ADMIN, ROLE.TECHNICIEN],
  },
  {
    to:    "/rapports",
    label: "Rapports",
    roles: [ROLE.ADMIN, ROLE.INGENIEUR],
  },
  {
    to:    "/administration",
    label: "Administration",
    roles: [ROLE.ADMIN],
  },
];

// =============================================================
// navForRole(role)
// Retourne uniquement les liens accessibles pour un rôle donné.
// =============================================================
export function navForRole(role) {
  if (!role) return [];
  return MENU_NAVIGATION.filter((lien) => lien.roles.includes(role));
}

// =============================================================
// hasRole(roleUtilisateur, rolesAutorises)
// =============================================================
export function hasRole(roleUtilisateur, rolesAutorises) {
  return roleUtilisateur && rolesAutorises.includes(roleUtilisateur);
}
