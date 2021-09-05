from pydantic import BaseModel
from dapr.clients import DaprClient


class ClientError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class Vehicle(BaseModel):
    vehicleId: str
    make: str
    model: str
    ownerName: str
    ownerEmail: str


class VehicleRegistrationClient:
    def __init__(self, base_address: str):
        self.base_address = base_address

    def get_vehicle_info(self, license_number: str) -> Vehicle:
        with DaprClient() as client:
            response = client.invoke_method(
                app_id="vehicleregistrationservice",
                method_name=f"vehicleinfo/{license_number}",
                data=b'',
                http_verb="get"
            )

            return Vehicle.parse_raw(response.text())
