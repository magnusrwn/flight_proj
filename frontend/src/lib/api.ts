import type { FlightPredRequest, FlightPredResponse } from "../types/api";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.trim() || "http://localhost:8000";
const PREDICTION_ENDPOINT =
  import.meta.env.VITE_PREDICTION_ENDPOINT?.trim() || "/predict";

// Just one request from the frontend for the whole app
export async function fetchPrediction(
  payload: FlightPredRequest,
): Promise<FlightPredResponse> {
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

  return (await response.json()) as FlightPredResponse;
}
