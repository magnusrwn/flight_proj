import { type FormEvent, useState } from "react";
import { Panel } from "../../components/Panel";
import type { FlightPredRequest } from "../../types/api";

type FlightLookupFormProps = {
  isLoading: boolean;
  onSubmit: (payload: FlightPredRequest) => Promise<void>;
};

type FormErrors = {
  flightCode?:string;
  depAirport?:string;
  arrAirport?:string;
  depDate?:string;
}

function isDateString(date:string):boolean{
  const pattern = /^\d{4}-\d{2}-\d{2}$/; // '^' = start of string, '$' end of string, '/', '/' enclose
  return pattern.test(date);
}

function inputClassName(hasError:boolean):string {
  const baseClassName = "w-full rounded-2xl border px-4 py-3 text-base text-white outline-none placeholder:text-slate-500 transition-all duration-300";
  return hasError
    ? `${baseClassName} border-red-400 text-red-200 focus:border-red-300`
    : `${baseClassName} border-white/10 focus:border-white/50`;
}

function errorClassName(hasError:boolean):string {
  return hasError ? "text-sm font-medium text-red-300" : "text-sm font-medium";
}

export function FlightLookupForm({
  isLoading,
  onSubmit,
}: FlightLookupFormProps) {
  const [flightCode, setFlightCode] = useState("");
  const [depAirport, setDepAirport] = useState("");
  const [arrAirport, setArrAirprot] = useState("");
  const [depDate, setDepDate] = useState("");
  const [errors, setErrors] = useState<FormErrors>({})
  
  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    
    const nextErrors: FormErrors = {};
    const trimmedFlightCode = flightCode.trim().toUpperCase();
    const trimmedDepAiport = depAirport.trim().toUpperCase();
    const trimmedArrAirport = arrAirport.trim().toUpperCase()
    const trimmedDepDate = depDate.trim().toUpperCase()

    if (!trimmedFlightCode){
      nextErrors.flightCode = "Flight code is required"
    };

    if (!trimmedDepAiport || trimmedArrAirport.length !== 3){
      nextErrors.depAirport = "Daperture airport is required"
    };

    if (!trimmedArrAirport || trimmedArrAirport.length !== 3){
      nextErrors.arrAirport = "Daperture airport is required"
    };

    if (!trimmedDepDate){
      nextErrors.depDate = "Departure date is required"
    } else if (!isDateString(trimmedDepDate)){
      nextErrors.depDate = "Use format YYYY-MM-DD"
    };
    
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0){
      return;
    }

    await onSubmit({
      flightNumber: trimmedFlightCode,
      date: trimmedDepDate,
      depIataCode: trimmedDepAiport,
      destIataCode: trimmedArrAirport,
    });
  }

  return (
    // get a transition
    <Panel className="
     max-h-[80vh] overflow-y-auto sm:px-8 lg:px-10

     hover:shadow-sm
   hover:shadow-amber-50
     hover:border-2
     transition-colors
    ">
      <div className=" gap-4">
          <h2 className="text-2xl  text-white">
            Search for flight
          </h2>
      </div>

      <form className="space-y-4" onSubmit={handleSubmit}>

        <label className="block space-y-2">
          <span className={errorClassName(Boolean(errors.flightCode))}>
            Flight code
          </span>
          <input
            aria-invalid={Boolean(errors.flightCode)}
            className={inputClassName(Boolean(errors.flightCode))}
            placeholder="AA100, DL2451, UA818"
            type="text"
            value={flightCode}
            onChange={(event) => setFlightCode(event.target.value)}
          />
          {errors.flightCode && (
            <p className="text-sm text-red-300">{errors.flightCode}</p>
          )}
        </label>
        
        <label className="block space-y-2">
          <span className={errorClassName(Boolean(errors.depDate))}>
            Departure Airport
          </span>
          <input
            aria-invalid={Boolean(errors.depDate)}
            className={inputClassName(Boolean(errors.depDate))}
            placeholder="YYYY-MM-DD"
            type="text"
            value={depDate}
            onChange={(event) => setDepDate(event.target.value)}
          />
          {errors.depDate && (
            <p className="text-sm text-red-300">{errors.depDate}</p>
          )}
        </label>
        

        <label className="gap-x-5">
          <span className={errorClassName(Boolean(errors.depAirport || errors.arrAirport))}>
            Dates
          </span>
          <div className="grid grid-cols-2 gap-x-4">
            <div className="space-y-2">
              <input
                aria-invalid={Boolean(errors.depAirport)}
                className={inputClassName(Boolean(errors.depAirport))}
                placeholder="PHX"
                type="text"
                value={depAirport}
                onChange={(event) => setDepAirport(event.target.value)}
              />
              {errors.depAirport && (
                <p className="text-sm text-red-300">{errors.depAirport}</p>
              )}
            </div>
            <div className="space-y-2">
              <input
                aria-invalid={Boolean(errors.arrAirport)}
                className={inputClassName(Boolean(errors.arrAirport))}
                placeholder="LAX"
                type="text"
                value={arrAirport}
                onChange={(event) => setArrAirprot(event.target.value)}
              />
              {errors.arrAirport && (
                <p className="text-sm text-red-300">{errors.arrAirport}</p>
              )}
            </div>
          </div>
        </label>
          
        <button
          className="w-full rounded-2xl border border-white/15 bg-white/10 px-5 py-3 mt-4 text-sm font-semibold text-white hover:bg-white/15 active:bg-white/20 active:border-white/25"
          disabled={isLoading}
          type="submit"
        >
          {isLoading ? "Running lookup..." : "Get prediction"}
        </button>

      </form>
    </Panel>
  );
}
