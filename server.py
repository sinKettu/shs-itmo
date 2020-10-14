#!/bin/python3

import argparse
from http.server import HTTPServer

import HTTPRequestHandler as rh

# TODO:
#   - Parsing config/config
#   - Using regexps in urls.yaml and when resolving in handler


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
    return args.address, args.port, args.log, args.ban


def main():
    args = handle_arguments()
    bind_addr = args[0], args[1]
    log_file = args[2]
    ban_file = args[3]

    rh.prepare_handlers()
    httpd = HTTPServer(bind_addr, rh.SimpleHTTPRequestHandler)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
