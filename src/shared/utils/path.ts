export function isValidPathFormat(value: string): boolean {
  const v = value.trim();
  if (!v) return true;

  const uncPath = /^\\\\[^\\]+\\[^\\]+/;
  const drivePath = /^[a-zA-Z]:[\\/]/;
  const unixAbsolute = /^\//;

  return uncPath.test(v) || drivePath.test(v) || unixAbsolute.test(v);
}
