from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs

from urls import URLHandler, setup_url_handler, get_url_handler
from mappings import default

# Need to write accordance of dynamic page url and handler-function here
__handlers_mapping = [
    ("/", default.handle_default)
]


def prepare_handlers():
    """
        The routine prepares URLHandler to work
        with HTTP handler. Need to be called berfore
        HTTPServer() initialization.
    """
    setup_url_handler()
    uhandler = get_url_handler()
    for mapping in __handlers_mapping:
        uhandler.map_url_with_handler(*mapping)


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

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
        if not url[-1] == "/":  # crutch needed to be fixed with redirect
            url += "/"
        data = parse_qs(path_content[1]) if len(path_content) == 2 else {}
        method = "GET"
        in_headers = dict(self.headers)

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
        if not url[-1] == "/":  # crutch needed to be fixed with redirect
            url += "/"
        in_headers = dict(self.headers)
        content_len = int(in_headers.get("Content-Length"))
        data = self.rfile.read(content_len)
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
