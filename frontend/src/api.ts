export type Health = { status: "ok" | "degraded"; database: "connected" | "unavailable" };

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function getHealth(): Promise<Health> {
  const response = await fetch(`${apiBaseUrl}/api/health`);
  if (!response.ok) throw new Error(`API responded with ${response.status}`);
  return response.json() as Promise<Health>;
}
