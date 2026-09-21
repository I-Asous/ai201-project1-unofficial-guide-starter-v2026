#!/usr/bin/env python3
"""
The Unofficial Guide — the same pipeline, over HTTP.

    python serve.py                          run it locally on port 5000
    gunicorn serve:app                       run it the way a host runs it

Nothing new happens in this file. It is a wrapper: a request comes in, it
hands the question to `app.py::ask_pipeline` — the exact function the command
line uses — and hands the answer back as JSON. Retrieval, the relevance gate
and the grounded prompt all still live where they lived. If you change how
your system answers, you change it in those files and this one follows.

Two routes:

    POST /ask       {"question": "..."} in, the answer and its sources out
    GET  /health    is the service up, and is there an index to search

Why this exists: `app.py` runs once and exits, which is fine on your laptop
and impossible to deploy. A hosted service has to stay up and wait for
requests. This is the smallest thing that does that.

Unit 9: this file now logs one JSON line per request to stdout — the request
line, the status, and the timing, split into retrieval and generation so a slow
request says which stage was slow. Hosts collect stdout, so that is the log.
On startup it also builds the index if there isn't one, because a host's disk
doesn't survive a restart.
"""

import faulthandler
import json
import logging
import os
import sys
import time
import uuid

from flask import Flask, g, jsonify, request

import config

# A crash inside a compiled dependency (an "illegal instruction" from a library
# built for a different CPU, say) would otherwise exit with a bare status code
# and no Python traceback. This makes it print which line was running.
faulthandler.enable()

app = Flask(__name__)

# ─── Logging ─────────────────────────────────────────────────────────────────
# One JSON object per line, on stdout. Structured so a person or a script can
# filter it ("every request over 3000 ms", "every refused question") rather
# than grep prose. Logging goes through this logger, not print, so gunicorn's
# own output and ours don't interleave mid-line.

log = logging.getLogger("unofficial_guide")
log.setLevel(logging.INFO)
if not log.handlers:
    _handler = logging.StreamHandler(sys.stdout)
    _handler.setFormatter(logging.Formatter("%(message)s"))
    log.addHandler(_handler)
    log.propagate = False


def _emit(event: str, **fields) -> None:
    """Write one structured log line. Never raises: logging must not break a request."""
    try:
        record = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "event": event, **fields}
        log.info(json.dumps(record, default=str))
    except Exception:  # noqa: BLE001
        pass


def _ms(start: float, end: float | None = None) -> float:
    return round(((end if end is not None else time.perf_counter()) - start) * 1000, 1)


def _peak_rss_mb() -> float:
    """Highest memory this process has used so far, in MB (Linux reports KB, macOS bytes)."""
    import resource

    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return round(peak / (1e6 if sys.platform == "darwin" else 1e3), 1)


def ensure_index() -> None:
    """Build the index if this machine doesn't have one yet.

    A deployed service starts on a blank disk every time it restarts, so
    "run python app.py index first" cannot be a manual step. This runs once at
    startup, before the first request; the time it takes is logged, because on
    a cold start it is most of the wait.
    """
    from store import build_index, index_exists

    if index_exists(config.CORPUS):
        _emit("index", action="found", corpus=config.CORPUS, peak_rss_mb=_peak_rss_mb())
        return
    from chunker import split_documents
    from ingest import load_documents

    started = time.perf_counter()
    chunks = split_documents(load_documents(config.CORPUS))
    build_index(chunks, corpus=config.CORPUS)
    _emit("index", action="built", corpus=config.CORPUS, chunks=len(chunks),
          build_ms=_ms(started), peak_rss_mb=_peak_rss_mb())


@app.before_request
def _start_timer():
    g.request_id = uuid.uuid4().hex[:8]
    g.t0 = time.perf_counter()
    g.stages = {}


@app.after_request
def _log_request(response):
    """One line per request: who asked what, what came back, how long it took."""
    fields = {
        "request_id": g.get("request_id"),
        "method": request.method,
        "path": request.path,
        "status": response.status_code,
        "total_ms": _ms(g.t0) if "t0" in g else None,
        "peak_rss_mb": _peak_rss_mb(),
        **g.get("stages", {}),
        **g.get("outcome", {}),
    }
    _emit("request", **fields)
    response.headers["X-Request-Id"] = g.get("request_id", "")
    return response


@app.get("/health")
def health():
    """Is the service up, and is there an index to search?

    Two different questions, and the second one is the one that bites. A
    freshly deployed service answers this route happily while every /ask
    returns "no index" — hosts give you no disk that survives a restart, so
    the index has to be built as part of getting the service up. Checking
    here means you find that out in one request instead of five.
    """
    from store import index_exists

    ready = index_exists(config.CORPUS)
    return jsonify(
        {
            "status": "ok",
            "corpus": config.CORPUS,
            "index_ready": ready,
            "detail": (
                "ready"
                if ready
                else "no index for this corpus — run `python app.py index`"
            ),
        }
    )


@app.post("/ask")
def ask():
    """One question in, one grounded answer out.

    A refused question is a 200, not an error. The gate refusing is your
    system working — it is an answer, and the JSON says so with
    `"refused": true` so whatever calls this can tell the two apart.
    """
    from app import ask_pipeline

    payload = request.get_json(silent=True) or {}
    question = (payload.get("question") or "").strip()

    if not question:
        return (
            jsonify(
                {
                    "error": "Send JSON with a question in it, like "
                    '{"question": "is the housing lottery random?"}'
                }
            ),
            400,
        )

    # ask_pipeline calls on_gate right after retrieval and on_prompt right
    # before the model call, so those two moments split the request into stages
    # without touching app.py. A refused question never reaches on_prompt, which
    # is why it shows retrieval_ms and no generation_ms: it cost no model call.
    marks = {}

    def on_gate(_decision):
        marks["gate"] = time.perf_counter()

    def on_prompt(_prompt):
        marks["prompt"] = time.perf_counter()

    g.outcome = {"question": question[:200]}
    try:
        outcome = ask_pipeline(
            question, corpus=config.CORPUS, on_gate=on_gate, on_prompt=on_prompt
        )
    except Exception as exc:  # noqa: BLE001 — a reader gets this, not a traceback
        if "gate" in marks:
            g.stages["retrieval_ms"] = _ms(g.t0, marks["gate"])
        g.outcome["error"] = f"{type(exc).__name__}: {exc}"[:300]
        return jsonify({"error": f"{type(exc).__name__}: {exc}"}), 500

    end = time.perf_counter()
    g.stages["retrieval_ms"] = _ms(g.t0, marks["gate"]) if "gate" in marks else None
    if "prompt" in marks:
        g.stages["generation_ms"] = _ms(marks["prompt"], end)
    g.outcome.update(
        refused=outcome["refused"],
        best_distance=round(outcome["best_distance"], 4),
        sources=outcome["sources"],
    )

    return jsonify(
        {
            "question": question,
            "answer": outcome["answer"],
            "refused": outcome["refused"],
            "sources": outcome["sources"],
            "best_distance": round(outcome["best_distance"], 4),
            "threshold": outcome["threshold"],
            "corpus": config.CORPUS,
        }
    )


# Under gunicorn `main()` never runs, so the index is built at import instead.
# Set AI201_SKIP_INDEX=1 to skip it (the tests do).
if os.getenv("AI201_SKIP_INDEX") != "1" and __name__ != "__main__":
    ensure_index()


def main():
    # Hosts tell you which port to listen on through PORT, and they expect you
    # on 0.0.0.0. Binding 127.0.0.1 instead works perfectly on your laptop and
    # then answers nothing at all once deployed, because the host's router
    # can't reach a socket that only accepts connections from inside the
    # container. It is the single most common way a first deploy "succeeds"
    # and is unreachable.
    port = int(os.getenv("PORT", "5000"))

    # Debug mode reloads on save, which is handy, and prints a console that
    # runs arbitrary code, which is not something to leave switched on where
    # strangers can reach it. Off unless you ask for it.
    debug = os.getenv("AI201_DEBUG", "0") == "1"

    ensure_index()
    print(f"Serving The Unofficial Guide on http://localhost:{port}")
    print(f"Corpus: {config.CORPUS}    (Ctrl-C to stop)\n")
    print("Try it from another terminal:\n")
    print(f"  curl http://localhost:{port}/health")
    print(
        f"  curl -X POST http://localhost:{port}/ask \\\n"
        f"    -H 'Content-Type: application/json' \\\n"
        f"    -d '{{\"question\": \"is the housing lottery random?\"}}'\n"
    )

    app.run(host="0.0.0.0", port=port, debug=debug)


if __name__ == "__main__":
    main()
