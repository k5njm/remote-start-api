"""
Remote Start - Raspberry Pi GPIO RESTful Server

Description:
This server allows for controlling a GPIO pin on a Raspberry Pi using a RESTful interface. There are three main endpoints:
    - /lock
    - /unlock
    - /engine

Each endpoint responds to a POST request and triggers a specific GPIO pin activation pattern.

Configuration:
The server configuration can be set using environment variables:
    - GPIO_PIN: Defines which GPIO pin number is controlled (default is 23).
    - API_USERNAME: Username for basic API authentication (default is 'admin').
    - API_PASSWORD: Password for basic API authentication (default is 'password').
    - LOG_LEVEL: Defines the logging level (default is 'WARNING'). Other valid values include 'INFO', 'DEBUG', 'ERROR', etc.

Usage:
To run the server, simply execute the script. Make sure to have the necessary libraries installed.

Authentication:
The API uses basic authentication. For better security, consider moving to token-based authentication in a production scenario.

Endpoints:
    - POST /lock: Activate the GPIO pin for 0.25 seconds.
    - POST /unlock: Activate the GPIO pin for 0.25 seconds, pause for 0.1 seconds, and then activate again for 0.25 seconds.
    - POST /engine: Activate the GPIO pin for 5 seconds.

Rate Limiting:
The /lock and /unlock endpoints are rate-limited to 1 request per second. The /engine endpoint is limited to 1 request per minute.

Warnings:
    - Use caution when connecting external devices to your Raspberry Pi GPIO.
    - Ensure your setup can handle frequent state changes to prevent hardware damage.
    - Always keep authentication information confidential.

Note:
This documentation is for reference. Always refer to external documentation for libraries and hardware details.
"""


import time
import logging
import os
from flask import Flask, jsonify, abort, request
from flask_limiter import Limiter
import RPi.GPIO as GPIO
from functools import wraps


# Setup Logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
limiter = Limiter(app)

# Configuration
GPIO_PIN = int(os.environ.get("GPIO_PIN", 23))
USERNAME = os.environ.get("API_USERNAME", "admin")
PASSWORD = os.environ.get("API_PASSWORD", "password")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()

try:
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(GPIO_PIN, GPIO.OUT)
except RuntimeError:
    logging.error("Error importing RPi.GPIO! This is probably because you need superuser privileges.")


def authenticate(f):
    """
    This decorator checks for valid authentication headers.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not (auth.username == USERNAME and auth.password == PASSWORD):
            abort(401, "Invalid authentication credentials.")
        return f(*args, **kwargs)
    return decorated


def activate_gpio(duration):
    """
    Activate GPIO pin for a specific duration.
    """
    try:
        GPIO.output(GPIO_PIN, GPIO.HIGH)
        time.sleep(duration)
        GPIO.output(GPIO_PIN, GPIO.LOW)
    except Exception as e:
        logging.error(f"Error activating GPIO: {e}")
        abort(500, "GPIO activation error")

@app.route('/lock', methods=['POST'])
@limiter.limit("1 per second")
@authenticate
def lock():
    logging.info("Lock activation requested")
    activate_gpio(0.25)
    return jsonify({"status": "Lock activated!"})

@app.route('/unlock', methods=['POST'])
@limiter.limit("1 per second")
@authenticate
def unlock():
    logging.info("Unlock activation requested")
    activate_gpio(0.25)
    time.sleep(0.1)
    activate_gpio(0.25)
    return jsonify({"status": "Unlock activated!"})

@app.route('/engine', methods=['POST'])
@limiter.limit("2 per minute")
@authenticate
def engine():
    logging.info("Engine activation requested")
    activate_gpio(5)
    return jsonify({"status": "Engine activated!"})




if __name__ == '__main__':
    try:
        app.run(host='127.0.0.1', port=5000)
    finally:
        GPIO.cleanup()

