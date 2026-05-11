import json
import logging
import os

from flask import Flask, Response, jsonify, request

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def _parse_response_json(value):
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
    body = request.get_json(silent=True, force=True) or {}

    response_code = body.get("ResponseCode", 200)
    if not isinstance(response_code, int) or response_code < 100 or response_code > 599:
        return jsonify({"error": "ResponseCode must be a valid HTTP status code (100-599)"}), 400

    has_body = "ResponseJSON" in body
    response_data = _parse_response_json(body["ResponseJSON"]) if has_body else None
    response_format = body.get("ResponseFormat")

    reserved = {"ResponseJSON", "ResponseFormat", "ResponseCode"}
    ignored = sorted(body.keys() - reserved)

    logger.info(
        "Stub called | method=%s path=/%s ResponseCode=%s hasBody=%s ignoredFields=%s",
        request.method,
        path,
        response_code,
        has_body,
        ignored if ignored else "none",
    )

    if not has_body:
        return Response("", status=response_code)

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
