from flask import Flask, request, send_from_directory
from gevent.pywsgi import WSGIServer
import flask_sse
import threading, signal
import json
import keycapture

app = Flask(__name__)
# https://github.com/singingwolfboy/flask-sse/issues/7
channel = flask_sse.Channel()
klogger = keycapture.Keycapture()

server = WSGIServer(("", 5000), app)
klthread = threading.Thread(target=klogger.start_capture, daemon=True)

@app.route('/subscribe')
def subscribe():
    return channel.subscribe()

@app.route('/publish', methods=['POST'])
def publish():
    channel.publish(json.dumps(request.json))
    return "OK"

# Path for our main Svelte page
@app.route("/")
def base():
    return send_from_directory('client/public', 'index.html')

# Path for all the static files (compiled JS/CSS, etc.)
@app.route("/<path:path>")
def home(path):
    return send_from_directory('client/public', path)

@app.route("/shutdown")
def shutdown():
    print("Shutdown request")
    server.stop()
    return "Goodbye, remember to hit any key"

def ctrlc_handler(signum, frame):
    server.stop()

def main():
    klthread.start()

    signal.signal(signal.SIGINT, ctrlc_handler)
    server.serve_forever()

    print("Goodbye")

if __name__ == "__main__":
	main()