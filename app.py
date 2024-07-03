import gevent.monkey
gevent.monkey.patch_all()

import requests
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import json
import os
import gzip
import io

app = Flask(__name__)
CORS(app)
TELEGRAPH_URL = 'https://api.openai.com'

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy(path):
    global TELEGRAPH_URL
    url = TELEGRAPH_URL + '/' + path
    headers = dict(request.headers)
    headers['Host'] = TELEGRAPH_URL.replace('https://', '')
    headers['Access-Control-Allow-Origin'] = headers.get('Access-Control-Allow-Origin') or "*"

    response = requests.request(
        method=request.method,
        url=url,
        headers=headers,
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False,
        stream=True  # Changed to True to handle streaming responses
    )

    # Filter out headers not to be forwarded
    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [(name, value) for (name, value) in response.raw.headers.items()
               if name.lower() not in excluded_headers]

    # Decompress if the content is gzipped
    content = response.content
    if response.headers.get('Content-Encoding') == 'gzip':
        content = gzip.decompress(content)

    # Decode content to UTF-8
    try:
        decoded_content = content.decode('utf-8')
    except UnicodeDecodeError:
        # If UTF-8 decoding fails, try to decode as ISO-8859-1 (or another encoding if needed)
        decoded_content = content.decode('iso-8859-1')

    # Create a new Response object with the decoded content
    flask_response = Response(decoded_content, response.status_code, headers)

    return flask_response



# @app.route("/")
# def hello_world():
#     return "Connect Success"

@app.route("/get_my_ip", methods=["GET"])
def get_my_ip():
    ip = request.access_route[-1]

    return jsonify({'ip': ip}), 200

@app.route("/get_outbound_ip", methods=["GET"])
def get_outbound_ip():
    # Define the API endpoint
    url = 'https://api.ipify.org/?format=json'

    # Send a GET request to the API
    response = requests.get(url)
    ip = response.json()

    return jsonify({'ip': ip}), 200

# @app.route("/OpenAIChat", methods=["GET"])
# def OpenAIChat():
#     target_model = request.args.get("model", "")
#     target_prompt = request.args.get("prompt", "")
#     APIKey = request.args.get("apikey", "")

#     url = 'https://api.openai.com/v1/chat/completions'
#     headers = {
#         'Content-Type': 'application/json',
#         'Authorization': f'Bearer {APIKey}'
#     }
#     data = {
#         "model": target_model,
#         "messages": [
#             {"role": "user", "content": target_prompt}
#         ],
#         "max_tokens": 1024,
#         "temperature": 0.5,
#         "top_p": 1
#     }
#     try:
#         print("start")
#         response = requests.post(url, headers=headers, json=data)
#         print(response.status_code)
#         if response.status_code == 200:
#             result = response.json()
#             return result
#         else:
#             return "Empty"
#     except Exception as e:
#         return (str(e))



if __name__ == "__main__":
    app.run()
