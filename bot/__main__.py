from bot import app
from flask import Flask
from threading import Thread

web_server = Flask(__name__) 

@web_server.route("/")
def fun():
    return "<h1>Hello World</h1>"

def web():
    web_server.run(host="0.0.0.0", port=5000)

if __name__ == "__main__":
    t = Thread(target=web)
    t.start()
    
    app.run()