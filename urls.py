from os import path
import yaml
import re

# Global private storage for main URLHandler instance
__uhandler = None


class URLHandler:

    not_existing_page = 0
    dynamic_page = 1
    static_page = 2
    re_page = 3

    def __init__(self):
        self.urls_path = "config/urls.yaml"
        self.urls = {}
        self.re_urls = {}

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
                hlr = urls[url].get("handler", None)
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
            elif tp == "re":
                urls[url]["type"] = self.re_page
                hlr = urls[url].get("handler", None)
                if hlr is not None:
                    err = f"Parsing Error: wrong handler for {url}"
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
        parsed = self.__parse_urls()
        self.re_urls = {i: parsed[i] for i in parsed
                        if parsed[i]["type"] == self.re_page}

        self.urls = {i.replace("/", ""): parsed[i] for i in parsed
                        if parsed[i]["type"] != self.re_page}

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

    def __check_and_process(self,
                            url_ex: str,
                            method: str,
                            in_headers: dict,
                            data: bytes):
        if method not in self.urls[url_ex]["methods"]:
            return 405, b"Method not Allowed", {}

        elif self.urls[url_ex]["type"] == self.not_existing_page:
            headers = self.urls[url_ex].get("headers", {})
            return 404, b"Page Not Found", headers

        elif self.urls[url_ex]["type"] == self.static_page:
            headers = self.urls[url_ex].get("headers", {})
            fin = open(self.urls[url_ex]["handler"], "rb")
            data = fin.read()
            fin.close()
            return 200, data, headers

        elif self.urls[url_ex]["type"] == self.dynamic_page and \
             self.urls[url_ex]["handler"] is not None:
            headers = self.urls[url_ex].get("headers", {})
            status, data, headers = self.urls[url_ex]["handler"](
                method,
                in_headers,
                data
            )
            return status, data, headers

        elif self.urls[url_ex]["type"] == self.dynamic_page and \
             self.urls[url_ex]["handler"] is None:
             return 500, b"Internal Server Error", {}

        else:
            return 404, b"Page Not Found", {}

    def handle(self, url: str, method: str, in_headers: dict, data: bytes):
        formatted_url = url.replace("/", "")
        if formatted_url in self.urls:
            return self.__check_and_process(
                formatted_url,
                method,
                in_headers,
                data
            )

        for url_ex in self.re_urls:
            if re.sub(url_ex, "", url):
                continue

            elif method not in self.re_urls[url_ex]["methods"]:
                return 405, b"Method not Allowed", {}

            elif self.re_urls[url_ex]["type"] == self.not_existing_page:
                headers = self.urls[url_ex].get("headers", {})
                return 404, b"Page Not Found", headers

            elif self.re_urls[url_ex]["handler"] is not None:
                headers = self.urls[url_ex].get("headers", {})
                status, data, headers = self.urls[url_ex]["handler"](
                    url,
                    method,
                    in_headers,
                    data
                )

            elif (path.abspath(f".{url}").startswith(path.abspath("."))
                    and path.exists(f".{url}")
                    and path.isfile(f".{url}")):

                headers = self.re_urls[url_ex].get("headers", {})
                fin = open(f".{url}", "rb")
                data = fin.read()
                fin.close()
                return 200, data, headers

        return 404, b"Page Not Found", {}


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
