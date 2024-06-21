import datetime
import time
from google.cloud import apigateway_v1
from google.cloud.apigateway_v1.types import Gateway
from google.api_core.exceptions import NotFound
from openapi_spec_validator import validate_spec
from openapi_spec_validator.readers import read_from_filename
import os

from .util import color_text, wait_for_deletion
from .constants import OKCYAN, OKGREEN, WARNING, FAIL


def create_api_gateway_service(
    client: apigateway_v1.ApiGatewayServiceClient, project_id: str, api_id: str
) -> None:
    api_name = f"projects/{project_id}/locations/global/apis/{api_id}"
    try:
        existing_api = client.get_api(name=api_name)
        if existing_api:
            print(
                color_text(
                    f"API {api_id} already exists. Deleting...", WARNING
                )
            )
            client.delete_api(name=api_name)
            wait_for_deletion(client.get_api, api_name)
    except NotFound:
        print(
            color_text(
                f"API {api_id} does not exist. Creating new API...", OKGREEN
            )
        )

    api = apigateway_v1.Api(display_name=api_id)
    client.create_api(
        parent=f"projects/{project_id}/locations/global",
        api=api,
        api_id=api_id,
    )

    while True:
        try:
            client.get_api(name=api_name)
            print(color_text(f"API {api_id} is now active.", OKGREEN))
            break
        except NotFound:
            print(
                color_text(
                    f"Waiting for API {api_id} to be created...", WARNING
                )
            )
            time.sleep(5)


def create_or_update_api_config(
    client: apigateway_v1.ApiGatewayServiceClient,
    project_id: str,
    api_id: str,
    api_config_id: str,
    api_config_file: str,
):
    print(color_text("Creating or Updating API Config...", OKCYAN))
    parent = client.api_path(project_id, api_id)
    api_config_name = f"projects/{project_id}/locations/global/apis/{api_id}/configs/{api_config_id}"

    # Check if the OpenAPI document exists and is readable
    if not os.path.isfile(api_config_file):
        raise FileNotFoundError(
            f"OpenAPI document not found at path: {api_config_file}"
        )

    # Validate OpenAPI document
    try:
        spec_dict, _ = read_from_filename(api_config_file)
        validate_spec(spec_dict)
        print(
            color_text(
                f"OpenAPI document {api_config_file} is valid.", OKGREEN
            )
        )
    except Exception as e:
        raise ValueError(f"Invalid OpenAPI document: {e}")

    api_config = apigateway_v1.ApiConfig(
        name=api_config_name,
        display_name=api_config_id,
        openapi_documents=[
            apigateway_v1.ApiConfig.OpenApiDocument(
                document=apigateway_v1.ApiConfig.File(path=api_config_file)
            )
        ],
    )

    try:
        existing_config = client.get_api_config(name=api_config_name)
        if existing_config:
            print(
                color_text(
                    f"API Config {api_config_id} already exists. Deleting...",
                    WARNING,
                )
            )
            client.delete_api_config(name=api_config_name)
            wait_for_deletion(client.get_api_config, api_config_name)
    except NotFound:
        print(
            color_text(
                f"API Config {api_config_id} does not exist. Creating new API Config...",
                OKGREEN,
            )
        )

    start_time = datetime.datetime.now()
    max_duration = datetime.timedelta(minutes=10)
    while True:
        try:
            client.create_api_config(
                parent=parent,
                api_config=api_config,
                api_config_id=api_config_id,
            )
            print(color_text(f"API Config {api_config_id} created.", OKGREEN))
            break
        except Exception as e:
            print(color_text(f"Error creating API Config: {e}", WARNING))
            elapsed_time = datetime.datetime.now() - start_time
            if elapsed_time > max_duration:
                print(color_text("Max duration reached. Exiting...", FAIL))
                raise RuntimeError(
                    "Failed to create API Config within the allowed time frame."
                )
            print(color_text("Retrying in 5 seconds...", WARNING))
            time.sleep(5)


def create_gateway(
    client: apigateway_v1.ApiGatewayServiceClient,
    project_id: str,
    location: str,
    gateway_name: str,
    api_id: str,
    api_config_id: str,
) -> None:
    gateway_name_full = (
        f"projects/{project_id}/locations/{location}/gateways/{gateway_name}"
    )
    print(color_text("Creating API Gateway...", OKCYAN))

    try:
        existing_gateway = client.get_gateway(name=gateway_name_full)
        if existing_gateway:
            print(
                color_text(
                    f"Gateway {gateway_name} already exists. Deleting...",
                    WARNING,
                )
            )
            client.delete_gateway(name=gateway_name_full)
            wait_for_deletion(client.get_gateway, gateway_name_full)
    except NotFound:
        print(
            color_text(
                f"Gateway {gateway_name} does not exist. Creating new Gateway...",
                OKGREEN,
            )
        )

    gateway = Gateway(
        name=gateway_name_full,
        api_config=f"projects/{project_id}/locations/global/apis/{api_id}/configs/{api_config_id}",
    )
    client.create_gateway(
        parent=f"projects/{project_id}/locations/{location}",
        gateway_id=gateway_name,
        gateway=gateway,
    )
    print(color_text(f"Gateway {gateway_name} created.", OKGREEN))
