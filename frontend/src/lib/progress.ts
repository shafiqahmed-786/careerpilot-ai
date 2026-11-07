export function completionPercent(completed: number, total: number): number {
  if (total <= 0) return 0;
  return Math.round((completed * 100) / total);
}

export function statusLabel(status: string): string {
  if (status === "missing") return "Not reported";
  if (status === "improve") return "Below target";
  if (status === "sufficient") return "Meets target";
  if (status === "in_progress") return "In progress";
  if (status === "completed") return "Completed";
  if (status === "pending") return "Pending";
  return status;
}
