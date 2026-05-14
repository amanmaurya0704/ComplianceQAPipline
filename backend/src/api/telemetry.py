import os
import logging
from azure.monitor.opentelemetry import configure_azure_monitor

logger = logging.getLogger("azure-comp-orestration-telemetry")

def setup_telemetry():
    '''
    Configures Azure Monitor for telemetry using OpenTelemetry SDK
    '''
    connection_string = os.getenv("APPLICATIONINSIGHT_CONNECTION_STRING")
    if not connection_string:
        logger.warning("APPLICATIONINSIGHT_CONNECTION_STRING is not set. Telemetry will not be sent to Azure Monitor.")
        return
    try:
        configure_azure_monitor(
            connection_string=connection_string,
            logger_name="azure-comp-orestration-tracing",
        )
        logger.info("Azure Monitor telemetry configured successfully.")
    except Exception as e:
        logger.error(f"Failed to configure Azure Monitor telemetry: {e}")