# You are able to map dynamic and re pages
# dymaic handlers must accept method, incomming headers and data
# re handlers must accept url, method, incomming headers and data
from hashlib import sha256

cookies = {}
users = {}


def get_mappings():
    handlers_mapping = [
        ("/csrf-naive/", handle_naive),
        ("/csrf-token/", handle_token),
        ("/origin-referer-protected/", handle_origin_protected),
        ("/token-cors-protected/", handle_token_protected),
        ("/register/", handle_register),
        ("/login/", handle_login)
    ]

    return handlers_mapping


def handle_naive(method, headers, data):
    return 200, b"", {}


def handle_token(method, headers, data):
    return 200, b"", {}


def handle_origin_protected(method, headers, data):
    return 200, b"", {}


def handle_token_protected(method, headers, data):
    return 200, b"", {}


def handle_register(method, headers, data):
    if method == "GET":
        fin = open("static/register.html", "rb")
        d = fin.read()
        fin.close()
        return 200, d, {"content-type": "text/html; charset=UTF-8"}
    elif method == "POST":
        d = data["body"].decode("utf-8").split("&")
        d = dict([tuple(i.split("=")) for i in d])
        login = d["login"]
        password = d["password"]
        if password != d["password_confirm"]:
            return 403, b"Passwords do not match", {}
        elif login in users:
            return 403, b"User already exists", {}

        h = sha256()
        h.update(password.encode("utf-8"))
        users[login] = h.digest()
        fin = open("static/suc_reg.html", "rb")
        d = fin.read()
        fin.close()
        return 200, d, {"content-type": "text/html; charset=UTF-8"}


def handle_login(method, headers, data):
    return 200, b"", {}
