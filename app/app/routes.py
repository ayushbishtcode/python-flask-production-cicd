from flask import Blueprint, jsonify

api = Blueprint("api", __name__)


@api.get("/health")
def health():
    return jsonify(
        {
            "status": "healthy",
            "service": "employee-api",
        }
    ), 200