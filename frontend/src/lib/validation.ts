export const MAX_PASSWORD_BYTES = 72;
export const MIN_PASSWORD_LENGTH = 8;

/** Mirrors the API rules. bcrypt only uses 72 bytes, and emoji or accents use more than one byte. */
export function passwordProblem(password: string): string | null {
  if (password.length < MIN_PASSWORD_LENGTH) return `Use at least ${MIN_PASSWORD_LENGTH} characters.`;
  if (!password.trim()) return "Password cannot be only spaces.";
  if (new TextEncoder().encode(password).length > MAX_PASSWORD_BYTES) {
    return `Password is too long: at most ${MAX_PASSWORD_BYTES} bytes (emoji and non-Latin letters use several bytes each).`;
  }
  return null;
}

export function emailProblem(email: string): string | null {
  const value = email.trim();
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) return "Enter a valid email address.";
  return null;
}
