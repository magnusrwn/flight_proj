import { type FormEvent, useState } from "react";
import { Panel } from "../../components/Panel";
import type { FlightPredRequest } from "../../types/api";

type FlightLookupFormProps = {
  isLoading: boolean;
  onSubmit: (payload: FlightPredRequest) => Promise<void>;
};

type FormErrors = {
  depAirport?:string;
  arrAirport?:string;
  depDate?:string;
  scheduledDepartureTime?:string;
}

function isDateString(date:string):boolean{
  const pattern = /^\d{4}-\d{2}-\d{2}$/; // '^' = start of string, '$' end of string, '/', '/' enclose
  return pattern.test(date);
}

function isTimeString(time:string):boolean{
  const pattern = /^\d{2}:\d{2}$/;
  return pattern.test(time);
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
  const [depAirport, setDepAirport] = useState("");
  const [arrAirport, setArrAirport] = useState("");
  const [depDate, setDepDate] = useState("");
  const [scheduledDepartureTime, setScheduledDepartureTime] = useState("");
  const [errors, setErrors] = useState<FormErrors>({})
  
  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    
    const nextErrors: FormErrors = {};
    const trimmedDepAiport = depAirport.trim().toUpperCase();
    const trimmedArrAirport = arrAirport.trim().toUpperCase()
    const trimmedDepDate = depDate.trim()
    const trimmedScheduledDepartureTime = scheduledDepartureTime.trim()

    if (!trimmedDepAiport || trimmedDepAiport.length !== 3){
      nextErrors.depAirport = "Departure airport is required"
    };

    if (!trimmedArrAirport || trimmedArrAirport.length !== 3){
      nextErrors.arrAirport = "Arrival airport is required"
    };

    if (!trimmedDepDate){
      nextErrors.depDate = "Departure date is required"
    } else if (!isDateString(trimmedDepDate)){
      nextErrors.depDate = "Use format YYYY-MM-DD"
    };

    if (!trimmedScheduledDepartureTime){
      nextErrors.scheduledDepartureTime = "Scheduled departure time is required"
    } else if (!isTimeString(trimmedScheduledDepartureTime)){
      nextErrors.scheduledDepartureTime = "Use format HH:MM"
    };
    
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0){
      return;
    }

    await onSubmit({
      date: trimmedDepDate,
      scheduledDepartureTime: trimmedScheduledDepartureTime,
      depIataCode: trimmedDepAiport,
      destIataCode: trimmedArrAirport,
    });
  }

  return (
    // get a transition
    <Panel className="
     max-h-[80vh] overflow-y-auto sm:px-8 lg:px-10
    ">
      <div className=" gap-4">
          <h2 className="text-2xl  text-white">
            Search for flight
          </h2>
      </div>

      <form className="space-y-4" onSubmit={handleSubmit}>
        
        <label className="block space-y-2">
          <span className={errorClassName(Boolean(errors.depDate))}>
            Departure date
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

        <label className="block space-y-2">
          <span className={errorClassName(Boolean(errors.scheduledDepartureTime))}>
            Scheduled departure
          </span>
          <input
            aria-invalid={Boolean(errors.scheduledDepartureTime)}
            className={inputClassName(Boolean(errors.scheduledDepartureTime))}
            step={60}
            type="time"
            value={scheduledDepartureTime}
            onChange={(event) => setScheduledDepartureTime(event.target.value)}
          />
          {errors.scheduledDepartureTime && (
            <p className="text-sm text-red-300">{errors.scheduledDepartureTime}</p>
          )}
        </label>

        <fieldset className="space-y-2">
          <legend className={errorClassName(Boolean(errors.depAirport || errors.arrAirport))}>
            Airports
          </legend>
          <div className="grid grid-cols-2 gap-x-4">
            <div className="space-y-2">
              <label
                className={errorClassName(Boolean(errors.depAirport))}
                htmlFor="departure-airport"
              >
                Departure
              </label>
              <input
                aria-invalid={Boolean(errors.depAirport)}
                className={inputClassName(Boolean(errors.depAirport))}
                id="departure-airport"
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
              <label
                className={errorClassName(Boolean(errors.arrAirport))}
                htmlFor="arrival-airport"
              >
                Arrival
              </label>
              <input
                aria-invalid={Boolean(errors.arrAirport)}
                className={inputClassName(Boolean(errors.arrAirport))}
                id="arrival-airport"
                placeholder="LAX"
                type="text"
                value={arrAirport}
                onChange={(event) => setArrAirport(event.target.value)}
              />
              {errors.arrAirport && (
                <p className="text-sm text-red-300">{errors.arrAirport}</p>
              )}
            </div>
          </div>
        </fieldset>
          
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
