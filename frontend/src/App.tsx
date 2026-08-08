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
    <div className="min-h-screen">
      <div className="
        xl:border
        mx-auto min-h-screen max-w-7xl
        px-6 py-8 my-10 sm:px-8 lg:px-10
        rounded-sm"
      >
        <div className="
         space-x-5
         h-90
         grid
         grid-rows-2
         grid-cols-1
         gap-y-10
        
         xl:mb-10
         xl:flex
        ">
          <header className="
            overflow-hidden
            rounded-2xl
            border
            p-8
            sm:p-10
            h-full w-full
            xl:
          ">
            <div className="relative grid gap-8 lg:grid-cols-[1.5fr_0.9fr]">
              <div>
                  <h1 className="text-2xl text-white sm:text-5xl pb-2 underline underline-offset-4 decoration-2">
                    Predict domestic U.S. flight disruption from one lookup.
                  </h1>
                  <p className="text-base leading-7 text-[var(--color-mist)] sm:text-lg">
                    Single-page interface for flight delay prediction, route
                    context, and a future map view anchored to the backend model.
                  </p>
                </div>
            </div>
          </header>
          
          <FlightLookupForm
            isLoading={requestState === "loading"}
            onSubmit={handleLookup}
          />
        </div>

        <section className="h-full">
          <MapPanel requestState={requestState} result={result} />
        </section>
        
        <section className="space-y-6">
          <PredictionResult
            errorMessage={errorMessage}
            requestState={requestState}
            result={result}
          />
        </section>

      </div>
    </div>
  );
}
