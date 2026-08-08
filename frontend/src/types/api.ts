export type RequestState = "idle" | "loading" | "success" | "error";

export type FlightPredRequest = {
  flightNumber:string;
  date: string; // check this
  depIataCode: string;
  destIataCode: string;
};

// Validate use
// export type PredictionCard = {
//   label: string;
//   value: string;
//   helper: string;
// };

export type AirportMapPoint = {
  originCode: string;
  destCode: string;
  originLat: number;
  originLong: number;
};

// Mock -- Base nothing from this
export type PredictionResponse = {
  // lookup: {
  //   flightCode: string;
  //   carrier?: string;
  // };
  // route: {
  //   originNameLabel: string;
  //   destinationNameLabel: string;
  // };
  // // predictionCards: PredictionCard[];
  // // explanations: {
  // //   weatherSummary?: string;
  // //   featureSummary?: string;
  // // };
  // map: {
  //   origin?: AirportMapPoint;
  //   destination?: AirportMapPoint;
  // };
};
