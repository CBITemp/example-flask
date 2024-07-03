import requests
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)

# Configure Flask logger
app.logger.setLevel('INFO')

TELEGRAPH_URL = 'https://api.openai.com'

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy(path):
    url = f"{TELEGRAPH_URL}/{path}"
    headers = {key: value for (key, value) in request.headers if key != 'Host'}
    headers['Host'] = TELEGRAPH_URL.replace('https://', '')

    app.logger.info(f"Incoming request: {request.method} {url}")
    app.logger.info(f"Request headers: {headers}")

    try:
        app.logger.info("Sending request to upstream server")
        response = requests.request(
            method=request.method,
            url=url,
            headers=headers,
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False
        )
        app.logger.info(f"Received response from upstream server. Status code: {response.status_code}")
        app.logger.info(f"Response headers: {dict(response.headers)}")

        app.logger.info(f"Original response encoding: {response.encoding}")
        response.encoding = 'utf-8'
        app.logger.info("Forced response encoding to UTF-8")

        def generate():
            app.logger.info("Starting to generate response content")
            for chunk in response.iter_content(chunk_size=4096, decode_unicode=True):
                if chunk:
                    app.logger.info(f"Processing chunk. Type: {type(chunk)}, Length: {len(chunk)}")
                    app.logger.info(f"Sample of chunk content: {chunk[:100]}")
                    yield chunk
            app.logger.info("Finished generating response content")

        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in response.raw.headers.items()
                   if name.lower() not in excluded_headers]
        app.logger.info(f"Filtered response headers: {headers}")

        content_type = response.headers.get('Content-Type', 'text/plain; charset=utf-8')
        app.logger.info(f"Setting Content-Type to: {content_type}")

        app.logger.info("Preparing to send response to client")
        return Response(generate(), status=response.status_code, headers=headers, content_type=content_type)

    except requests.RequestException as e:
        app.logger.error(f"Request exception occurred: {str(e)}")
        return str(e), 500



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
