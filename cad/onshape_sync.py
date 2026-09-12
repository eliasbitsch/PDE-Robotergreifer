"""STEP-Dateien nach Onshape hochladen und uebersetzen lassen.

Nutzt die Session-Cookies eines im Browser angemeldeten Onshape-Kontos statt
API-Keys. Die Onshape-REST-API akzeptiert die normale Web-Session, solange der
XSRF-Token als Header mitgeschickt wird - damit entfaellt der Umweg ueber das
Developer-Portal.

Cookies und Token werden vom Playwright-Browser in den Scratchpad geschrieben:
    onshape_cookies.txt   Netscape-Cookiejar
    onshape_xsrf.txt      XSRF-Token

Aufruf:
    python onshape_sync.py            # Baugruppe + Zange hochladen
    python onshape_sync.py --status   # nur Uebersetzungsstatus abfragen
"""
import json
import os
import subprocess
import sys
import time

HIER = os.path.dirname(os.path.abspath(__file__))
STEP_DIR = os.path.join(HIER, "..", "out", "step")

SCRATCH = os.environ.get(
    "PDE_SCRATCH",
    r"C:\Users\BitschE\AppData\Local\Temp\claude"
    r"\C--Users-BitschE\0ccad5ab-04a6-44f6-895c-d44b194084b7\scratchpad")
COOKIES = os.path.join(SCRATCH, "onshape_cookies.txt")
XSRF = os.path.join(SCRATCH, "onshape_xsrf.txt")

API = "https://cad.onshape.com/api/v6"
DID = "b1983011606222863da301b2"
WID = "8b0ebce61c2046c71f645192"

# Was hochgeladen wird. Die Einzelteile bleiben bewusst aussen vor - in Onshape
# wird die Baugruppe gebraucht, die Einzelteile stecken darin.
DATEIEN = [
    "Greifer_Baugruppe.step",
    "Greiferzange_FEM.step",
]


def _tok():
    if not os.path.exists(COOKIES):
        raise SystemExit(
            "Cookies fehlen (%s).\n"
            "Im Playwright-Browser bei Onshape anmelden und die Cookies\n"
            "in den Scratchpad schreiben lassen." % COOKIES)
    return open(XSRF).read().strip()


def _curl(args, timeout=600):
    r = subprocess.run(["curl", "-s", "-b", COOKIES,
                        "-H", "X-XSRF-TOKEN: " + _tok(),
                        "-H", "Accept: application/json"] + args,
                       capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError("curl fehlgeschlagen: %s" % r.stderr[:300])
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        raise RuntimeError("keine JSON-Antwort: %s" % r.stdout[:300])


def hochladen(name):
    pfad = os.path.join(STEP_DIR, name)
    if not os.path.exists(pfad):
        raise SystemExit("fehlt: %s" % pfad)
    mb = os.path.getsize(pfad) / 1e6
    print("  %-28s %6.2f MB  ... " % (name, mb), end="", flush=True)
    d = _curl(["-F", "file=@%s;type=application/step" % pfad,
               "-F", "encodedFilename=" + name,
               "-F", "translate=true",
               "-F", "flattenAssemblies=false",
               "-F", "yAxisIsUp=false",
               "%s/blobelements/d/%s/w/%s" % (API, DID, WID)])
    print("ok  (Element %s)" % d.get("id", "?"))
    return d


def elemente():
    return _curl(["%s/documents/d/%s/w/%s/elements" % (API, DID, WID)])


def status():
    el = elemente()
    print("\nELEMENTE IM DOKUMENT")
    print("  %-38s %-14s %s" % ("Name", "Typ", "Element-ID"))
    print("  " + "-" * 72)
    for e in el:
        print("  %-38s %-14s %s"
              % (e.get("name", "")[:38], e.get("elementType", ""), e.get("id", "")))
    return el


def main():
    if "--status" in sys.argv:
        status()
        return

    print("UPLOAD NACH ONSHAPE")
    print("  Dokument %s" % DID)
    for n in DATEIEN:
        hochladen(n)

    print("\nWarte auf die Uebersetzung ...")
    for _ in range(30):
        time.sleep(4)
        el = elemente()
        if any(e.get("elementType") == "PARTSTUDIO"
               and e.get("name", "").startswith("Greifer") for e in el):
            break
    status()
    print("\n  https://cad.onshape.com/documents/%s/w/%s" % (DID, WID))


if __name__ == "__main__":
    main()
