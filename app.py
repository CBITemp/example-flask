import requests
from flask import Flask, jsonify, request, Response, stream_with_context
from flask_cors import CORS
import json
import os
import traceback
import gzip
from io import BytesIO

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
    
    try:
        response = requests.request(
            method=request.method,
            url=url,
            headers=headers,
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False)
        
        # Check for Content-Encoding header
        content_encoding = response.headers.get('Content-Encoding')
        
        def generate():
            if content_encoding == 'gzip':
                # Decompress gzipped content
                buffer = BytesIO(response.content)
                with gzip.GzipFile(fileobj=buffer, mode='rb') as f:
                    yield f.read()
            else:
                # If not gzipped, yield content as is
                yield response.content
        
        # Filter out headers not to be forwarded
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in response.headers.items()
                   if name.lower() not in excluded_headers]
        
        return Response(stream_with_context(generate()), 
                        response.status_code, 
                        headers)
    
    except requests.RequestException as e:
        app.logger.error(f"Request error: {str(e)}")
        return jsonify({"error": "Request to Telegraph failed", "details": str(e)}), 500
    
    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500


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
