"""Onshape-REST-API mit zwei Transportwegen - kostenlos oder ueber den API-Key.

HINTERGRUND

Onshape begrenzt den programmatischen Zugriff auf ein JAHRESKONTINGENT
(EDU Student: 2.500 Aufrufe). Ist es aufgebraucht, antwortet die API mit
HTTP 402, bis das Abrechnungsjahr endet.

Entscheidend: das Kontingent gilt nur fuer Aufrufe mit API-Key oder OAuth aus
privaten Anwendungen. Die normale Browser-Session zaehlt NICHT mit.
    https://onshape-public.github.io/docs/auth/limits/

Daraus folgen zwei Wege:

    "session"  Cookies einer angemeldeten Browser-Session  -> kostenlos
    "key"      API-Key (derselbe Weg wie der MCP-Server)    -> zaehlt

Fuer iterative Arbeit (FeatureScript schreiben, pruefen, korrigieren) ist
"session" der richtige Weg. "key" ist der Rueckfall, wenn keine Browser-Session
vorliegt - etwa in einem Cronjob.

ENDPUNKTKATALOG

Beide Wege sprechen Endpunkte ueber ihre operationId an (z.B.
"getFeatureStudioContents"). Die Zuordnung operationId -> Pfad stammt aus
endpoints.json; die Datei wird aus dem MCP-Server erzeugt:

    python oscall.py onshape_api_search '{"query":""}' > endpoints.json

Dieser MCP-Aufruf ist gratis - api_search arbeitet rein lokal auf einer
eingebetteten OpenAPI-Spezifikation und geht nie ans Netz.

SITZUNG ERNEUERN

onshape_session.json enthaelt die Cookies und laeuft mit der Browser-Session
ab. Bei HTTP 401 im Session-Modus: im Playwright-Browser neu anmelden und die
Cookies erneut ablegen (siehe savesrv.py).

AUFRUF

    from api import Onshape
    os_api = Onshape()                       # Session-Modus
    d = os_api("getDocuments", query={"filter": "0", "limit": "10"})

    python api.py getDocuments '{"query":{"limit":"5"}}'
"""
import json
import os
import sys

import requests

HIER = os.path.dirname(os.path.abspath(__file__))
BASIS = "https://cad.onshape.com/api/v6"
KATALOG = os.path.join(HIER, "endpoints.json")

SESSION_DATEI = os.environ.get(
    "ONSHAPE_SESSION", os.path.expanduser("~/.secrets/onshape_session.json"))
KEY_DATEI = os.environ.get(
    "ONSHAPE_KEYS", os.path.expanduser("~/.secrets/onshape_keys.json"))


class ApiFehler(RuntimeError):
    pass


class Onshape:
    def __init__(self, modus="session"):
        if modus not in ("session", "key"):
            raise ValueError("modus muss 'session' oder 'key' sein")
        self.modus = modus
        self.katalog = self._katalog()
        self.s = requests.Session()
        self.s.headers["Accept"] = "application/json"
        # Vor Onshape haengt eine Web Application Firewall. Sie beantwortet
        # Anfragen mit der Kennung "python-requests/..." mit einer HTML-Seite
        # "403 Forbidden" - das kommt von der WAF, nicht von der API. Mit einer
        # Browser-Kennung und passendem Origin laesst sie die Anfrage durch.
        self.s.headers["User-Agent"] = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36")
        self.s.headers["Origin"] = "https://cad.onshape.com"
        self.s.headers["Referer"] = "https://cad.onshape.com/documents"

        if modus == "session":
            if not os.path.exists(SESSION_DATEI):
                raise ApiFehler(
                    "Keine Session gefunden (%s).\n"
                    "Im Playwright-Browser bei Onshape anmelden und die Cookies "
                    "ablegen." % SESSION_DATEI)
            d = json.load(open(SESSION_DATEI, encoding="utf-8"))
            for k, v in d["cookies"].items():
                self.s.cookies.set(k, v, domain=".onshape.com")
            if d.get("xsrf"):
                # Schreibende Aufrufe verlangt Onshape mit XSRF-Header
                self.s.headers["X-XSRF-TOKEN"] = d["xsrf"]
        else:
            if not os.path.exists(KEY_DATEI):
                raise ApiFehler("Keine API-Keys gefunden (%s)." % KEY_DATEI)
            k = json.load(open(KEY_DATEI, encoding="utf-8"))
            self.s.auth = (k["access"], k["secret"])

    @staticmethod
    def _katalog():
        if not os.path.exists(KATALOG):
            raise ApiFehler(
                "Endpunktkatalog fehlt (%s).\n"
                "Erzeugen mit:  python oscall.py onshape_api_search '{\"query\":\"\"}' "
                "> endpoints.json" % KATALOG)
        roh = json.load(open(KATALOG, encoding="utf-8"))
        return {e["operation_id"]: e for e in roh}

    def __call__(self, endpoint, path=None, query=None, body=None, roh=False):
        """Ruft einen Endpunkt ueber seine operationId auf."""
        e = self.katalog.get(endpoint)
        if e is None:
            treffer = [k for k in self.katalog if endpoint.lower() in k.lower()]
            raise ApiFehler("Unbekannter Endpunkt %r.%s"
                            % (endpoint,
                               ("  Gemeint: " + ", ".join(treffer[:5])) if treffer else ""))

        pfad = e["path"]
        for k, v in (path or {}).items():
            marke = "{%s}" % k
            if marke not in pfad:
                raise ApiFehler("Pfadparameter %r kommt in %s nicht vor" % (k, pfad))
            pfad = pfad.replace(marke, str(v))
        if "{" in pfad:
            fehlt = pfad[pfad.index("{"):].split("}")[0].strip("{")
            raise ApiFehler("Pfadparameter fehlt: %s  (%s)" % (fehlt, e["path"]))

        kw = {"params": query or {}}
        if body is not None:
            kw["json"] = body
        r = self.s.request(e["method"], BASIS + pfad, **kw)

        if r.status_code == 402:
            raise ApiFehler(
                "HTTP 402 - das jaehrliche API-Kontingent ist aufgebraucht.\n"
                "Betrifft nur den Key-Modus; im Session-Modus zaehlen Aufrufe nicht.")
        if r.status_code == 401 and self.modus == "session":
            raise ApiFehler(
                "HTTP 401 - die Browser-Session ist abgelaufen.\n"
                "Im Playwright-Browser neu anmelden und die Cookies neu ablegen.")
        if r.status_code >= 300:
            raise ApiFehler("HTTP %d bei %s %s\n%s"
                            % (r.status_code, e["method"], pfad, r.text[:600]))
        if roh:
            return r.content
        if not r.content:
            return None
        try:
            return r.json()
        except ValueError:
            return r.text


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    modus = "session"
    argv = sys.argv[1:]
    if argv[0] in ("--key", "--session"):
        modus = argv.pop(0).lstrip("-")
    endpoint = argv[0]
    opt = json.loads(argv[1]) if len(argv) > 1 else {}
    api = Onshape(modus)
    d = api(endpoint, path=opt.get("path"), query=opt.get("query"), body=opt.get("body"))
    print(json.dumps(d, indent=2, ensure_ascii=False)[:4000])


if __name__ == "__main__":
    main()
