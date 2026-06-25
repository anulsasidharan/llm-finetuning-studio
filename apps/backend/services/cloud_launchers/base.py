from dataclasses import dataclass


@dataclass(frozen=True)
class LaunchedPod:
    pod_id: str
    image_name: str
    machine_id: str | None


class CloudLauncherError(Exception):
    """Raised when a cloud GPU provider's pod launch/terminate API call fails or
    returns an unexpected shape. Callers (cloud_launch_service) map this to a
    user-facing ExternalServiceError rather than letting it bubble up raw."""
