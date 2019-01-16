import socket
from ..settings import MONGO_HOST


def get_host_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect((MONGO_HOST, 80))
    ip = s.getsockname()[0]
    s.close()
    return ip
