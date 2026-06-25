import httpx

from services.cloud_launchers.base import CloudLauncherError, LaunchedPod

RUNPOD_GRAPHQL_URL = "https://api.runpod.io/graphql"

DEFAULT_CLOUD_TYPE = "ALL"
DEFAULT_GPU_COUNT = 1
DEFAULT_CONTAINER_DISK_GB = 50
DEFAULT_VOLUME_GB = 50


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _build_launch_mutation(
    *,
    name: str,
    image_name: str,
    gpu_type_id: str,
    gpu_count: int,
    cloud_type: str,
    container_disk_in_gb: int,
    volume_in_gb: int,
    env: dict[str, str],
) -> str:
    """Mutation shape ported from runpod-python's api/mutations/pods.py ::
    generate_pod_deployment_mutation (confirmed against the live GitHub source —
    RunPod's GraphQL API has no public schema doc, so the official SDK's own
    query-builder is the closest thing to a contract test). Trimmed to only the
    fields this launcher sets; quote-escaping added since the SDK's own f-string
    interpolation has none.
    """
    env_items = ", ".join(
        f'{{ key: "{_escape(k)}", value: "{_escape(v)}" }}' for k, v in env.items()
    )
    return f"""
    mutation {{
      podFindAndDeployOnDemand(
        input: {{
          name: "{_escape(name)}"
          imageName: "{_escape(image_name)}"
          cloudType: {cloud_type}
          gpuTypeId: "{_escape(gpu_type_id)}"
          gpuCount: {gpu_count}
          containerDiskInGb: {container_disk_in_gb}
          volumeInGb: {volume_in_gb}
          env: [{env_items}]
        }}
      ) {{
        id
        imageName
        machineId
      }}
    }}
    """


def _build_terminate_mutation(pod_id: str) -> str:
    return f"""
    mutation {{
        podTerminate(input: {{ podId: "{_escape(pod_id)}" }})
    }}
    """


async def _graphql_request(
    api_key: str, query: str, client: httpx.AsyncClient | None = None
) -> dict:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    owns_client = client is None
    http_client = client or httpx.AsyncClient(timeout=30.0)
    try:
        response = await http_client.post(
            RUNPOD_GRAPHQL_URL, headers=headers, json={"query": query}
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise CloudLauncherError(f"RunPod API request failed: {exc}") from exc
    finally:
        if owns_client:
            await http_client.aclose()

    payload = response.json()
    if "errors" in payload:
        raise CloudLauncherError(f"RunPod GraphQL error: {payload['errors']}")
    return payload.get("data", {})


async def launch_runpod_pod(
    *,
    api_key: str,
    name: str,
    image_name: str,
    gpu_type_id: str,
    env: dict[str, str],
    gpu_count: int = DEFAULT_GPU_COUNT,
    cloud_type: str = DEFAULT_CLOUD_TYPE,
    container_disk_in_gb: int = DEFAULT_CONTAINER_DISK_GB,
    volume_in_gb: int = DEFAULT_VOLUME_GB,
    client: httpx.AsyncClient | None = None,
) -> LaunchedPod:
    query = _build_launch_mutation(
        name=name,
        image_name=image_name,
        gpu_type_id=gpu_type_id,
        gpu_count=gpu_count,
        cloud_type=cloud_type,
        container_disk_in_gb=container_disk_in_gb,
        volume_in_gb=volume_in_gb,
        env=env,
    )
    data = await _graphql_request(api_key, query, client)
    pod = data.get("podFindAndDeployOnDemand")
    if not pod or not pod.get("id"):
        raise CloudLauncherError(
            f"RunPod did not return a deployed pod for gpu_type_id={gpu_type_id!r} "
            "— likely no GPU availability."
        )
    return LaunchedPod(
        pod_id=pod["id"],
        image_name=pod.get("imageName", image_name),
        machine_id=pod.get("machineId"),
    )


async def terminate_runpod_pod(
    *, api_key: str, pod_id: str, client: httpx.AsyncClient | None = None
) -> None:
    query = _build_terminate_mutation(pod_id)
    await _graphql_request(api_key, query, client)
