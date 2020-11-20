# You are able to map dynamic and re pages
# dymaic handlers must accept method, incomming headers and data
# re handlers must accept url, method, incomming headers and data


def get_mappings():
    handlers_mapping = [
        ("/", handle_default)
    ]

    return handlers_mapping


def handle_default(method, headers, data):
    return 200, b"Hello!", {}
