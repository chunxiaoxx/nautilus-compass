"""echo_demo handler · trivial echo for 5-step cycle wiring demo."""


def execute(message: str = "ping") -> dict:
    return {"echo": message, "skill": "echo_demo"}


if __name__ == "__main__":
    import json, sys
    msg = sys.argv[1] if len(sys.argv) > 1 else "ping"
    print(json.dumps(execute(message=msg)))
