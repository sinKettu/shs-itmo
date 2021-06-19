# Simple HTTP Server (SHS)

Based on Python's HTTP Lib.

## Build

No build required

## Run

To get help about parameters:
```python3 server.py -h```

To run with default configs:
```python3 server.py```

To specify address and port to bind:
```python3 server.py -a "address" -p "port"```

## Docker

To build container:
```sudo docker build -t your/target .```

Or get existing:
```sudo docker pull sinfox/shs:itmo```
