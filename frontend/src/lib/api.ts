import type { FlightLookupRequest, PredictionResponse } from "../types/api";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.trim() || "http://localhost:8000";
const PREDICTION_ENDPOINT =
  import.meta.env.VITE_PREDICTION_ENDPOINT?.trim() || "/predict";

export async function fetchPrediction(
  payload: FlightLookupRequest,
): Promise<PredictionResponse> {
  const response = await fetch(`${API_BASE_URL}${PREDICTION_ENDPOINT}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Prediction request failed with status ${response.status}.`);
  }

  return (await response.json()) as PredictionResponse;
}
