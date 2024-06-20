# import os
# from env_util import find_env_file, load_env_variables, find_key_file
# from gcloud_util import deploy_to_cloud_run
# from google_api_util import (
#     create_api_gateway_service,
#     create_or_update_api_config,
#     create_gateway,
# )
# from .util import color_text, run_command
# from .constants import OKCYAN, OKGREEN


# def main():
#     project_id = "hephaestus-418809"
#     region = "us-west1"
#     api_gateway_region = "us-west2"
#     cloud_sql_instance = "hephaestus-418809:us-west1:user-api"
#     api_config_file = os.path.join(os.getcwd(), "peeps-web-service.yml")
#     api_gateway_name = "peeps-web-service-api-gateway"
#     service_name = "peeps-web-service"
#     api_id = "peeps-web-service-api"
#     api_config_id = f"{api_id}-config"

#     env_file = find_env_file()
#     print(color_text(f"Using .env file: {env_file}", OKGREEN))
#     env_vars = load_env_variables(env_file)
#     global DATABASE_PASSWORD
#     DATABASE_PASSWORD = env_vars.get("DATABASE_PASSWORD", "")

#     key_file = find_key_file()
#     print(color_text(f"Using key file: {key_file}", OKGREEN))
#     credentials = Credentials.from_service_account_file(key_file)
#     os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_file

#     api_gateway_client = apigateway_v1.ApiGatewayServiceClient(
#         credentials=credentials
#     )

#     print(
#         color_text("Authenticating gcloud with a service account...", OKCYAN)
#     )
#     os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_file

#     print(color_text("Building Docker image...", OKCYAN))
#     env = os.environ.copy()
#     env["DOCKER_BUILDKIT"] = "1"
#     run_command(
#         f"docker build -t gcr.io/{project_id}/{service_name}:latest --progress=plain .",
#         env=env,
#     )
#     print(color_text("Pushing Docker image...", OKCYAN))
#     run_command(f"docker push gcr.io/{project_id}/{service_name}:latest")

#     deploy_to_cloud_run(
#         project_id, region, service_name, cloud_sql_instance, env_vars
#     )

#     print(color_text("Creating new API...", OKCYAN))
#     create_api_gateway_service(api_gateway_client, project_id, api_id)

#     create_or_update_api_config(
#         api_gateway_client, project_id, api_id, api_config_id, api_config_file
#     )

#     create_gateway(
#         api_gateway_client,
#         project_id,
#         api_gateway_region,
#         api_gateway_name,
#         api_id,
#         api_config_id,
#     )


# if __name__ == "__main__":
#     main()
