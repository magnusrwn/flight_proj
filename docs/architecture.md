# Architecture

## Overview

This repo is essentially a full-stack ML project. It combines multiple data srouces, creates pipelines for that data, trains a model on it, and then integrates APIs for the service of that predictive model.

It is important to understand that this is not a produciton full stack app. Its primary purpouse was to get me back upto scratch with literal typed code creation after a little break, learn a few new technologies, and imorove on existing ones. **Thus... This is meant to be run locally,** however, that does not mean that care has not been taken, or that algos are inneficient, or that testing wsa skiped out on... those things are still implemented.

---

## Goals and Non-Goals

This is a significant delay predictor. It takes basic input of date, departure, destination, and time of departure and outputs a prediction on weather the flight will be significantly delayed. (As well as a raw resposne area for general data on the flight itself)

This is not a looker. It's mainly, as prior stated, to refresh the core ideas of full-stack aps, scikitlearn, decently efficient algos creation, datacleaning, and error handeling/ responses, etc...

The depth of the data used was not great, as stated in  `docs/ml.md`, however the prediction has proven some utility.

It should also be noted that the speed of the prediction is deeply slow. This is mainly due to the Aviation Stack API, which is both very slow on request, and incredibly slow on its site -- not to meantion the req/response(s). I'm affraid I can not fully recommend this API.

---

## DuckDB Context

**DuckBD stores all data of this project. This decision was made because:**
- Using CSV's with pandas for xmillion rows is a RAM nightmare
- Creating a local databse is a little annoying, and makes it harder to share as a project
- I got $100+ a month quotes from AWS to host a bare-bones databse

DuckDB has been amazing, and entirely fits the requirements/ goals of this project

---

## Runtime Flow

**Successfull backend service flow:**
Request at `/predict` -> Ensure handed airport codes exist in my dataset -> Send flight data API request to Aviation Stack API -> Match response of flights to the flight you requested -> Build flight data to match training dataset -> Match vars needed for Open-Meteo API -> Calculate flight distance from coords -> Open-Meteo API request -> Type check data against training data base model -> Predict -> Package and respond

---

## Frontend Architecture

Frontend is a basic TS + React + Tailwind app. It is only responsible for sending the fech request, and type checking the request/ form input before sending the request.

This is it.

As it is just meant to be run locally on this itteration of the project, there is no need for anything else.

### App Structure

Frontend structire is very standard with no suprises. `App.tsx` holds the page, components are in `/components`, contracts are in `/types`, components are in `/components`. Nithing is suprising, everything says what it does on the tin.


### Components

Reusable logic is stored in `backend/src/utils.py`. Althoguh, as a unique service application, it has few reused things -- the best example would be the `request_with_retry` function.


### Types

- **Backend:** All types exist as `Pydantic BaseModel(s)`. These live in `backend/src/models/base_models.py`
- **Frontend:** All frontend contracts live in `frontend/src/types/api.ts`

### Styling

- Minimal style classes exist in `frontend/src/index.css`
- Most styles are Tailwind, and thus in components/ App.tsx directly.
---

## Routes

This project has 2 routes:

**`/haelth`**: Returns: {"status":"ok"}

*and*

**`/predict`**: Returning the base model `FuncResponse`. For more detals on the payload see [here](https://github.com/magnusrwn/flight_proj/blob/main/docs/api.md) with Ctrl/Cmnd + f: 'Response Contract'

---

## Logging
- Logging is configured in `backend/src/logger_config.py` and outputs to `backend/logs`. These are excluded from git tracing, and thus not visable in the repo.
- Logging occurs in FILL HERE AND CHECK

---

## Environment Configuration

Env config is explained [here](https://github.com/magnusrwn/flight_proj/blob/main/README.md). Use Ctrl/ Cmnd + f: '.env Configuration'

---

## Error Handling

All errors are handled the same. All responses are the same:
- Responses fllow `FuncResponse` base model. Here, the main field being 'ok' will be set to false in the case of error.
- Additional information will be handed in optional fields. This means status codes, error data packages, and error messages are all passed to the fronetned in a uniform way. It is simple, and it is quick, and fits exactly the needs of this project.

HTTP errors are caught and hendled in the frontend

---

## Deployment

**Backend:**
- [start in project root]
- Run: `cd backend`
- Run: `uv sync`
- Run: `uv run uvicorn src.main:app --reload` *or* `uvicorn src.main:app --reload`

**Frontend:**
- [start in project root]
- Run: `cd frontend`
- Run: `npm i`
- Run: `npm run dev`
---
## CORS
- Cors are setup on this app. Located in `backend/src/main.py`
- It permits requests from `http://localhost:5173`, which is the address of the localy hosted Vite app

---

## Performance Considerations

Again, I must mention the service is slow. This is due to the Aviation Stack API response, and mainly, its response speed.

As well as this, it should be repeated that I do not recommend training the models with the pre-made pipeline(s).

If you are to train one arround the data I've prepped in the pipeline, you should do it on a remote computer. In this peoject I used AWS's EC2.

---

## Known Limitations

- Dates: The Aviation Stack API allows for some dates at some periods of the future... not all of them. Yes, I know thats vague, and yes I know it sucks, but I paid for my subscription already, and thus this project is built on it
- Flights: The Aviation Stack API misses popular flights. This was made apparent when it did not have a flight I was going to take in the near future at the time of developing/ testing this app. So, dont plame my project, blame the API.

In all seriousness thoguh, the API is not horrific, however it was *greatly* dissapointing. One major itteration of this project would be to itterate away from this API, and to another.

Todos for this project will be kept [here](https://github.com/magnusrwn/flight_proj)