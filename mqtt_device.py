"""AWS IoT Core MQTT subscriber for the virtual load indicator.

Required environment variables:
  AWS_IOT_ENDPOINT  - AWS IoT data endpoint, e.g. xxxx-ats.iot.ap-south-1.amazonaws.com
  AWS_IOT_CERT      - device certificate file path
  AWS_IOT_PRIVATE_KEY - matching private key file path
  AWS_IOT_CA        - Amazon Root CA file path
Optional:
  AWS_IOT_CLIENT_ID (default: load-indicator-subscriber)
  AWS_IOT_TOPIC (default: ecommerce/server/load)

This process receives load messages. It does not read CloudWatch by itself.
"""
import json
import os
import signal
import sys
import threading
from pathlib import Path

from awscrt import mqtt
from awsiot import mqtt_connection_builder

ANGLES = {"LOW": 0, "MEDIUM": 90, "HIGH": 180}
stop_event = threading.Event()


def required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def on_message(topic: str, payload: bytes, **kwargs) -> None:
    """Validate a message and print the virtual servo's target position."""
    try:
        message = json.loads(payload.decode("utf-8"))
        status = str(message.get("status", "")).upper()
        if status not in ANGLES:
            print(f"[MQTT] Ignored message with unknown status: {message!r}")
            return

        angle = ANGLES[status]
        cpu = message.get("cpu_percent")
        source = message.get("source", "unspecified")
        print(f"[MQTT] Topic: {topic}")
        print(f"[LOAD] Status: {status} | Virtual servo: {angle} degrees")
        if isinstance(cpu, (int, float)):
            print(f"[METRIC] CPU utilization: {cpu:.1f}%")
        print(f"[SOURCE] {source}")
        print("-" * 52)
    except (UnicodeDecodeError, json.JSONDecodeError, AttributeError) as exc:
        print(f"[MQTT] Invalid JSON message: {exc}")


def main() -> int:
    endpoint = required_env("AWS_IOT_ENDPOINT")
    cert = Path(required_env("AWS_IOT_CERT")).expanduser()
    private_key = Path(required_env("AWS_IOT_PRIVATE_KEY")).expanduser()
    ca = Path(required_env("AWS_IOT_CA")).expanduser()
    for label, path in (("certificate", cert), ("private key", private_key), ("CA certificate", ca)):
        if not path.is_file():
            raise FileNotFoundError(f"{label} file not found: {path}")

    client_id = os.getenv("AWS_IOT_CLIENT_ID", "load-indicator-subscriber")
    topic = os.getenv("AWS_IOT_TOPIC", "ecommerce/server/load")

    connection = mqtt_connection_builder.mtls_from_path(
        endpoint=endpoint,
        cert_filepath=str(cert),
        pri_key_filepath=str(private_key),
        ca_filepath=str(ca),
        client_id=client_id,
        clean_session=True,
        keep_alive_secs=30,
    )

    print(f"Connecting to AWS IoT Core endpoint: {endpoint}")
    connect_future = connection.connect()
    connect_future.result(timeout=15)
    print("Connected. Subscribing to:", topic)

    subscribe_future, packet_id = connection.subscribe(
        topic=topic,
        qos=mqtt.QoS.AT_LEAST_ONCE,
        callback=on_message,
    )
    subscribe_future.result(timeout=15)
    print("Subscription active. Press Ctrl+C to stop.")

    def request_stop(signum, frame):
        stop_event.set()

    signal.signal(signal.SIGINT, request_stop)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, request_stop)

    try:
        while not stop_event.wait(1):
            pass
    finally:
        print("Disconnecting from AWS IoT Core...")
        try:
            connection.disconnect().result(timeout=10)
        except Exception as exc:  # keep shutdown graceful if network is already gone
            print(f"Disconnect notice: {exc}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
