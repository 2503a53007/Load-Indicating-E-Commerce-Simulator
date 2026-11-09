"""Optional CloudWatch-to-AWS-IoT publisher.

Reads the EC2 CPUUtilization metric from CloudWatch and publishes a JSON
load message to ecommerce/server/load. This is the explicit bridge between
CloudWatch and AWS IoT Core; CloudWatch does NOT publish to IoT automatically.

AWS credentials are obtained from the standard boto3 credential chain
(AWS CLI profile, environment, or an attached IAM role). Do not put keys here.
"""
import json
import os
import signal
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import boto3
from awscrt import mqtt
from awsiot import mqtt_connection_builder

stop_requested = False


def env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None or not str(value).strip():
        raise RuntimeError(f"Missing required environment variable: {name}")
    return str(value).strip()


def load_level(cpu_percent: float) -> str:
    """Thresholds are configurable; defaults are demo thresholds."""
    low_max = float(os.getenv("LOAD_MEDIUM_THRESHOLD", "40"))
    high_min = float(os.getenv("LOAD_HIGH_THRESHOLD", "75"))
    if low_max >= high_min:
        raise ValueError("LOAD_MEDIUM_THRESHOLD must be lower than LOAD_HIGH_THRESHOLD")
    if cpu_percent < low_max:
        return "LOW"
    if cpu_percent < high_min:
        return "MEDIUM"
    return "HIGH"


def main() -> int:
    global stop_requested
    region = env("AWS_REGION")
    instance_id = env("EC2_INSTANCE_ID")
    endpoint = env("AWS_IOT_ENDPOINT")
    cert = Path(env("AWS_IOT_CERT")).expanduser()
    private_key = Path(env("AWS_IOT_PRIVATE_KEY")).expanduser()
    ca = Path(env("AWS_IOT_CA")).expanduser()
    topic = env("AWS_IOT_TOPIC", "ecommerce/server/load")
    interval = int(env("PUBLISH_INTERVAL_SECONDS", "60"))

    for label, path in (("certificate", cert), ("private key", private_key), ("CA certificate", ca)):
        if not path.is_file():
            raise FileNotFoundError(f"{label} file not found: {path}")
    if interval < 60:
        raise ValueError("Use a publish interval of at least 60 seconds for this demo.")

    cloudwatch = boto3.client("cloudwatch", region_name=region)
    connection = mqtt_connection_builder.mtls_from_path(
        endpoint=endpoint,
        cert_filepath=str(cert),
        pri_key_filepath=str(private_key),
        ca_filepath=str(ca),
        client_id=os.getenv("AWS_IOT_CLIENT_ID", "cloudwatch-load-publisher"),
        clean_session=True,
        keep_alive_secs=30,
    )

    print(f"Connecting publisher to AWS IoT Core in {region}...")
    connection.connect().result(timeout=15)
    print(f"Connected. Reading AWS/EC2 CPUUtilization for {instance_id}.")

    def stop_handler(signum, frame):
        global stop_requested
        stop_requested = True

    signal.signal(signal.SIGINT, stop_handler)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, stop_handler)

    try:
        while not stop_requested:
            end = datetime.now(timezone.utc)
            response = cloudwatch.get_metric_statistics(
                Namespace="AWS/EC2",
                MetricName="CPUUtilization",
                Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
                StartTime=end - timedelta(minutes=10),
                EndTime=end,
                Period=300,
                Statistics=["Average"],
            )
            datapoints = response.get("Datapoints", [])
            if not datapoints:
                print("No CPU datapoint returned yet. Check instance ID, region, and metric availability.")
            else:
                latest = max(datapoints, key=lambda point: point["Timestamp"])
                cpu = float(latest["Average"])
                status = load_level(cpu)
                message = {
                    "status": status,
                    "cpu_percent": round(cpu, 2),
                    "servo_angle": {"LOW": 0, "MEDIUM": 90, "HIGH": 180}[status],
                    "source": "AWS CloudWatch AWS/EC2 CPUUtilization",
                    "instance_id": instance_id,
                    "region": region,
                    "timestamp": latest["Timestamp"].astimezone(timezone.utc).isoformat(),
                }
                connection.publish(
                    topic=topic,
                    payload=json.dumps(message),
                    qos=mqtt.QoS.AT_LEAST_ONCE,
                ).result(timeout=10)
                print(f"Published {status} ({cpu:.1f}%) to {topic}")
            # Sleep in short intervals so Ctrl+C can stop promptly.
            for _ in range(interval):
                if stop_requested:
                    break
                time.sleep(1)
    finally:
        print("Disconnecting publisher...")
        connection.disconnect().result(timeout=10)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
