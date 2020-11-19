#!/bin/python3

import argparse
from http.server import HTTPServer

import HTTPRequestHandler as rh

# TODO:
#   - Parsing config/config
#   - Ban IP list
#   - Alerts
#   - Separate stderr and stdout


def handle_arguments():
    """
        Parsing cmd arguments
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("-a", dest="address", type=str,
                        default="127.0.0.1", help="Bind Address")
    parser.add_argument("-p", dest="port", type=int,
                        default=80, help="Port to listen to")
    parser.add_argument("-l", dest="log", help="Path to log file",
                        default=None)
    parser.add_argument("-b", dest="ban", type=str,
                        default="config/banned.txt",
                        help="Path to IP ban list")
    args = parser.parse_args()

    config = {
        "address": args.address,
        "port": args.port,
        "log_file": args.log,
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


def main():
    args = handle_arguments()
    bind_addr = args["address"], args["port"]

    rh.prepare_handlers()
    new_handler = handler_factory(args)
    httpd = HTTPServer(bind_addr, new_handler)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
