import { Panel } from "../../components/Panel";
import type { PredictionResponse, RequestState } from "../../types/api";

type MapPanelProps = {
  requestState: RequestState;
  result: PredictionResponse | null;
};

export function MapPanel({ requestState, result }: MapPanelProps) {
  const origin = result?.map.origin
  const destination = result?.map.destination
  const hasMapData = origin !== undefined && destination !== undefined

  return (
    <Panel className="flex h-full min-h-[26rem] flex-col">
      <div className="mb-5 flex items-center justify-between gap-3">
        <div className="space-y-2">
          <p className="text-sm uppercase tracking-[0.24em] text-[var(--color-accent-soft)]">
            Route Map
          </p>
          <h2 className="text-2xl font-semibold text-white">
            Reserved for route visualization.
          </h2>
        </div>
        <span className="rounded-full border border-white/10 bg-white/6 px-3 py-1 text-xs uppercase tracking-[0.18em] text-[var(--color-mist)]">
          Future Leaflet panel
        </span>
      </div>

      <div className="relative flex flex-1 items-center justify-center overflow-hidden rounded-[1.5rem] border border-dashed border-white/10 bg-[linear-gradient(180deg,rgba(255,255,255,0.04),rgba(255,255,255,0.02))] p-6">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(255,184,77,0.12),transparent_22%),radial-gradient(circle_at_80%_70%,rgba(77,208,164,0.14),transparent_20%)]" />
        <div className="absolute inset-x-10 top-1/2 h-px bg-gradient-to-r from-transparent via-white/12 to-transparent" />
        <div className="absolute left-[20%] top-[34%] h-3.5 w-3.5 rounded-full border-4 border-[var(--color-accent)] bg-[var(--color-paper)] shadow-[0_0_18px_rgba(255,184,77,0.45)]" />
        <div className="absolute right-[22%] bottom-[28%] h-3.5 w-3.5 rounded-full border-4 border-[var(--color-good)] bg-[var(--color-paper)] shadow-[0_0_18px_rgba(77,208,164,0.45)]" />

        <div className="relative z-10 max-w-md rounded-[1.5rem] border border-white/10 bg-[rgba(9,17,29,0.78)] p-5 text-center backdrop-blur-sm">
          <p className="text-sm uppercase tracking-[0.24em] text-[var(--color-accent-soft)]">
            Map Placeholder
          </p>
          <h3 className="mt-3 text-xl font-semibold text-white">
            {hasMapData
              ? `${origin.code} to ${destination.code}`
              : "Origin and destination markers will render here"}
          </h3>
          <p className="mt-3 text-sm leading-6 text-[var(--color-mist)]">
            Plan to replace this panel with <code>react-leaflet</code> and
            OpenStreetMap tiles once the backend returns stable route metadata.
          </p>
          <p className="mt-4 text-xs uppercase tracking-[0.18em] text-[var(--color-mist)]">
            State: {requestState}
          </p>
        </div>
      </div>
    </Panel>
  );
}
