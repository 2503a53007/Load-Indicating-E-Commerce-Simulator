
# Load-Indicating E-Commerce Simulator

## Project Introduction

The Load-Indicating E-Commerce Simulator is a web-based shopping simulation that demonstrates application load monitoring using AWS cloud services and a virtual servo motor.

## Objectives

- Develop an e-commerce website.
- Implement product search and shopping cart functionality.
- Monitor application/server load.
- Identify LOW, MEDIUM and HIGH load conditions.
- Map server load to virtual servo angles.
- Integrate AWS CloudWatch and AWS IoT Core using MQTT.

## Technology Stack

- HTML
- CSS
- JavaScript
- Python
- AWS Elastic Beanstalk
- Amazon EC2
- Amazon CloudWatch
- AWS IoT Core
- MQTT
- Git and GitHub

## Load Mapping

| Load | Servo Angle |
|---|---:|
| LOW | 0° |
| MEDIUM | 90° |
| HIGH | 180° |

## Project Structure

Load_Indicator_Simulator/
- index.html
- styles.css
- app.js
- mqtt_device.py
- cloudwatch_publisher.py
- servo_demo.py
- requirements.txt
- README.md
- .gitignore

## Local Execution

1. Open the project in VS Code.
2. Run index.html using Live Server.
3. Open the VS Code terminal.
4. Create a virtual environment:

   py -m venv .venv

5. Activate it:

   .\.venv\Scripts\Activate.ps1

6. Install dependencies:

   py -m pip install -r requirements.txt

7. Run the servo demonstration:

   py servo_demo.py

## AWS Integration

AWS IoT Core receives MQTT messages through mutual TLS authentication.

The Python MQTT subscriber listens to:

ecommerce/server/load

CloudWatch CPUUtilization is read by cloudwatch_publisher.py using boto3. The script maps the CPU metric to a load state and publishes it to AWS IoT Core.

CloudWatch does not automatically publish to IoT Core.

## Security

- Keep Certificates locally.
- Never upload private keys.
- Never commit AWS credentials.
- Use IAM roles and least-privilege permissions.
- Use .gitignore to protect sensitive files.

## Testing

- Test the frontend independently.
- Test the virtual servo independently.
- Test MQTT subscription independently.
- Test CloudWatch publishing independently.
- Verify AWS connectivity before claiming integration is working.
