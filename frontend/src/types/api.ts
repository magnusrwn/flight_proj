export type RequestState = "idle" | "loading" | "success" | "error";

export type FlightPredRequest = {
  flightNumber:string;
  date: string;
  depIataCode: string;
  destIataCode: string;
};



// Mock -- Base nothing from this
export type FlightPredResponse = {
  is_significant_delay: boolean;
  significant_delay_probability: number | null;

  coordinates: {
    origin_lat: number;
    origin_long: number;
    dest_lat: number;
    dest_long: number;
  },
  distance: {
    fl_distance:number;
  }
  aviationApiData: {
    origin:string;
    origin_city_name: string;
    origin_lat: number;
    origin_long: number;
    
    dest: string;
    dest_city_name: string;
    dest_lat: number;
    dest_long: number;

    flight_date: string;
    day_of_month: number;
    day_of_week: number;
    pred_dep_time: number;
    pred_arr_time: number;
    pred_elapsed_time: number;
    year: number;
    month: number;
  }
};
