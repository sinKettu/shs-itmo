from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs

from urls import URLHandler

from mappings import default


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, request, client_address, server):
        self.uhandler = URLHandler()
        self.uhandler.update_urls_info()
        self.uhandler.map_url_with_handler("/", default.handle_default)
        super().__init__(request, client_address, server)

    def add_headers(self, headers):
        self.send_header("Server", "None")
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

        status, data, headers = self.uhandler.handle(
            url,
            method,
            in_headers,
            data
        )

        self.send_response(status)
        self.add_headers(headers)
        self.wfile.write(data)
