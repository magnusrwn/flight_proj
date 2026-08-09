import { Panel } from "../../components/Panel";
import type { FlightPredResponse, RequestState } from "../../types/api";

type PredictionResultProps = {
  errorMessage: string | null;
  requestState: RequestState;
  result: FlightPredResponse | null;
};

export function PredictionResult({
  errorMessage,
  requestState,
  result,
}: PredictionResultProps) {
  const hasResult = requestState === "success" && result !== null;
  const probability = result?.significant_delay_probability;

  return (
    <Panel>
      <div className="mb-5 flex items-start justify-between gap-4">
        <div className="space-y-2">
          <p className="text-2xl">Output</p>
        </div>
      </div>

      {requestState === "error" ? (
        <div className="mb-5 rounded-2xl border border-[rgba(255,123,123,0.25)] bg-[rgba(255,123,123,0.08)] px-4 py-3 text-sm text-[var(--color-paper)]">
          {errorMessage}
        </div>
      ) : null}
      <div className="relative mt-5 overflow-hidden rounded-2xl">
        <div
          className={`grid gap-3 sm:grid-cols-2 md:grid-cols-3 ${
            hasResult ? "" : "opacity-35 blur-[1px]"
          }`}
        >
          <SummaryRow
            label="Delay Risk"
            value={
              result
                ? result.is_significant_delay
                  ? "Significant"
                  : "Low"
                : "--"
            }
          />
          <SummaryRow
            label="Origin"
            value={result?.aviationApiData.origin ?? "--"}
          />
          <SummaryRow
            label="Destination"
            value={result?.aviationApiData.dest ?? "--"}
          />
          <SummaryRow
            label="Probability"
            value={
              probability === null || probability === undefined
                ? "--"
                : `${Math.round(probability * 100)}%`
            }
          />
          <SummaryRow
            label="Distance"
            value={
              result ? `${Math.round(result.distance.fl_distance)} mi` : "--"
            }
          />
          <SummaryRow
            label="Flight Date"
            value={result?.aviationApiData.flight_date ?? "--"}
          />
        </div>

        {!hasResult ? (
          <div className="absolute inset-0 flex items-center justify-center rounded-2xl border border-white/10 bg-zinc-900/75 px-5 text-center backdrop-blur-sm">
            <p className="max-w-sm text-sm font-medium text-[var(--color-mist)]">
              Output is not available until prediction results come in.
            </p>
          </div>
        ) : null}
      </div>
    </Panel>
  );
}

function SummaryRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-white/8 bg-white/4 px-3 py-3">
      <p className="text-xs uppercase tracking-[0.18em] text-[var(--color-mist)]">
        {label}
      </p>
      <p className="mt-2 text-sm font-medium text-white">{value}</p>
    </div>
  );
}
