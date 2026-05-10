import json
import logging
import os

from flask import Flask, Response, jsonify, request

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def _parse_response_json(value):
    """Return value as a Python object. If value is a JSON string, decode it."""
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
@app.route("/<path:path>", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
def stub(path=""):
    body = request.get_json(silent=True, force=True)

    if not body:
        logger.warning("Request body missing or not valid JSON")
        return jsonify({"error": "Request body must be valid JSON"}), 400

    if "ResponseJSON" not in body:
        logger.warning("ResponseJSON field missing from request")
        return jsonify({"error": "ResponseJSON field is required in the request body"}), 400

    response_data = _parse_response_json(body["ResponseJSON"])
    response_format = body.get("ResponseFormat")
    response_code = body.get("ResponseCode", 200)

    if not isinstance(response_code, int) or response_code < 100 or response_code > 599:
        return jsonify({"error": "ResponseCode must be a valid HTTP status code (100-599)"}), 400

    reserved = {"ResponseJSON", "ResponseFormat", "ResponseCode"}
    ignored = sorted(body.keys() - reserved)

    logger.info(
        "Stub called | method=%s path=/%s ResponseCode=%s ResponseFormat=%s ignoredFields=%s",
        request.method,
        path,
        response_code,
        type(response_format).__name__,
        ignored if ignored else "none",
    )

    # If ResponseFormat is an array template, ensure the response is also an array.
    # If ResponseFormat is an object template, ensure the response is a single object.
    if isinstance(response_format, list) and not isinstance(response_data, list):
        response_data = [response_data]
    elif isinstance(response_format, dict) and isinstance(response_data, list):
        if len(response_data) == 1:
            response_data = response_data[0]

    payload = json.dumps(response_data, indent=2)
    return Response(payload, status=response_code, mimetype="application/json")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
