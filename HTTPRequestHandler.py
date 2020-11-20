from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs

from urls import URLHandler, setup_url_handler, get_url_handler
from mapping import get_mappings





class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        self.prepare_handlers()
        super(SimpleHTTPRequestHandler, self).__init__(*args, **kwargs)

    def prepare_handlers(self):
        """
            The routine prepares URLHandler to work
            with HTTP handler. Need to be called berfore
            HTTPServer() initialization.
        """
        setup_url_handler()
        uhandler = get_url_handler()
        mappings = get_mappings()
        for mapping in mappings:
            uhandler.map_url_with_handler(*mapping)

    def log_message(self, *args):
        """
            Overriding built-in method for more smart logging
        """
        tm = self.log_date_time_string().encode("utf-8")
        addr, port = self.client_address
        msg = tm + b"\n" + f"Request from: {addr}:{port}\n\n".encode("utf-8")
        msg += str(self.requestline).encode("utf-8") + b"\n"
        msg += str(self.headers).encode("utf-8")
        length = int(self.headers.get("Content-Length", 0))

        if self.read_data:
            msg += self.read_data

        msg += b"\n-------------------------------------------------------\n\n"
        try:
            print(msg.decode("utf-8"))
        except UnicodeDecodeError:
            print(msg)

    def version_string(self):
        return "Unknown Server"

    def add_headers(self, headers):
        for header in headers:
            content = headers[header]
            self.send_header(header, content)
        super().end_headers()

    def do_GET(self):
        path_content = self.path.split("?", 1)
        url = path_content[0]
        data = parse_qs(path_content[1]) if len(path_content) == 2 else {}
        method = "GET"
        in_headers = dict(self.headers)
        self.read_data = b""

        uhandler = get_url_handler()
        status, data, headers = uhandler.handle(
            url,
            method,
            in_headers,
            data
        )

        self.send_response(status)
        self.add_headers(headers)
        self.wfile.write(data)

    def do_POST(self):
        url = self.path.split("?", 1)[0]
        in_headers = dict(self.headers)
        content_len = int(in_headers.get("Content-Length", 0))
        data = self.rfile.read(content_len)
        self.read_data = data
        method = "POST"

        uhandler = get_url_handler()
        status, data, headers = uhandler.handle(
            url,
            method,
            in_headers,
            data
        )

        self.send_response(status)
        self.add_headers(headers)
        self.wfile.write(data)
