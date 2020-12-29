# You are able to map dynamic and re pages
# dymaic handlers must accept method, incomming headers and data
# re handlers must accept url, method, incomming headers and data


def get_mappings():
    handlers_mapping = [
        ("/", handle_default),
        ("/redirect", handle_redirect)
    ]

    return handlers_mapping


def handle_default(method, headers, data):
    return 200, b"Hello!", {}


def handle_redirect(method, headers, data):
    if "url" in data["url"]:
        url = data["url"]["url"]
    else:
        url = "127.0.0.1"

    return 302, b"", {
        "Location": f"http://{url}/"
    }
