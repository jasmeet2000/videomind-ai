"""
Network utilities for basic connectivity checks used by readiness probes.
"""
from __future__ import annotations

import socket
from contextlib import closing


def tcp_check(host: str, port: int, timeout: float = 1.0) -> bool:
    """Perform a simple TCP connect to host:port with a timeout.

    Returns True if the TCP port accepts a connection within the
    timeout; False otherwise. This is intentionally lightweight so
    health checks don't require DB drivers or external clients.
    """
    try:
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            sock.settimeout(timeout)
            sock.connect((host, int(port)))
        return True
    except Exception:
        return False
