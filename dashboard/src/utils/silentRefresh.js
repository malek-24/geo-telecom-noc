/**
 * Met à jour une liste d'objets par id sans recréer les références inchangées (limite le clignotement).
 */
export function mergeById(prev, next, idKey = 'id') {
  if (!Array.isArray(next)) return prev;
  if (!prev?.length) return next;

  const nextMap = new Map(next.map(item => [item[idKey], item]));
  const merged = prev.map(item => nextMap.get(item[idKey]) ?? item);

  next.forEach(item => {
    if (!merged.some(m => m[idKey] === item[idKey])) merged.push(item);
  });

  return merged;
}
