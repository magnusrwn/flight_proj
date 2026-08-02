from fastapi import FastAPI
from logger_config import configure_logging
configure_logging()

app = FastAPI()

# Response Model (Would define in ~/models, however just one endpoint here)
@app.get("/health")
def health_check():
    return {"status":"ok"}

@app.post("/send-flight-number")
def send_flight_number(body):
    pass