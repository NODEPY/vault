export function originOf(value) {
  const url = new URL(value);
  if (url.port === '0' || url.protocol !== 'https:' || url.username || url.password) throw new Error('Open an HTTPS website.');
  return url.origin;
}
export function hostPattern(origin) { return `${new URL(origin).protocol}//${new URL(origin).hostname}/*`; }
export function validCandidate(value) {
  return value && typeof value.username === 'string' && typeof value.password === 'string' && value.password.length > 0 && value.password.length <= 4096 && value.username.length <= 4096;
}
