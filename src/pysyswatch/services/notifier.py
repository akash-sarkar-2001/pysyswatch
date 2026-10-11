import logging

import httpx

from pysyswatch.config.settings import settings
from pysyswatch.models.schemas import HealthDiagnosis, HealthState

logger = logging.getLogger(__name__)


def send_alert_if_needed(health: HealthDiagnosis, previous_state: HealthState) -> None:
    """Fires a webhook only when the system enters a CRITICAL/WARNING state."""
    if not settings.alert_webhook_url:
        return

    # Only alert if the state has degraded to prevent spam
    if health.state == HealthState.HEALTHY or health.state == previous_state:
        return

    try:
        issues_text = "\n".join([f"- {issue}" for issue in health.issues])
        payload = {
            "text": f"🚨 *PySysWatch Alert* 🚨\n*Status:* {health.state.value}\n*Issues:*\n{issues_text}"
        }

        # Fire-and-forget HTTP request with a short timeout
        httpx.post(settings.alert_webhook_url, json=payload, timeout=5.0)
        logger.info("Alert webhook dispatched successfully.")
    except Exception as e:
        logger.error(f"Failed to dispatch alert webhook: {e}")
