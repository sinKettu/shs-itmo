from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
from urls import URLHandler


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def __init__(self):
        super().__init__(self)
        self.uhandler = URLHandler()

    def add_headers(self, headers):
        for header, content in headers:
            self.send_header(header, content)
        super().end_headers(self)

    def do_GET(self):
        path_content = self.path.split("?", 1)
        url = path_content[0]
        data = parse_qs(path_content[1]) if len(path_content) == 2 else {}
        method = "GET"
        in_headers = self.headers

        status, data, headers = self.uhandler.handle(
            url,
            method,
            in_headers,
            data
        )

        self.send_response(status)
        self.add_headers(headers)
        self.wfile.write(data)
