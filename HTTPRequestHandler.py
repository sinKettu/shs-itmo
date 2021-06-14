from datetime import datetime
from time import asctime
from hashlib import sha256
from base64 import b64encode
from os import getenv
import random as rand
import sys
import importlib

from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
import requests

import mapping
from urls import URLHandler, setup_url_handler, get_url_handler

pages_to_alert = {}


def generate_session_token():
    """
        Generating token to control server remotely
    """
    seed = str(datetime.now()).encode("utf-8")
    h = sha256()
    h.update(seed)
    seed = h.digest()
    rand.seed(seed)
    token = bytes([rand.randint(0, 255) for i in range(64)])
    return b64encode(token).decode("utf-8")


def prepare_handlers(token: bytes):
    """
        The routine prepares URLHandler to work
        with HTTP handler. Need to be called berfore
        HTTPServer() initialization.
    """

    mapping = importlib.reload(sys.modules["mapping"])
    setup_url_handler(token)
    uhandler = get_url_handler()
    mappings = mapping.get_mappings()
    for mp in mappings:
        uhandler.map_url_with_handler(*mp)


def load_watch_list(pth: str):
    global pages_to_alert
    fin = open(pth, "r")
    pages_to_alert = set([i.strip().replace("/", "")
                          for i in fin.read().split("\n") if i])
    fin.close()


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def log_message(self, *args):
        """
            Overriding built-in method for more smart logging
        """
        try:
            tm = self.log_date_time_string()
            addr, port = self.client_address

            if addr.startswith("172."):
                _addr = self.headers.get("X-Real-IP", None)
                if _addr:
                    addr = _addr

            mark = f"[{tm} | {addr}:{port}] "

            rline = str(self.requestline).replace("\n", f"\n{mark}")
            msg = mark.encode("utf-8")
            msg += rline.encode("utf-8") + b"\n" + mark.encode("utf-8")

            hdrs = str(self.headers).replace("\n", f"\n{mark}")
            msg += hdrs.encode("utf-8")
        except Exception as e:
            msg = f"Error while trying to log message, exception: {e}\n"
            msg = f"{msg}Function args: {args}"
            msg += "\n--------------------------------------------------\n\n"
            print(msg, flush=True, file=sys.stderr)
            return

        try:
            msg += self.read_data
        except Exception as e:
            msg += b"[No `self.read_data`: " + e.encode("utf-8")
            msg += b"\n--------------------------------------------------\n\n"
            print(msg, flush=True, file=sys.stderr)
            return

        msg += b"\n--------------------------------------------------\n\n"
        try:
            print(msg.decode("utf-8"), flush=True)
        except UnicodeDecodeError:
            print(msg, flush=True)

    def version_string(self):
        return "Unknown Server"

    def add_headers(self, headers):
        for header in headers:
            content = headers[header]
            self.send_header(header, content)
        super().end_headers()

    def parse_url_parameters(self, params: str):
        return dict(tuple(i.split("=", 1)) for i in params.split("&") if i)

    def alert_if_needed(self, url: str, addr: str):
        payload = {
            'channel': "@aivanov",
            'username': "secrets_tracker",
            'text':  f"Peer `{addr}` accessed url `{url}` at `{asctime()}`",
            "as_user": "secrets_tracker",
        }

        token = getenv("SLACK_TOKEN")
        s = requests.Session()
        resp = s.post("https://slack.com/api/chat.postMessage",
                      json=payload,
                      headers={
                          "Content-Type": "application/json; charset=utf-8",
                          "Authorization": f"Bearer {token}"
                      })

    def do_GET(self):
        path_content = self.path.split("?", 1)
        url = path_content[0]

        if len(path_content) == 2:
            try:
                url_data = self.parse_url_parameters(path_content[1])
            except Exception:
                url_data = {}
        else:
            url_data = {}

        method = "GET"
        in_headers = dict(self.headers)
        self.read_data = b""
        data = {
            "body": b"",
            "url": url_data
        }

        if url.replace("/", "") in pages_to_alert:
            self.alert_if_needed(url, self.client_address[0])

        uhandler = get_url_handler()
        try:
            status, data, headers = uhandler.handle(
                url,
                method,
                in_headers,
                data
            )

            self.send_response(status)
            self.add_headers(headers)
            self.wfile.write(data)
        except Exception:
            self.send_response(500)
            self.wfile.write(b"Internal Server Error")

    def do_POST(self):
        path_content = self.path.split("?", 1)
        url = path_content[0]

        if len(path_content) == 2:
            try:
                url_data = self.parse_url_parameters(path_content[1])
            except Exception:
                url_data = {}
        else:
            url_data = {}

        in_headers = dict(self.headers)
        content_len = int(in_headers.get("Content-Length", 0))
        data = self.rfile.read(content_len)
        self.read_data = data
        method = "POST"
        data = {
            "body": data,
            "url": url_data
        }

        if url in pages_to_alert:
            self.alert_if_needed(url, self.client_address[0])

        uhandler = get_url_handler()
        try:
            status, data, headers = uhandler.handle(
                url,
                method,
                in_headers,
                data
            )

            self.send_response(status)
            self.add_headers(headers)
            self.wfile.write(data)
        except Exception as e:
            self.send_response(500)
            self.wfile.write(b"Internal Server Error")
