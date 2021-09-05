from dapr.clients import DaprClient
from . import models


class FineCollectionClient:
    def collect_fine(self, violation: models.SpeedingViolation):
        with DaprClient() as client:
            client.invoke_method(
                app_id="finecollectionservice",
                method_name="collectfine",
                data=violation.json()
            )
