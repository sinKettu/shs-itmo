#!/bin/python3
import sys

import argparse
from http.server import HTTPServer
from hashlib import sha256

import HTTPRequestHandler as rh
import exceptions
import yaml

ignore_ip = set()


class SimpleHTTPServer(HTTPServer):
    def __init__(self, *args, **kwargs):
        self.ip_to_ignore = ignore_ip
        del kwargs["ignore_ip"]
        super(SimpleHTTPServer, self).__init__(*args, **kwargs)
    
    def verify_request(self, request, client_address):
        return client_address[0] not in self.ip_to_ignore

    def _handle_request_noblock(self):
        """Handle one request, without blocking.

        I assume that selector.select() has returned that the socket is
        readable before this function was called, so there should be no risk of
        blocking in get_request().
        """
        try:
            request, client_address = self.get_request()
        except OSError:
            return
        if self.verify_request(request, client_address):
            try:
                self.process_request(request, client_address)
            except exceptions.RebootCall:
                raise
            except Exception:
                self.handle_error(request, client_address)
                self.shutdown_request(request)
            except:
                self.shutdown_request(request)
                raise
        else:
            print(f"Request from {client_address} blocked", flush=True)
            self.shutdown_request(request)


def handle_arguments():
    """
        Parsing cmd arguments
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("-a", dest="address", type=str,
                        default="", help="Bind Address")
    parser.add_argument("-p", dest="port", type=int,
                        default=0, help="Port to listen to")
    parser.add_argument("-o", dest="stdout", help="Path to log stdout",
                        default=None)
    parser.add_argument("-e", dest="stderr", help="Path to log stderr",
                        default=None)
    parser.add_argument("-b", dest="ban", type=str,
                        default="",
                        help="Path to IP ban list")
    parser.add_argument("-w", dest="watch", type=str,
                        default="",
                        help="Path to list of pages to alert about visits"),
    parser.add_argument("-c", dest="config", type=str,
                        default="config/config.yaml",
                        help="Path to config file to use. Given cmd " +
                             "parameters will overwrite config parameters")
    args = parser.parse_args()

    if args.config:
        try:
            fin = open(args.config, "r")
            data = fin.read()
            fin.close()
            config = yaml.load(data, yaml.SafeLoader)["config"]
        except Exception as e:
            print(f"Error: cannot read config file: {e}", flush=True)
            exit(-1)

    cmd_config = {
        "address": args.address,
        "port": args.port,
        "stdout": args.stdout,
        "stderr": args.stderr,
        "ban": args.ban,
        "watch": args.watch
    }

    for key in cmd_config:
        if cmd_config[key]:
            config[key] = cmd_config[key]

    return config


def load_ip_to_ignore(pth: str):
    global ignore_ip
    try:
        fin = open(pth, "r")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr, flush=True)

    ignore_ip = set([i.strip() for i in fin.read().split("\n")])


def handler_factory(parameters: dict,
                    change_token: bool = False,
                    reload_handlers: bool = False,
                    reload_ip_to_ignore: bool = False,
                    reload_watch_list: bool = False):
    """
        "Class Factory" needed to implement ability
        to pass parameters to HTTP handler.
    """
    if change_token:
        token = rh.generate_session_token()
        print(f"Session Token: {token}", flush=True)
        print(f"cURL: curl -H \"X-Session-Token: {token}\" " +
              f"http://127.0.0.1:{parameters['port']}/server/control/?action=")
        h = sha256()
        h.update(token.encode("utf-8"))

    if reload_handlers and change_token:
        rh.prepare_handlers(h.digest())
    elif reload_handlers and not change_token:
        rh.prepare_handlers(b"")
    
    if reload_ip_to_ignore:
        load_ip_to_ignore(parameters["ban"])

    if reload_watch_list:
        rh.load_watch_list(parameters["watch"])

    class CustomHandler(rh.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            self.server_parameters = parameters
            super(CustomHandler, self).__init__(*args, **kwargs)

    return CustomHandler


def configure_output(out, err):
    if out is not None:
        try:
            fout = open(out, "a")
            sys.stdout = fout
        except Exception as e:
            print(f"Error: Could not redirect stdout: {e}",
                  file=sys.stderr,
                  flush=True)
            exit(-1)
    if err is not None:
        try:
            ferr = open(err, "a")
            sys.stderr = ferr
        except Exception as e:
            print(f"Error: Could not redirect stderr: {e}",
                  file=sys.stderr,
                  flush=True)
            exit(-1)


def main():
    args = handle_arguments()
    bind_addr = args["address"], args["port"]
    configure_output(args["stdout"], args["stderr"])

    new_handler = handler_factory(args, True, True, True, True)
    httpd = SimpleHTTPServer(bind_addr, new_handler, ignore_ip=ignore_ip)
    print(f"Server listens to {bind_addr}", flush=True)

    while True:
        try:
            httpd.serve_forever()
        except exceptions.RebootCall:
            httpd.shutdown()
            httpd.server_close()
            new_handler = handler_factory(args,
                                          reload_handlers=True,
                                          reload_ip_to_ignore=True,
                                          reload_watch_list=True)

            httpd = SimpleHTTPServer(bind_addr,
                                     new_handler,
                                    ignore_ip=ignore_ip)
            print("Server rebooted", flush=True)
            continue
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr, flush=True)
            httpd.shutdown()


if __name__ == "__main__":
    main()
