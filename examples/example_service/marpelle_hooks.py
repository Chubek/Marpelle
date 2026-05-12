def ping(payload):
    return {"pong": True, "echo": payload}


def status(_payload):
    return {"status": "running"}


HOOKS = {
    "ping": ping,
    "status": status,
}
