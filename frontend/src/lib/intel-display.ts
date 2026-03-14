type IntelDisplaySource = {
  title?: string | null;
  raw_input: string;
};

export function getIntelDisplayTitle(
  intel: IntelDisplaySource,
  maxLength?: number,
): string {
  const base = (intel.title || intel.raw_input).replace(/\s+/g, " ").trim();
  if (!maxLength || base.length <= maxLength) {
    return base;
  }
  return `${base.slice(0, maxLength)}…`;
}
