import socket
try:
    print(f"Resolving api.binance.com: {socket.gethostbyname('api.binance.com')}")
    print(f"Resolving stream.binance.com: {socket.gethostbyname('stream.binance.com')}")
except Exception as e:
    print(f"Error: {e}")
