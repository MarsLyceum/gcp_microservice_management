from google.api_core.exceptions import NotFound
import time

from .util import color_text, wait_for_deletion
from .constants import OKCYAN, OKGREEN, WARNING


def deploy_to_cloud_run(
    project_id, region, service_name, cloud_sql_instance, env_vars
):
    from google.cloud import run_v2

    print(color_text("Deploying to Google Cloud Run...", OKCYAN))
    client = run_v2.ServicesClient()
    service_path = (
        f"projects/{project_id}/locations/{region}/services/{service_name}"
    )

    service = run_v2.Service(
        template=run_v2.RevisionTemplate(
            containers=[
                run_v2.Container(
                    image=f"gcr.io/{project_id}/{service_name}:latest",
                    env=[
                        run_v2.EnvVar(name=key, value=value)
                        for key, value in env_vars.items()
                    ],
                    volume_mounts=[
                        run_v2.VolumeMount(
                            name="cloudsql", mount_path="/cloudsql"
                        )
                    ],
                )
            ],
            volumes=[
                run_v2.Volume(
                    name="cloudsql",
                    cloud_sql_instance=run_v2.CloudSqlInstance(
                        instances=[cloud_sql_instance]
                    ),
                )
            ],
            annotations={
                "run.googleapis.com/cloudsql-instances": cloud_sql_instance
            },
        ),
    )

    try:
        existing_service = client.get_service(name=service_path)
        if existing_service:
            print(
                color_text(
                    f"Service {service_name} already exists. Deleting...",
                    WARNING,
                )
            )
            client.delete_service(name=service_path)
            wait_for_deletion(client.get_service, service_path)
    except NotFound:
        print(
            color_text(
                f"Service {service_name} does not exist. Creating new service...",
                OKGREEN,
            )
        )

    client.create_service(
        parent=f"projects/{project_id}/locations/{region}",
        service=service,
        service_id=service_name,
    )

    while True:
        try:
            client.get_service(name=service_path)
            print(
                color_text(f"Service {service_name} is now active.", OKGREEN)
            )
            break
        except NotFound:
            print(
                color_text(
                    f"Waiting for {service_name} to be created...", WARNING
                )
            )
            time.sleep(5)
