from google.api_core.exceptions import NotFound
from google.cloud import run_v2
import time

from .util import color_text, run_command
from .constants import OKCYAN, OKGREEN, WARNING


def deploy_to_cloud_run(
    project_id,
    region,
    service_name,
    env_vars,
    registry="gcr.io",
    cloud_sql_instance=None,
    force_recreate=False,  # if True, delete & recreate instead of updating
    memory_limit="512Mi",  # New parameter: default memory limit
):
    print(color_text("Deploying to Google Cloud Run...", OKCYAN))
    client = run_v2.ServicesClient()
    service_path = (
        f"projects/{project_id}/locations/{region}/services/{service_name}"
    )

    # Prepare Cloud SQL configuration if needed.
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

    # Build the service object with the new image.
    # Note the addition of the container resources field using memory_limit.
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
                    resources=run_v2.ResourceRequirements(
                        limits={"memory": memory_limit}
                    ),
                )
            ],
            volumes=volumes,
            annotations=annotations,
        ),
    )

    try:
        # Check if the service already exists.
        try:
            existing_service = client.get_service(name=service_path)
        except NotFound:
            existing_service = None

        if force_recreate:
            if existing_service:
                print(
                    color_text(
                        f"Deleting existing service {service_name}...", OKCYAN
                    )
                )
                delete_op = client.delete_service(name=service_path)
                # Wait until the service is deleted.
                while True:
                    try:
                        client.get_service(name=service_path)
                        print(
                            color_text(
                                f"Waiting for {service_name} to be deleted...",
                                WARNING,
                            )
                        )
                        time.sleep(5)
                    except NotFound:
                        print(
                            color_text(
                                f"Service {service_name} deleted.", OKGREEN
                            )
                        )
                        break
            # Create new service
            print(
                color_text(f"Creating new service {service_name}...", OKCYAN)
            )
            client.create_service(
                parent=f"projects/{project_id}/locations/{region}",
                service=service,
                service_id=service_name,
            )
            # Wait for the service to become active.
            while True:
                try:
                    client.get_service(name=service_path)
                    print(
                        color_text(
                            f"Service {service_name} is now active.", OKGREEN
                        )
                    )
                    break
                except NotFound:
                    print(
                        color_text(
                            f"Waiting for {service_name} to be created...",
                            WARNING,
                        )
                    )
                    time.sleep(5)
        else:
            if existing_service:
                print(
                    color_text(f"Updating service {service_name}...", OKCYAN)
                )
                # Set the full service name in the Service object.
                service.name = service_path
                updated_service = client.update_service(service=service)
                # Optionally wait until the new revision is ready.
                while True:
                    try:
                        client.get_service(name=service_path)
                        print(
                            color_text(
                                f"Service {service_name} is now updated.",
                                OKGREEN,
                            )
                        )
                        break
                    except NotFound:
                        print(
                            color_text(
                                f"Waiting for {service_name} to update...",
                                WARNING,
                            )
                        )
                        time.sleep(5)
            else:
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
                # Wait for the service to become active.
                while True:
                    try:
                        client.get_service(name=service_path)
                        print(
                            color_text(
                                f"Service {service_name} is now active.",
                                OKGREEN,
                            )
                        )
                        break
                    except NotFound:
                        print(
                            color_text(
                                f"Waiting for {service_name} to be created...",
                                WARNING,
                            )
                        )
                        time.sleep(5)
    except Exception as e:
        print(color_text(f"Error deploying service: {str(e)}", WARNING))
        raise

    # Set IAM policy for unauthenticated access.
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
