import mimetypes
import pathlib
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import asyncio
import logging
from multiprocessing import Process
from datetime import datetime
import json
import websockets
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import sys


class HttpHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        async def send_message(message_data):
            uri = "ws://localhost:5000"
            async with websockets.connect(uri) as websocket:
                await websocket.send(message_data)

        data = self.rfile.read(int(self.headers["Content-Length"]))
        print(data)
        data_parse = urllib.parse.unquote_plus(data.decode())
        print(data_parse)
        data_dict = {
            key: value for key, value in [el.split("=") for el in data_parse.split("&")]
        }
        print(data_dict)

        asyncio.run(send_message(json.dumps(data_dict)))

        self.send_response(302)
        self.send_header("Location", "redirect.html")
        self.end_headers()

    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == "/":
            self.send_html_file("index.html")
        elif pr_url.path == "/message":
            self.send_html_file("message.html")
        elif pr_url.path == "/view-messages":
            self.send_html_file("view-messages.html")
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file("error.html", 404)

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        with open(filename, "rb") as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", "text/plain")
        self.end_headers()
        with open(f".{self.path}", "rb") as file:
            self.wfile.write(file.read())


def run_http_server(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ("0.0.0.0", 3000)
    http = server_class(server_address, handler_class)
    logging.info(f"HTTP server started on {server_address}")
    http.serve_forever()


class WebSocketServer:
    def __init__(self):
        # self.client = MongoClient("mongodb://localhost:27017/")
        try:
            print("Connect to MongoDB . . .")
            self.client = MongoClient("mongodb://localhost:27017/")
            # Attempt a simple operation to confirm connection
            self.client.admin.command("ismaster")
            logging.info("Websocket server successfully connected to MongoDB!")
            # print("Successfully connected to MongoDB!")
        except ConnectionFailure as e:
            # print(f"MongoDB connection failed: {e}")
            logging.error(f"MongoDB connection failed: {e}")
            sys.exit(1)

        self.db = self.client["db_messages"]
        self.collection = self.db["messages"]

    async def ws_handler(self, websocket):
        async for message in websocket:
            data = json.loads(message)

            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

            message_data = {
                "date": date,
                "username": data["username"],
                "message": data["message"],
            }

            # save message to DB
            self.collection.insert_one(message_data)
            logging.info(f"Message: {message_data} saved to db.")


async def start_websocket_server():
    server = WebSocketServer()
    server_ip = "0.0.0.0"
    server_port = 5000
    async with websockets.serve(server.ws_handler, server_ip, server_port):
        # logging.info(f"WebSocket server started on {server_ip}:{server_port}")
        await asyncio.Future()


def run_websocket_server():
    asyncio.run(start_websocket_server())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    http_proc = Process(target=run_http_server)
    websocket_proc = Process(target=run_websocket_server)

    http_proc.start()
    websocket_proc.start()

    websocket_proc.join()
    http_proc.join()
