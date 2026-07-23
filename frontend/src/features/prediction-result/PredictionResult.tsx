import { Panel } from "../../components/Panel";
import type { PredictionResponse, RequestState } from "../../types/api";

type PredictionResultProps = {
  errorMessage: string | null;
  requestState: RequestState;
  result: PredictionResponse | null;
};

const idleCards = [
  {
    label: "Delay risk",
    value: "--",
    helper: "Primary classification or risk score",
  },
  {
    label: "Expected minutes",
    value: "--",
    helper: "Predicted arrival or departure delay",
  },
  {
    label: "Confidence",
    value: "--",
    helper: "Model confidence or calibrated band",
  },
];

export function PredictionResult({
  errorMessage,
  requestState,
  result,
}: PredictionResultProps) {
  const cards =
    result?.predictionCards.length && requestState === "success"
      ? result.predictionCards
      : idleCards;

  return (
    <Panel>
      <div className="mb-5 flex items-start justify-between gap-4">
        <div className="space-y-2">
          <p className="text-sm uppercase tracking-[0.24em] text-[var(--color-accent-soft)]">
            Prediction Output
          </p>
          <h2 className="text-2xl font-semibold text-white">
            Result area for backend model output.
          </h2>
        </div>
        <span className="rounded-full border border-white/10 bg-white/6 px-3 py-1 text-xs uppercase tracking-[0.18em] text-[var(--color-mist)]">
          {requestState}
        </span>
      </div>

      {requestState === "error" ? (
        <div className="mb-5 rounded-2xl border border-[rgba(255,123,123,0.25)] bg-[rgba(255,123,123,0.08)] px-4 py-3 text-sm text-[var(--color-paper)]">
          {errorMessage}
        </div>
      ) : null}

      <div className="grid gap-4 md:grid-cols-3">
        {cards.map((card) => (
          <div
            key={card.label}
            className="rounded-[1.5rem] border border-white/10 bg-white/5 p-4"
          >
            <p className="text-sm text-[var(--color-mist)]">{card.label}</p>
            <p className="mt-3 text-3xl font-semibold text-white">
              {card.value}
            </p>
            <p className="mt-4 text-sm leading-6 text-[var(--color-mist)]">
              {card.helper}
            </p>
          </div>
        ))}
      </div>

      <div className="mt-5 grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="rounded-[1.5rem] border border-white/10 bg-black/15 p-4">
          <p className="text-sm font-medium text-[var(--color-paper)]">
            Route and lookup summary
          </p>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <SummaryRow
              label="Flight"
              value={result?.lookup.flightCode ?? "Pending backend contract"}
            />
            <SummaryRow
              label="Carrier"
              value={result?.lookup.carrier ?? "Pending backend contract"}
            />
            <SummaryRow
              label="Origin"
              value={result?.route.originLabel ?? "Pending backend contract"}
            />
            <SummaryRow
              label="Destination"
              value={result?.route.destinationLabel ?? "Pending backend contract"}
            />
          </div>
        </div>

        <div className="rounded-[1.5rem] border border-white/10 bg-black/15 p-4">
          <p className="text-sm font-medium text-[var(--color-paper)]">
            Model notes
          </p>
          <div className="mt-4 space-y-3">
            <DetailPill
              label="Weather summary"
              value={result?.explanations.weatherSummary ?? "Reserved field"}
            />
            <DetailPill
              label="Feature highlights"
              value={result?.explanations.featureSummary ?? "Reserved field"}
            />
          </div>
        </div>
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

function DetailPill({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-white/8 bg-white/4 px-3 py-3">
      <p className="text-xs uppercase tracking-[0.18em] text-[var(--color-mist)]">
        {label}
      </p>
      <p className="mt-2 text-sm leading-6 text-white">{value}</p>
    </div>
  );
}
