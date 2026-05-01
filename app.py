import flask.json
try:
    from flask.json import JSONEncoder
except ImportError:
    import json
    class JSONEncoder(json.JSONEncoder):
        def default(self, obj):
            if hasattr(obj, 'to_json'):
                return obj.to_json()
            return super().default(obj)
    flask.json.JSONEncoder = JSONEncoder
    from flask import Flask
    Flask.json_encoder = JSONEncoder

from shop import app

if __name__ == "__main__":
    app.run(debug=True)