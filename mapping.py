# You are able to map dynamic and re pages
# dymaic handlers must accept method, incomming headers and data
# re handlers must accept url, method, incomming headers and data
from hashlib import sha256
from datetime import datetime
import re

# Cookies storage
cookies = {}
# Users storage
users = {}
# Forum's messages storage
messages = []
# Users CSRF-tokens' storage
tokens = {}

url_encoded_re = r"\%[0-9A-Za-z]{2,2}"


def get_mappings():
    # map URI and function to handle it
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
    # Naive page without any protection
    global messages
    if method == "GET":
        if not ("Cookie" in headers and "userid=" in headers["Cookie"]):
            fin = open("static/main_anon.html", "rb")
            d = fin.read()
            fin.close()
            return 200, d, {"content-type": "text/html; charset=UTF-8"}
        cookie = headers["Cookie"].split("userid=")[-1].split(";")[0]
        if cookie not in cookies:
            fin = open("static/main_anon.html", "rb")
            d = fin.read()
            fin.close()
            return 200, d, {"content-type": "text/html; charset=UTF-8"}

        login = cookies[cookie]
        fin = open("static/main.temp", "r")
        d = fin.read()
        fin.close()
        d = re.sub(r"USERNAME", login, d)
        d = re.sub(r"_URL_", "/csrf-naive/", d)

        fin = open("static/record.temp", "r")
        mt = fin.read()
        fin.close()
        mes_parsed = ""
        for i in messages:
            l, m = i
            tmp = re.sub(r"USERNAME", l, mt)
            tmp = re.sub(r"__MESSAGE__", m, tmp)
            mes_parsed = f"{mes_parsed}{tmp}"
        d = re.sub(r"__MESSAGES__", mes_parsed, d).encode("utf-8")

        return 200, d, {"content-type": "text/html; charset=UTF-8"}
    elif method == "POST":
        cookie = headers.get("Cookie", "").split("userid=")[-1].split(";")[0]
        if not(cookie in cookies):
            fin = open("static/main_anon.html", "rb")
            d = fin.read()
            fin.close()
            return 200, d, {"content-type": "text/html; charset=UTF-8"}

        login = cookies[cookie]
        d = data["body"].decode("utf-8").split("&")
        d = dict([tuple(i.split("=")) for i in d])
        message = d["message"].replace("+", " ")

        for i in re.finditer(url_encoded_re, message):
            tmp = i.group(0)
            n = int(tmp[1:].lower(), 16)
            message = message.replace(tmp, chr(n))

        messages.append((login, message))
        return 301, b"", {"Location": "/csrf-naive/"}


def handle_token(method, headers, data):
    # Page with token protection, but misconfigured COP
    global messages
    global tokens
    if method == "GET":
        if not ("Cookie" in headers and "userid=" in headers["Cookie"]):
            fin = open("static/main_anon.html", "rb")
            d = fin.read()
            fin.close()
            return 200, d, {"content-type": "text/html; charset=UTF-8"}
        cookie = headers["Cookie"].split("userid=")[-1].split(";")[0]
        if cookie not in cookies:
            fin = open("static/main_anon.html", "rb")
            d = fin.read()
            fin.close()
            return 200, d, {"content-type": "text/html; charset=UTF-8"}

        login = cookies[cookie]
        fin = open("static/main_token.temp", "r")
        d = fin.read()
        fin.close()

        d = re.sub(r"USERNAME", login, d)
        h = sha256()
        h.update(cookie.encode("utf-8"))
        h.update(str(datetime.now()).encode("utf-8"))
        d = re.sub(r"_TOKEN_", h.hexdigest(), d)

        tmp = tokens.get(cookie, set())
        tmp.add(h.hexdigest())
        tokens[cookie] = tmp

        fin = open("static/record.temp", "r")
        mt = fin.read()
        fin.close()
        mes_parsed = ""
        for i in messages:
            l, m = i
            tmp = re.sub(r"USERNAME", l, mt)
            tmp = re.sub(r"__MESSAGE__", m, tmp)
            mes_parsed = f"{mes_parsed}{tmp}"
        d = re.sub(r"__MESSAGES__", mes_parsed, d).encode("utf-8")

        if "Origin" in headers:
            # This headers allow an attacker to get user's token
            hdrs = {
                "Access-Control-Allow-Origin": headers["Origin"],
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS, HEAD",
                "content-type": "text/html; charset=UTF-8"
            }
        else:
            hdrs = {
                "content-type": "text/html; charset=UTF-8"
            }

        return 200, d, hdrs
    elif method == "POST":
        cookie = headers.get("Cookie", "").split("userid=")[-1].split(";")[0]
        if not(cookie in cookies):
            fin = open("static/main_anon.html", "rb")
            d = fin.read()
            fin.close()
            return 200, d, {"content-type": "text/html; charset=UTF-8"}

        login = cookies[cookie]
        d = data["body"].decode("utf-8").split("&")
        d = dict([tuple(i.split("=")) for i in d])
        tkns = tokens.get(cookie, set())

        # Protection by users' tokens
        if d["token"] not in tkns:
            return 403, b"CSRF Protection", {}
        else:
            tkns.remove(d["token"])
            tokens[cookie] = tkns

        message = d["message"].replace("+", " ")
        for i in re.finditer(url_encoded_re, message):
            tmp = i.group(0)
            n = int(tmp[1:].lower(), 16)
            message = message.replace(tmp, chr(n))

        messages.append((login, message))
        return 301, b"", {"Location": "/csrf-token/"}


def handle_origin_protected(method, headers, data):
    # The same as "naive", but with protection
    global messages
    if method == "GET":
        if not ("Cookie" in headers and "userid=" in headers["Cookie"]):
            fin = open("static/main_anon.html", "rb")
            d = fin.read()
            fin.close()
            return 200, d, {"content-type": "text/html; charset=UTF-8"}
        cookie = headers["Cookie"].split("userid=")[-1].split(";")[0]
        if cookie not in cookies:
            fin = open("static/main_anon.html", "rb")
            d = fin.read()
            fin.close()
            return 200, d, {"content-type": "text/html; charset=UTF-8"}

        login = cookies[cookie]
        fin = open("static/main.temp", "r")
        d = fin.read()
        fin.close()
        d = re.sub(r"USERNAME", login, d)
        d = re.sub(r"_URL_", "/origin-referer-protected/", d)

        fin = open("static/record.temp", "r")
        mt = fin.read()
        fin.close()
        mes_parsed = ""
        for i in messages:
            l, m = i
            tmp = re.sub(r"USERNAME", l, mt)
            tmp = re.sub(r"__MESSAGE__", m, tmp)
            mes_parsed = f"{mes_parsed}{tmp}"
        d = re.sub(r"__MESSAGES__", mes_parsed, d).encode("utf-8")

        return 200, d, {"content-type": "text/html; charset=UTF-8"}
    elif method == "POST":
        cookie = headers.get("Cookie", "").split("userid=")[-1].split(";")[0]
        if not(cookie in cookies):
            fin = open("static/main_anon.html", "rb")
            d = fin.read()
            fin.close()
            return 200, d, {"content-type": "text/html; charset=UTF-8"}

        # Protection by Origin/Referer checks via regexes
        if "Origin" in headers:
            if not re.match(
                    r"^https?:\/\/test\.itmo(:{1,1}[0-9]{1,5}){0,1}$",
                    headers["Origin"]):
                return 403, b"CSRF Protection", {}
        elif "Referer" in headers:
            if not re.match(
                    r"^https?:\/\/test\.itmo(:{1,1}[0-9]{1,5}){0,1}\/.*$",
                    headers["Origin"]):
                return 403, b"CSRF Protection", {}
        else:
            return 403, b"CSRF Protection", {}

        login = cookies[cookie]
        d = data["body"].decode("utf-8").split("&")
        d = dict([tuple(i.split("=")) for i in d])
        message = d["message"].replace("+", " ")

        for i in re.finditer(url_encoded_re, message):
            tmp = i.group(0)
            n = int(tmp[1:].lower(), 16)
            message = message.replace(tmp, chr(n))

        messages.append((login, message))
        return 301, b"", {"Location": "/origin-referer-protected/"}


def handle_token_protected(method, headers, data):
    # The same as token-protected but with CORS (COP)
    global messages
    global tokens
    if method == "GET":
        if not ("Cookie" in headers and "userid=" in headers["Cookie"]):
            fin = open("static/main_anon.html", "rb")
            d = fin.read()
            fin.close()
            return 200, d, {"content-type": "text/html; charset=UTF-8"}
        cookie = headers["Cookie"].split("userid=")[-1].split(";")[0]
        if cookie not in cookies:
            fin = open("static/main_anon.html", "rb")
            d = fin.read()
            fin.close()
            return 200, d, {"content-type": "text/html; charset=UTF-8"}

        login = cookies[cookie]
        fin = open("static/main_token.temp", "r")
        d = fin.read()
        fin.close()
        d = re.sub(r"USERNAME", login, d)
        d = re.sub(r"_URL_", "/token-cors-protected/", d)
        h = sha256()
        h.update(cookie.encode("utf-8"))
        h.update(str(datetime.now()).encode("utf-8"))
        d = re.sub(r"_TOKEN_", h.hexdigest(), d)
        tmp = tokens.get(cookie, set())
        tmp.add(h.hexdigest())
        tokens[cookie] = tmp

        fin = open("static/record.temp", "r")
        mt = fin.read()
        fin.close()
        mes_parsed = ""
        for i in messages:
            l, m = i
            tmp = re.sub(r"USERNAME", l, mt)
            tmp = re.sub(r"__MESSAGE__", m, tmp)
            mes_parsed = f"{mes_parsed}{tmp}"
        d = re.sub(r"__MESSAGES__", mes_parsed, d).encode("utf-8")

        # A lack of CORS headers in response is a protection itself
        return 200, d, {"content-type": "text/html; charset=UTF-8"}
    elif method == "POST":
        cookie = headers.get("Cookie", "").split("userid=")[-1].split(";")[0]
        if not(cookie in cookies):
            fin = open("static/main_anon.html", "rb")
            d = fin.read()
            fin.close()
            return 200, d, {"content-type": "text/html; charset=UTF-8"}

        login = cookies[cookie]
        d = data["body"].decode("utf-8").split("&")
        d = dict([tuple(i.split("=")) for i in d])
        tkns = tokens.get(cookie, set())

        # Protection by tokens
        if d["token"] not in tkns:
            return 403, b"CSRF Protection", {}
        else:
            tkns.remove(d["token"])
            tokens[cookie] = tkns

        message = d["message"].replace("+", " ")
        for i in re.finditer(url_encoded_re, message):
            tmp = i.group(0)
            n = int(tmp[1:].lower(), 16)
            message = message.replace(tmp, chr(n))

        messages.append((login, message))
        return 301, b"", {"Location": "/token-cors-protected/"}


def handle_register(method, headers, data):
    # The page to register new users
    global users
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
    return 404, b"", {}


def handle_login(method, headers, data):
    # The page to log in as a user and get cookies
    global users
    global cookies
    if method == "GET":
        fin = open("static/login.html", "rb")
        d = fin.read()
        fin.close()
        return 200, d, {"content-type": "text/html; charset=UTF-8"}
    elif method == "POST":
        d = data["body"].decode("utf-8").split("&")
        d = dict([tuple(i.split("=")) for i in d])
        login = d["login"]
        password = d["password"]
        h = sha256()
        h.update(password.encode("utf-8"))
        if login in users and h.digest() == users[login]:
            h = sha256()
            h.update(users[login])
            dt = str(datetime.now()).encode("utf-8")
            h.update(dt)
            hdrs = {
                "Set-Cookie": f"userid={h.hexdigest()}; HttpOnly; Path=/",
                "content-type": "text/html; charset=UTF-8"
            }
            cookies[h.hexdigest()] = login
            fin = open("static/suc_login.html", "rb")
            d = fin.read()
            fin.close()
            return 200, d, hdrs
        else:
            return 403, b"Wrong login and/or password", {}
