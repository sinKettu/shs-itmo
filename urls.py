from os import path
import yaml

# Global private storage for main URLHandler instance
__uhandler = None


class URLHandler:

    not_existing_page = 0
    dynamic_page = 1
    static_page = 2

    def __init__(self):
        self.urls_path = "config/urls.yaml"
        self.urls = {}

    def __parse_urls(self):
        """
            Parsing YAML config with urls to dictonary
            with checks for parameters
        """
        fin = open(self.urls_path, "r")
        urls = fin.read()
        fin.close()
        urls = yaml.load(urls, Loader=yaml.SafeLoader)

        for url in urls:
            tp = urls[url].get("type", None)
            if tp is None:
                raise NotImplementedError("Parsing Error: wrong type")
            elif tp == "none":
                urls[url]["type"] = self.not_existing_page
            elif tp == "dynamic":
                hlr = urls[url].get("handler", 0)
                urls[url]["type"] = self.dynamic_page
                if hlr is not None:
                    err = "Parsing Error: wrong dynamic handler"
                    raise NotImplementedError(err)
            elif tp == "static":
                urls[url]["type"] = self.static_page
                hlr = urls[url].get("handler", None)
                if hlr is None:
                    err = "Parsing Error: static handler missed"
                    raise NotImplementedError(err)

                if not (path.exists(hlr) and path.isfile(hlr)):
                    err = f"Parsing Error: file {hlr} not found"
                    raise NotImplementedError(err)
            else:
                err = "Parsing Error: wrong url type"
                raise NotImplementedError(err)

            methods = urls[url].get("methods", None)
            if methods is None:
                urls[url]["methods"] = {"GET"}
            else:
                urls[url]["methods"] = {i.upper() for i in methods}

        return urls

    def update_urls_info(self):
        self.urls = self.__parse_urls()

    def map_url_with_handler(self, url: str, handler):
        """
            Mapping dynamic pages with handler-functions to process it
        """
        if url not in self.urls:
            raise NotImplementedError(f"Cannot find url '{url}'")
        elif self.urls[url]["type"] != self.dynamic_page:
            raise NotImplementedError(f"Cannot map not dynamic url '{url}'")
        elif self.urls[url]["handler"] is not None:
            raise NotImplementedError(f"Handler already exists")
        else:
            self.urls[url]["handler"] = handler

    def handle(self, url: str, method: str, in_headers: dict, data: bytes):
        """
            Handling requests by type of url
        """
        if url not in self.urls:
            return 404, b"Page Not Found", {}
        elif method not in self.urls[url]["methods"]:
            return 405, b"Method not Allowed", {}
        elif self.urls[url]["type"] == self.not_existing_page:
            headers = self.urls[url].get("headers", {})
            return 404, b"Page Not Found", headers
        elif self.urls[url]["type"] == self.static_page:
            headers = self.urls[url].get("headers", {})
            fin = open(self.urls[url]["handler"], "rb")
            data = fin.read()
            fin.close()
            return 200, data, headers
        elif self.urls[url]["type"] == self.dynamic_page:
            headers = self.urls[url].get("headers", {})
            status, data, headers = self.urls[url]["handler"](
                method,
                in_headers,
                data
            )

            return status, data, headers


def setup_url_handler():
    """
        Initialize URLHandler instance if it does not exist
    """
    global __uhandler
    if __uhandler is not None:
        return

    __uhandler = URLHandler()
    __uhandler.update_urls_info()


def get_url_handler() -> URLHandler:
    return __uhandler
