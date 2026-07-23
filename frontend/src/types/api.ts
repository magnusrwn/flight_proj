export type RequestState = "idle" | "loading" | "success" | "error";

export type FlightLookupRequest = {
  flightCode: string;
};

export type PredictionCard = {
  label: string;
  value: string;
  helper: string;
};

export type AirportMapPoint = {
  code: string;
  latitude?: number;
  longitude?: number;
};

export type PredictionResponse = {
  lookup: {
    flightCode: string;
    carrier?: string;
  };
  route: {
    originLabel: string;
    destinationLabel: string;
  };
  predictionCards: PredictionCard[];
  explanations: {
    weatherSummary?: string;
    featureSummary?: string;
  };
  map: {
    origin?: AirportMapPoint;
    destination?: AirportMapPoint;
  };
};
