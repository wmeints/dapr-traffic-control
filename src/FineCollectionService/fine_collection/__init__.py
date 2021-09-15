from fastapi import FastAPI
from fastapi.responses import Response
from . import models, settings, services, clients


app = FastAPI()
app_settings = settings.ApplicationSettings()

processor = services.ViolationProcessor(
    services.FineCalculator(), 
    clients.VehicleRegistrationClient()
)


@app.get("/dapr/subscribe")
def subscribe():
    subscription = [dict(
       pubsubname="pubsub",
       topic="speedingviolations",
       route="/collectfine"
    )]

    return subscription


@app.post("/collectfine")
def collect_fine(violation: models.SpeedingViolation) -> Response:
    processor.process_speed_violation(violation)

    return Response(status_code=200)
