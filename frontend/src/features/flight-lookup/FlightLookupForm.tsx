import { type FormEvent, useState } from "react";
import { Panel } from "../../components/Panel";
import type { FlightLookupRequest } from "../../types/api";

type FlightLookupFormProps = {
  isLoading: boolean;
  onSubmit: (payload: FlightLookupRequest) => Promise<void>;
};

export function FlightLookupForm({
  isLoading,
  onSubmit,
}: FlightLookupFormProps) {
  const [flightCode, setFlightCode] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = flightCode.trim().toUpperCase();
    if (!trimmed) {
      return;
    }

    await onSubmit({ flightCode: trimmed });
  }

  return (
    <Panel className="overflow-hidden">
      <div className="mb-5 flex items-start justify-between gap-4">
        <div className="space-y-2">
          <p className="text-sm uppercase tracking-[0.24em] text-[var(--color-accent-soft)]">
            Flight Lookup
          </p>
          <h2 className="text-2xl font-semibold text-white">
            Search one domestic flight.
          </h2>
          <p className="max-w-xl text-sm leading-6 text-[var(--color-mist)]">
            Start with a flight code such as carrier plus number. This scaffold
            assumes the backend will resolve the route, weather context, and
            model inputs.
          </p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/5 px-3 py-2 text-right text-xs text-[var(--color-mist)]">
          <div>Backend-owned contract</div>
          <div>Prediction flow only</div>
        </div>
      </div>

      <form className="space-y-4" onSubmit={handleSubmit}>
        <label className="block space-y-2">
          <span className="text-sm font-medium text-[var(--color-paper)]">
            Flight code
          </span>
          <input
            className="w-full rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-base text-white outline-none transition placeholder:text-slate-500 focus:border-[var(--color-accent)] focus:ring-2 focus:ring-[rgba(255,184,77,0.16)]"
            placeholder="AA100, DL2451, UA818"
            value={flightCode}
            onChange={(event) => setFlightCode(event.target.value)}
          />
        </label>

        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm leading-6 text-[var(--color-mist)]">
            The first version is intentionally narrow: one lookup, one result
            state, one route map area.
          </p>
          <button
            className="inline-flex min-w-40 items-center justify-center rounded-2xl bg-[var(--color-accent)] px-5 py-3 text-sm font-semibold text-slate-950 transition hover:brightness-105 disabled:cursor-not-allowed disabled:opacity-60"
            disabled={isLoading}
            type="submit"
          >
            {isLoading ? "Running lookup..." : "Get prediction"}
          </button>
        </div>
      </form>
    </Panel>
  );
}
