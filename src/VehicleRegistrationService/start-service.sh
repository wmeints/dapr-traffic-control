#!/bin/bash

APP_PORT=6001
GRPC_PORT=60001
DAPR_PORT=3601
APP_ID=finecollectionservice
APP_CLASS=fine_collection:app

dapr run --app-id $APP_ID --app-port $APP_PORT --dapr-http-port $DAPR_PORT --dapr-grpc-port $GRPC_PORT -- uvicorn $APP_CLASS --port $APP_PORT
