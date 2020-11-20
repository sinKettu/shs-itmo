#!/bin/python3
import sys

import argparse
from http.server import HTTPServer

import HTTPRequestHandler as rh

# TODO:
#   - Parsing config/config
#   - Ban IP list
#   - Alerts
#   - Separate stderr and stdout


class SimpleHTTPServer(HTTPServer):
    def __init__(self, *args, **kwargs):
        super(SimpleHTTPServer, self).__init__(*args, **kwargs)

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
            except Exception:
                self.handle_error(request, client_address)
                self.shutdown_request(request)
            except:
                self.shutdown_request(request)
                raise
        else:
            self.shutdown_request(request)


def handle_arguments():
    """
        Parsing cmd arguments
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("-a", dest="address", type=str,
                        default="127.0.0.1", help="Bind Address")
    parser.add_argument("-p", dest="port", type=int,
                        default=80, help="Port to listen to")
    parser.add_argument("-o", dest="stdout", help="Path to log stdout",
                        default=None)
    parser.add_argument("-e", dest="stderr", help="Path to log stderr",
                        default=None)
    parser.add_argument("-b", dest="ban", type=str,
                        default="config/banned.txt",
                        help="Path to IP ban list")
    args = parser.parse_args()

    config = {
        "address": args.address,
        "port": args.port,
        "stdout": args.stdout,
        "stderr": args.stderr,
        "ban": args.ban
    }

    return config


def handler_factory(parameters: dict):
    """
        "Class Factory" needed to implement ability
        to pass parameters to HTTP handler.
    """

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
            print(f"Error: Could not redirect stdout: {e}", file=sys.stderr)
            exit(-1)
    if err is not None:
        try:
            ferr = open(err, "a")
            sys.stderr = ferr
        except Exception as e:
            print(f"Error: Could not redirect stderr: {e}", file=sys.stderr)
            exit(-1)


def main():
    args = handle_arguments()
    bind_addr = args["address"], args["port"]
    configure_output(args["stdout"], args["stderr"])

    new_handler = handler_factory(args)
    httpd = SimpleHTTPServer(bind_addr, new_handler)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
