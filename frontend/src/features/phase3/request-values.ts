// Display/filter compatibility never rewrites stored Request values.
export const requestPriorities = ["Low", "Normal", "High", "Urgent"];
export const requestStatuses = ["Open", "In Progress", "Resolved", "Closed", "Cancelled"];
export function requestValue(value: unknown, choices: string[]) {
  const raw = String(value ?? "");
  return choices.find(choice => choice.toLowerCase() === raw.toLowerCase()) ?? raw;
}
