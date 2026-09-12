"""Ruft ein Tool des onshape-mcp-Servers ueber stdio auf.

Damit laesst sich der MCP-Server benutzen, ohne die Claude-Session neu zu
starten (er ist nur im Projekt-Scope C:/git/FH/PDE registriert).

    python oscall.py <tool> [json-argumente]
    python oscall.py --list
"""
import json
import os
import subprocess
import sys
import time

CMD = ["npx", "--yes", "onshape-mcp"]
KEYS = os.environ.get("ONSHAPE_KEYS",
                      os.path.expanduser("~/.secrets/onshape_keys.json"))


def umgebung():
    """API-Keys aus der Datei als Umgebungsvariablen bereitstellen.

    Ueber Umgebungsvariablen statt --access-key/--secret-key, damit die
    Geheimnisse nicht in der Prozessliste auftauchen.
    """
    env = dict(os.environ)
    if os.path.exists(KEYS):
        k = json.load(open(KEYS))
        env["ONSHAPE_MCP_AUTH__METHOD"] = "basic"
        env["ONSHAPE_MCP_AUTH__ACCESS_KEY"] = k["access"]
        env["ONSHAPE_MCP_AUTH__SECRET_KEY"] = k["secret"]
        # Schreibweisen ohne Praefix-Verschachtelung als Rueckfallebene
        env["ONSHAPE_ACCESS_KEY"] = k["access"]
        env["ONSHAPE_SECRET_KEY"] = k["secret"]
    return env


def rpc(nachrichten, timeout=180):
    eingabe = "\n".join(json.dumps(n) for n in nachrichten) + "\n"
    p = subprocess.run(CMD, input=eingabe, capture_output=True, text=True,
                       timeout=timeout, shell=True, env=umgebung())
    aus = []
    for zeile in p.stdout.splitlines():
        zeile = zeile.strip()
        if not zeile.startswith("{"):
            continue
        try:
            aus.append(json.loads(zeile))
        except json.JSONDecodeError:
            pass
    if not aus and p.stderr:
        print("STDERR:", p.stderr[:800], file=sys.stderr)
    return aus


def init():
    return {"jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                       "clientInfo": {"name": "oscall", "version": "1"}}}


def bereit():
    return {"jsonrpc": "2.0", "method": "notifications/initialized"}


def call(tool, args, tid=2):
    return {"jsonrpc": "2.0", "id": tid, "method": "tools/call",
            "params": {"name": tool, "arguments": args}}


def zeige(antworten, tid=2):
    for a in antworten:
        if a.get("id") != tid:
            continue
        if "error" in a:
            print("FEHLER:", json.dumps(a["error"], ensure_ascii=False)[:1500])
            return
        r = a.get("result", {})
        for c in r.get("content", []):
            if c.get("type") == "text":
                print(c["text"])
        if r.get("isError"):
            print("(Server meldet isError)")
        if not r.get("content"):
            print(json.dumps(r, ensure_ascii=False)[:2000])
        return
    print("keine Antwort auf id", tid)


def main():
    if len(sys.argv) < 2 or sys.argv[1] == "--list":
        a = rpc([init(), bereit(),
                 {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}])
        for x in a:
            if x.get("id") == 2:
                for t in x["result"]["tools"]:
                    print("%-26s %s" % (t["name"], t["description"].split("\n")[0][:100]))
        return
    tool = sys.argv[1]
    args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    zeige(rpc([init(), bereit(), call(tool, args)]))


if __name__ == "__main__":
    main()
