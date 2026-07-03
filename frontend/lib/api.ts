import { Params, AnalyseResult } from "./types";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function analyser(params: Params): Promise<AnalyseResult> {
  const res = await fetch(`${API}/api/analyse`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}
