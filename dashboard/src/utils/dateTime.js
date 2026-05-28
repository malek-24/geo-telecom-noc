/**
 * Affichage des dates en fuseau horaire Tunisie (Africa/Tunis, UTC+1).
 */
const TZ = 'Africa/Tunis';

/** Parse une date renvoyée par l'API (ISO avec +01:00 ou suffixe Z). */
export function parseServerDate(value) {
  if (value == null || value === '') return null;
  if (value instanceof Date) return value;
  let s = String(value).trim();
  if (!s) return null;
  if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}/.test(s)) {
    s = s.replace(' ', 'T');
  }
  if (!/[Zz+\-]\d{2}/.test(s) && !s.endsWith('Z')) {
    s = `${s}+01:00`;
  }
  const d = new Date(s);
  return Number.isNaN(d.getTime()) ? null : d;
}

/** Date + heure (ex. 26/05/2026 14:30). */
export function formatDateTimeTN(value, options = {}) {
  const d = parseServerDate(value);
  if (!d) return '—';
  const { date = true, time = true } = options;
  const fmt = {};
  if (date) {
    fmt.day = '2-digit';
    fmt.month = '2-digit';
    fmt.year = 'numeric';
  }
  if (time) {
    fmt.hour = '2-digit';
    fmt.minute = '2-digit';
  }
  return new Intl.DateTimeFormat('fr-TN', { timeZone: TZ, ...fmt }).format(d);
}

/** Heure seule (ex. 14:30). */
export function formatTimeTN(value) {
  return formatDateTimeTN(value, { date: false, time: true });
}

/** Date seule. */
export function formatDateTN(value) {
  return formatDateTimeTN(value, { date: true, time: false });
}
