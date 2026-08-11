# Architecture

Use this file as a guided draft. Answer the questions under each heading, then remove or rewrite the questions once the section feels complete.

---

## Overview

- What does this project do in one or two paragraphs?
- Who is the system for: you as the developer, a portfolio reviewer, an end user, or all of these?
- What are the main parts of the system: frontend, backend API, external APIs, DuckDB data, and ML model?
- What is the simplest useful explanation of how a user request becomes a flight delay prediction?
- What should a new developer understand before reading the code?

---

## Goals

- What should the application be able to do reliably?
- What user workflow is most important: entering a flight, fetching schedule/weather data, or displaying a prediction?
- What did you want to learn or demonstrate with this project?
- What quality goals matter most: correctness, explainability, speed, maintainability, testability, or cost?
- How will you know the architecture is good enough for this project?

---

## Non-Goals

- What does this project intentionally not support yet?
- Are you avoiding user accounts, payments, persisted user history, admin tooling, or production-scale infrastructure?
- Are there flight types, countries, airlines, airports, or dates you do not plan to support?
- Are there ML features or deployment features you intentionally left out?
- What would be over-engineering for the current version?

---

## System Context

- What external systems does the app depend on?
- What does the frontend own?
- What does the backend own?
- What does the ML model own?
- What does DuckDB store, and why is it used instead of a larger database?
- What data comes from AviationStack?
- What data comes from Open-Meteo?
- What data comes from static or generated local files?
- Which parts of the system require API keys?

---

## High-Level Diagram

- What boxes should appear in the diagram?
- What direction does data flow between the browser, FastAPI app, AviationStack, Open-Meteo, DuckDB, and model artifact?
- Which parts run at request time?
- Which parts run offline during data preparation or model training?
- Would a Mermaid diagram make this easier to read?
- If using Mermaid, what labels would make the system understandable without reading the code first?

---

## Runtime Flow

- What is the complete request path from clicking submit in the UI to displaying the prediction?
- Which operations happen synchronously during the request?
- Which operations are local lookups versus external API calls?
- Which steps can fail, and how does the user see those failures?
- What intermediate data is created before the model receives input?

---

### Flight Prediction Request

- What fields does the frontend send to `POST /predict`?
- What formats are expected for `date`, `scheduledDepartureTime`, `depIataCode`, and `destIataCode`?
- Where is the request validated?
- Are airport codes normalized to uppercase?
- What happens if the request contains extra fields or malformed data?

### Aviation Data Lookup

- Why does the backend call AviationStack before prediction?
- Which AviationStack endpoint is used?
- Which request fields are sent to AviationStack?
- How is the returned flight matched to the user's requested departure airport, destination airport, and scheduled departure time?
- What is the scheduled departure time tolerance?
- What happens if no matching flight is found?

### Weather Data Lookup

- Why does the backend call Open-Meteo?
- Does the system request weather for the origin, destination, or both?
- Which date is used for the weather request?
- Which weather fields are required by the model?
- What happens if the weather API returns missing, invalid, or partial data?

### Model Inference

- Where is the trained model artifact stored?
- What input columns must exist before inference?
- Which fields are numeric and which are categorical?
- What preprocessing is included in the saved model pipeline?
- What does the model return: class label, probability, or both?
- What does `is_significant_delay` mean?

### Prediction Response

- What response fields does the backend return to the frontend?
- Which fields are directly from user input, AviationStack, DuckDB, Open-Meteo, or model output?
- How is the delay probability represented?
- What should the frontend display if probability is `null`?
- Which extra fields are useful for debugging or explaining the prediction to a user?

---

## Frontend Architecture

- What is the frontend responsible for?
- Which frontend framework and build tool are used?
- How is the app split between reusable components, feature modules, API helpers, and shared types?
- What frontend state exists: form state, loading state, error state, and prediction result state?
- What assumptions does the frontend make about the backend response shape?

### App Structure

- What does `src/App.tsx` coordinate?
- Which files define the first screen a user sees?
- Which folders contain shared code versus feature-specific code?
- Are there any conventions for naming files or folders?

### Feature Modules

- What user-facing features exist right now?
- Which feature owns the flight lookup form?
- Which feature owns the prediction result display?
- If a new feature is added, where should it live?

### Components

- Which components are generic and reusable?
- Which components are tied to flight prediction specifically?
- What props does each important component expect?
- What visual or layout responsibilities belong inside each component?

### API Client

- Where is the frontend API client defined?
- Which environment variables configure the API base URL and prediction endpoint?
- How are failed HTTP responses handled?
- Does the client transform request or response data, or does it pass JSON through directly?

### Types

- Where are shared TypeScript API types defined?
- Do the frontend types match the backend Pydantic models?
- Which fields are optional or nullable?
- What type mismatches should be watched for when the backend changes?

### Styling

- Where is global CSS defined?
- Are styles organized by component, feature, or global rules?
- What layout decisions are important for the form and result view?
- What browser or screen sizes should the UI support?

---

## Backend Architecture

- What is the backend responsible for?
- Which framework is used?
- Which code handles HTTP routing, service logic, external API clients, models, logging, and utility functions?
- What code runs only for training or data preparation and should not be part of the request path?
- What are the main dependencies of the backend?

### FastAPI Application

- Where is the FastAPI app created?
- Which middleware is configured?
- What frontend origins are allowed by CORS?
- Which routes are registered?
- How is logging configured at startup?

### Routes

- What does `GET /health` return, and what is it for?
- What does `POST /predict` receive and return?
- Does the route contain business logic, or does it delegate to a service?
- How are service failures converted into HTTP errors?

### Services

- Which service coordinates the flight prediction workflow?
- What are the major steps inside the service?
- Which helper functions build flight data, distance, weather features, model input, and final prediction?
- Which responsibilities should stay in the service layer instead of the route or API clients?

### Data Models

- Which Pydantic models define public request and response shapes?
- Which Pydantic models define internal service data?
- Which models define DuckDB table contracts?
- Which models forbid extra fields, and why?
- How do validation errors affect the API response?

### External API Clients

- Which files call AviationStack and Open-Meteo?
- Which environment variables are required for those clients?
- How are retries handled?
- What response wrapper is used for success and error results?
- What assumptions are made about each external API's response structure?

### Logging

- Where is logging configured?
- Where are API logs written?
- Which workflow steps emit useful logs?
- Are there any `print` calls that should become logger calls later?
- What sensitive values must never be logged?

### Configuration

- Which settings come from backend `.env` files?
- Which settings come from frontend `.env` files?
- Which paths are hardcoded, such as DuckDB path, log path, and model artifact path?
- What defaults exist for local development?
- Which settings would need to change for deployment?

---

## ML Architecture

- Which parts of the ML system run offline?
- Which parts run online during a prediction request?
- How does the training feature set match the inference feature set?
- How is the model artifact produced and consumed?
- What needs to stay stable between training and inference?

### Data Pipelines

- Which scripts or notebooks create cleaned flight, airport, weather, and model datasets?
- What raw files or external APIs do the pipelines depend on?
- Which DuckDB tables are created?
- What schema checks or invariants protect the pipeline?
- What steps must be run before the app can predict flights locally?

### Feature Engineering

- Which features are derived from schedule data?
- Which features are derived from airports and coordinates?
- Which features are derived from weather?
- Which categorical features are one-hot encoded?
- Which feature names must exactly match between training and inference?

### Model Artifacts

- Where is the trained model saved?
- What library loads the model during inference?
- Does the artifact include preprocessing as well as the classifier?
- How is the artifact versioned or regenerated?
- What happens if the artifact is missing?

### Inference Path

- How is request-time data converted into the single-row model dataframe?
- What field conversions are required before prediction?
- How are prediction probabilities calculated?
- What exceptions can happen during inference?
- How should inference failures be shown to API consumers?

---

## Data Storage and Generated Artifacts

- What is stored in DuckDB?
- Which tables are expected to exist?
- Which generated artifacts should be committed, and which should stay local?
- Where do trained models, figures, logs, and raw data live?
- Which files are too large, private, or reproducible and should be ignored by git?
- How can a new developer recreate the local data state?

---

## Environment Configuration

- Which environment variables are required to run the backend?
- Which environment variables are required to run the frontend?
- Which values are optional or have local defaults?
- Where should `.env` files be placed?
- What should be documented in `.env.example`?
- Which API keys are needed, and where can a developer get them?

---

## Error Handling

- What kinds of errors can happen before the backend reaches the model?
- What errors come from invalid user input?
- What errors come from missing local data or missing model artifacts?
- What errors come from external APIs?
- What status codes are returned for common failure cases?
- What error shape does the frontend currently receive?
- Are errors user-friendly enough, or mostly developer/debugging messages?

---

## Testing Strategy

- Which backend tests exist?
- What behavior is covered by unit tests?
- What behavior is covered by integration tests?
- Which external API calls are mocked or avoided in tests?
- Which ML pipeline contracts are tested?
- What frontend behavior still needs tests?
- What manual test steps should be run before a demo?

---

## Deployment

- How is the backend run locally?
- How is the frontend run locally?
- Has this project been deployed anywhere yet?
- If deployed later, where would the frontend, backend, DuckDB file, model artifact, and environment variables live?
- What changes would be needed for CORS, secrets, logging, file paths, and persistence?
- What deployment risks exist because this app depends on external APIs and local model/data files?

---

## Security and Privacy

- What secrets does the app use?
- How are API keys kept out of source control?
- Does the app store any user-submitted flight searches?
- Does the app process personal data?
- What could go wrong if external API responses are malformed?
- Are input validation and CORS settings strict enough for the current use case?

---

## Performance Considerations

- Which step is likely slowest: AviationStack, Open-Meteo, DuckDB lookup, model loading, or inference?
- Is the model loaded on every request?
- Would caching airport lookups, weather responses, or the model artifact improve performance?
- What happens if multiple users submit predictions at the same time?
- Are external API rate limits a concern?
- What performance is acceptable for a portfolio/demo app?

---

## Known Limitations

- Which limitations are caused by data quality?
- Which limitations are caused by external API availability or pricing?
- Which limitations are caused by the model choice?
- Which limitations are caused by using local DuckDB and local artifacts?
- Which airports, routes, dates, or weather scenarios may produce weak predictions?
- What should readers not overclaim about the prediction accuracy?
