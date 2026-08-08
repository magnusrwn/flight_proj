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
    <Panel className="overflow-hidden sm:px-8 lg:px-10">
      <div className=" gap-4">
          <h2 className="text-2xl  text-white">
            Search for flight
          </h2>
      </div>

      <form className="space-y-4" onSubmit={handleSubmit}>

        <label className="block space-y-2">
          <span className="text-sm font-medium">
            Flight code
          </span>
          <input
            className="w-full rounded-2xl border border-white/10  px-4 py-3 text-base text-white outline-none transition placeholder:text-slate-500"
            placeholder="AA100, DL2451, UA818"
            value={flightCode}
            onChange={(event) => setFlightCode(event.target.value)}
          />
        </label>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <button
            className="inline-flex min-w-40 items-center justify-center rounded-2xl px-5 py-3 text-sm  text-slate-950 transition hover:brightness-105 disabled:cursor-not-allowed disabled:opacity-60"
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
