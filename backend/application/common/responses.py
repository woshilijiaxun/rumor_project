from flask import jsonify

def ok(data=None, message="success", http_code=200):
    return jsonify({"status": "success", "message": message, "data": data}), http_code


def fail(message="fail", http_code=400, status="fail", data=None):
    return jsonify({"status": status, "message": message, "data": data}), http_code

