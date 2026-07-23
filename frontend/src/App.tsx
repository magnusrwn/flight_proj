import { useState } from "react";
import { FlightLookupForm } from "./features/flight-lookup/FlightLookupForm";
import { MapPanel } from "./features/map-panel/MapPanel";
import { PredictionResult } from "./features/prediction-result/PredictionResult";
import { fetchPrediction } from "./lib/api";
import type {
  FlightLookupRequest,
  PredictionResponse,
  RequestState,
} from "./types/api";

const summaryItems = [
  "Historical BTS flight performance",
  "Weather-enriched route context",
  "Prediction-ready backend contract",
];

export default function App() {
  const [requestState, setRequestState] = useState<RequestState>("idle");
  const [result, setResult] = useState<PredictionResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function handleLookup(payload: FlightLookupRequest) {
    setRequestState("loading");
    setErrorMessage(null);

    try {
      const response = await fetchPrediction(payload);
      setResult(response);
      setRequestState("success");
    } catch (error) {
      setResult(null);
      setRequestState("error");
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "The prediction request failed.",
      );
    }
  }

  return (
    <div className="min-h-screen bg-[var(--color-ink)] text-[var(--color-paper)]">
      <div className="mx-auto flex min-h-screen max-w-7xl flex-col px-6 py-8 sm:px-8 lg:px-10">
        <header className="relative overflow-hidden rounded-[2rem] border border-white/10 bg-[radial-gradient(circle_at_top_left,_rgba(255,184,77,0.22),_transparent_35%),linear-gradient(135deg,rgba(13,27,42,0.96),rgba(28,37,65,0.96))] p-8 shadow-[0_24px_90px_rgba(0,0,0,0.34)] sm:p-10">
          <div className="absolute -right-18 top-0 h-40 w-40 rounded-full bg-[rgba(251,133,0,0.18)] blur-3xl" />
          <div className="absolute bottom-0 left-1/3 h-28 w-28 rounded-full bg-[rgba(77,144,142,0.18)] blur-3xl" />
          <div className="relative grid gap-8 lg:grid-cols-[1.5fr_0.9fr]">
            <div className="space-y-5">
              <p className="text-sm uppercase tracking-[0.32em] text-[var(--color-accent-soft)]">
                Storm Project
              </p>
              <div className="space-y-3">
                <h1 className="max-w-3xl text-4xl font-semibold tracking-tight text-white sm:text-5xl">
                  Predict domestic U.S. flight disruption from one lookup.
                </h1>
                <p className="max-w-2xl text-base leading-7 text-[var(--color-mist)] sm:text-lg">
                  Single-page interface for flight delay prediction, route
                  context, and a future map view anchored to the backend model.
                </p>
              </div>
            </div>

            <div className="grid gap-3 self-end rounded-[1.75rem] border border-white/10 bg-white/6 p-5 backdrop-blur-sm">
              {summaryItems.map((item) => (
                <div
                  key={item}
                  className="flex items-center gap-3 rounded-2xl border border-white/8 bg-black/10 px-4 py-3"
                >
                  <span className="h-2.5 w-2.5 rounded-full bg-[var(--color-accent)]" />
                  <span className="text-sm text-[var(--color-paper)]">
                    {item}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </header>

        <main className="mt-8 grid flex-1 gap-6 lg:grid-cols-[0.9fr_1.1fr]">
          <section className="space-y-6">
            <FlightLookupForm
              isLoading={requestState === "loading"}
              onSubmit={handleLookup}
            />
            <PredictionResult
              errorMessage={errorMessage}
              requestState={requestState}
              result={result}
            />
          </section>

          <section className="h-full">
            <MapPanel requestState={requestState} result={result} />
          </section>
        </main>
      </div>
    </div>
  );
}
