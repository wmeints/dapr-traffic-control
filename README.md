# Dapr Traffic Control Sample

| Attribute               | Details                   |
| ----------------------- | ------------------------- |
| Dapr runtime version    | v1.4.3                    |
| Dapr Python SDK version | v1.3.0                    |
| Dapr CLI version        | v1.4.0                    |
| Language                | Python                    |
| Platform                | Python 3.9                |
| Environment             | Self hosted or Kubernetes |

This repository contains a sample application that simulates a traffic-control system using Dapr. For this sample I've
used a speeding-camera setup as can be found on several Dutch highways. A set of cameras are placed at the beginning
and the end of a stretch of highway. Using data from these cameras, the average speed of a vehicle is measured.
If this average speed is above the speeding limit on this highway, the driver of the vehicle receives a fine.

## Overview

This is an overview of the fictitious setup I'm simulating in this sample:

![Speed trap overview](img/speed-trap-overview.png)

There's 1 entry-camera and 1 exit-camera per lane. When a car passes an entry-camera, the license-number of the car and
the timestamp is registered.

When the car passes an exit-camera, this timestamp is also registered by the system. The system then calculates the
average speed of the car based on the entry- and exit-timestamp. If a speeding violation is detected, a message is sent
to the Central Fine Collection Agency (or CJIB in Dutch). They will retrieve the information of the owner of the vehicle
and send him or her a fine.

## Simulation

In order to simulate this in code, I created the following services:

![Services](img/services.png)

- The **Camera Simulation** is a Python console application that will simulate passing cars.
- The **Traffic Control Service** is a Python application that offers 2 endpoints: `/entrycam` and `/exitcam`.
- The **Fine Collection Service** is a Python application that offers 1 endpoint: `/collectfine` for collecting fines.
- The **Vehicle Registration Service** is a Python application that offers 1 endpoint: `/vehicleinfo/{license-number}`
  for getting the vehicle- and owner-information of speeding vehicle.

The way the simulation works is depicted in the sequence diagram below:

![Sequence diagram](img/sequence.png)

1. The Camera Simulation generates a random license-number and sends a *VehicleRegistered* message (containing this
   license-number, a random entry-lane (1-3) and the timestamp) to the `/entrycam` endpoint of the TrafficControlService.
2. The TrafficControlService stores the VehicleState (license-number and entry-timestamp).
3. After some random interval, the Camera Simulation sends a *VehicleRegistered* message to the `/exitcam` endpoint of
   the TrafficControlService (containing the license-number generated in step 1, a random exit-lane (1-3) and the exit
   timestamp).
4. The TrafficControlService retrieves the VehicleState that was stored at vehicle entry.
5. The TrafficControlService calculates the average speed of the vehicle using the entry- and exit-timestamp. It also
   stores the VehicleState with the exit timestamp for audit purposes, but this is left out of the sequence diagram
   for clarity.
6. If the average speed is above the speed-limit, the TrafficControlService calls the `/collectfine` endpoint of the
   FineCollectionService. The request payload will be a *SpeedingViolation* containing the license-number of the
   vehicle, the identifier of the road, the speeding-violation in KMh and the timestamp of the violation.
7. The FineCollectionService calculates the fine for the speeding-violation.
8. The FineCollectionSerivice calls the `/vehicleinfo/{license-number}` endpoint of the VehicleRegistrationService
   with the license-number of the speeding vehicle to retrieve its vehicle- and owner-information.
9. The FineCollectionService sends a fine to the owner of the vehicle by email.

All actions described in this sequence are logged to the console during execution so you can follow the flow.

## Dapr

This sample uses Dapr for implementing several aspects of the application. In the diagram below you see a schematic
overview of the setup:

![Dapr setup](img/dapr-setup.png)

1. For doing request/response type communication between the FineCollectionService and the VehicleRegistrationService,
   the **service invocation** building block is used.
2. For sending speeding violations to the FineCollectionService, the **publish and subscribe** building block is used.
   RabbitMQ is used as message broker.
3. For storing the state of a vehicle, the **state management** building block is used. Redis is used as state store.
4. Fines are sent to the owner of a speeding vehicle by email. For sending the email, the Dapr SMTP **output binding**
   is used.
5. The Dapr **input binding** for MQTT is used to send simulated car info to the TrafficControlService. Mosquitto is
   used as MQTT broker.
6. The FineCollectionService needs credentials for connecting to the smtp server and a license-key for a fine calculator
   component. It uses the **secrets management** building block with the local file component to get the credentials and
   the license-key.
7. The TrafficControlService has an alternative implementation based on Dapr **actors**. See
   [Run the application with actors](#run-the-application-with-dapr-actors) for instructions on how to run this.

Here is the sequence diagram again, but now with all the Dapr building blocks and components:

![Sequence diagram with Dapr building blocks](img/sequence-dapr.png)

## Run the application in Dapr self-hosted mode

In self-hosted mode everything will run on your local machine. To prevent port-collisions, all services listen on a
different HTTP port. When running the services with Dapr, you need additional ports voor HTTP and gRPC communication
with the sidecars. By default these ports are `3500` and `50001`. But to prevent confusion, you'll use totally different
port numbers in the assignments. The services will use the following ports:

| Service                    | Application Port | Dapr sidecar HTTP port | Dapr sidecar gRPC port |
| -------------------------- | ---------------- | ---------------------- | ---------------------- |
| TrafficControlService      | 6000             | 3600                   | 60000                  |
| FineCollectionService      | 6001             | 3601                   | 60001                  |
| VehicleRegistrationService | 6002             | 3602                   | 60002                  |

The ports can be specified on the command-line when starting a service with the Dapr CLI. The following command-line
flags can be used:

- `--app-port`
- `--dapr-http-port`
- `--dapr-grpc-port`

Execute the following steps to run the sample application in self hosted mode:

Start infrastructure components:

1. Make sure you have installed Dapr on your machine in self-hosted mode as described in the
   [Dapr documentation](https://docs.dapr.io/getting-started/install-dapr/).
2. Open a new command-shell.
3. Change the current folder to the `src/Infrastructure` folder of this repo.
4. Start the infrastructure services by executing `start-all.ps1` script. This script will start Mosquitto (MQTT broker),
5. RabbitMQ (pub/sub broker) and Maildev. Maildev is a development SMTP server that does not actually send out emails
   (by default). Instead, it offers a web frontend that will act as an email in-box showing the emails that were sent
   to the SMTP server. This is very convenient for demos of testscenarios.

Start the services:

1. Open a new command-shell.

2. Change the current folder to the `src/VehicleRegistrationService` folder of this repo.

3. Execute the following command (using the Dapr cli) to run the VehicleRegistrationService:

    ```console
    dapr run --app-id vehicleregistrationservice --app-port 6002 --dapr-http-port 3602 --dapr-grpc-port 60002 --config ../dapr/config/config.yaml --components-path ../dapr/components -- uvicorn vehicle_registration:app --port 6002
    ```

    >  Alternatively you can also run the `start-selfhosted.ps1` script.

4. Open a new command-shell.

5. Change the current folder to the `src/FineCollectionService` folder of this repo.

6. Execute the following command (using the Dapr cli) to run the FineCollectionService:

    ```console
    dapr run --app-id finecollectionservice --app-port 6001 --dapr-http-port 3601 --dapr-grpc-port 60001 --config ../dapr/config/config.yaml --components-path ../dapr/components -- uvicorn fine_collection:app --port 6001
    ```

    > Alternatively you can also run the `start-selfhosted.ps1` script.

7. Open a new command-shell.

8. Change the current folder to the `src/TrafficControlService` folder of this repo.

9. Execute the following command (using the Dapr cli) to run the TrafficControlService:

    ```console
    dapr run --app-id trafficcontrolservice --app-port 6000 --dapr-http-port 3600 --dapr-grpc-port 60000 --config ../dapr/config/config.yaml --components-path ../dapr/components -- uvicorn traffic_control:app --port 6000
    ```

    > Alternatively you can also run the `start-selfhosted.ps1` script.

10. Open a new command-shell.

11. Change the current folder to the `src/Simulation` folder of this repo.

12. Execute the following command to run the Camera Simulation:

     ```console
     python simulation
     ```

You should now see logging in each of the shells, similar to the logging shown below:

**Camera Simulation:**  

![Simulation logging](img/logging-simulation.png)

**TrafficControlService:**  

![TrafficControlService loggin](img/logging-trafficcontrolservice.png)

**FineCollectionService:**  

![FineCollectionService logging](img/logging-finecollectionservice.png)

**VehicleRegistrationService:**  

![VehicleRegistrationService logging](img/logging-vehicleregistrationservice.png)

To see the emails that are sent by the FineCollectionService, open a browser and browse to 
[http://localhost:4000](http://localhost:4000). You should see the emails coming in:

![Mailbox](img/mailbox.png)

## Disclaimer

The code in this repo is NOT production grade and lacks any automated testing. It is intentionally kept as simple as
possible (KISS). Its primary purpose is demonstrating several Dapr concepts and not being a full fledged application
that can be put into production as is.

The author can in no way be held liable for damage caused directly or indirectly by using this code.
