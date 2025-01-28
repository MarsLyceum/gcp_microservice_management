from google.api_core.exceptions import NotFound
from google.cloud import run_v2
import time

from .util import color_text, wait_for_deletion, run_command
from .constants import OKCYAN, OKGREEN, WARNING


def deploy_to_cloud_run(
    project_id,
    region,
    service_name,
    env_vars,
    registry="gcr.io",
    cloud_sql_instance=None,
):
    """
    Deploy a service to Google Cloud Run.

    :param project_id: GCP project ID
    :param region: GCP region
    :param service_name: Name of the Cloud Run service
    :param env_vars: Dictionary of environment variables to set on the
                                container
    :param registry: The container registry hostname (default: 'gcr.io')
    :param cloud_sql_instance: (Optional) The Cloud SQL instance connection
                                name (e.g., 'project:region:instance'). If
                                omitted, no Cloud SQL volume or annotations
                                will be added.
    """
    print(color_text("Deploying to Google Cloud Run...", OKCYAN))
    client = run_v2.ServicesClient()
    service_path = (
        f"projects/{project_id}/locations/{region}/services/{service_name}"
    )

    # Prepare optional Cloud SQL config if cloud_sql_instance is provided
    volume_mounts = []
    volumes = []
    annotations = {}

    if cloud_sql_instance:
        volume_mounts = [
            run_v2.VolumeMount(name="cloudsql", mount_path="/cloudsql")
        ]
        volumes = [
            run_v2.Volume(
                name="cloudsql",
                cloud_sql_instance=run_v2.CloudSqlInstance(
                    instances=[cloud_sql_instance]
                ),
            )
        ]
        annotations["run.googleapis.com/cloudsql-instances"] = (
            cloud_sql_instance
        )

    # Build the service object
    service = run_v2.Service(
        template=run_v2.RevisionTemplate(
            containers=[
                run_v2.Container(
                    image=f"{registry}/{project_id}/{service_name}:latest",
                    env=[
                        run_v2.EnvVar(name=key, value=value)
                        for key, value in env_vars.items()
                    ],
                    volume_mounts=volume_mounts,
                )
            ],
            volumes=volumes,
            annotations=annotations,
        ),
    )

    # Check if the service already exists
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

    # Create the service
    client.create_service(
        parent=f"projects/{project_id}/locations/{region}",
        service=service,
        service_id=service_name,
    )

    # Wait until the service is active
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

    # Set IAM policy to allow unauthenticated access
    print(
        color_text(
            "Setting IAM policy to allow unauthenticated access...", OKCYAN
        )
    )
    run_command(
        f"gcloud run services add-iam-policy-binding {service_name} "
        f'--member="allUsers" '
        f'--role="roles/run.invoker" '
        f"--region={region}"
    )

    print(
        color_text(
            f"Service {service_name} is now set to allow unauthenticated calls.",
            OKGREEN,
        )
    )
