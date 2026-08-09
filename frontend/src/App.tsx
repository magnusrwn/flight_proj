import { useState } from "react";
import { FlightLookupForm } from "./features/flight-lookup/FlightLookupForm";
import { PredictionResult } from "./features/prediction-result/PredictionResult";
import { fetchPrediction } from "./lib/api";
import type {
  FlightPredRequest,
  FlightPredResponse,
  RequestState,
} from "./types/api";

export default function App() {
  const [requestState, setRequestState] = useState<RequestState>("idle");
  const [result, setResult] = useState<FlightPredResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const rawResponseJson =
    requestState === "success" && result ? JSON.stringify(result, null, 2) : null;

  async function handleLookup(payload: FlightPredRequest) {
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
        mx-auto  max-w-7xl
        px-6 py-8 my-10 sm:px-8 lg:px-10
        rounded-sm"
      >
        <div className="
         space-x-5
         space-y-5
         mb-5
         h-fit

         xl:h-90
         xl:mb-10
         xl:flex
        ">
          <header className="
            overflow-hidden
            rounded-2xl
            p-8
            sm:p-10
            h-full w-full

            border-4
          ">
            <div className="gap-8 lg:grid-cols-[1.5fr_0.9fr]">
              <div className="w-auto">
                  <h1 className="text-2xl text-white sm:text-5xl pb-2 underline underline-offset-4 decoration-3">
                    Predict domestic U.S. flight disruption from one lookup.
                  </h1>
                </div>
            </div>
          </header>
          
          <FlightLookupForm
            isLoading={requestState === "loading"}
            onSubmit={handleLookup}
          />
        </div>

        <section className="space-y-6">
          <PredictionResult
            errorMessage={errorMessage}
            requestState={requestState}
            result={result}
          />
        </section>

        {rawResponseJson ? (
          <section className="mt-5 rounded-2xl border border-white/10 bg-black/30 p-4">
            <p className="mb-3 text-sm font-medium text-[var(--color-mist)]">
              Raw response
            </p>
            <pre className="max-h-96 overflow-auto whitespace-pre-wrap break-words rounded-xl bg-black/35 p-4 text-xs leading-5 text-[var(--color-paper)]">
              <code>{rawResponseJson}</code>
            </pre>
          </section>
        ) : null}

      </div>
    </div>
  );
}
