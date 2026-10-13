"""A small, polite GitHub REST client on the standard library.

Transports, chosen automatically:
  token  urllib with GITHUB_TOKEN or GH_TOKEN from the environment
  gh     the authenticated GitHub CLI, when it is installed (this tool never sees the token)
  anon   unauthenticated urllib (60 requests an hour, so only good for a few repos)

Every call waits `delay` seconds after the previous one, and a 403 or 429 waits `backoff`
seconds and retries. Reads only: there is no code here that writes to GitHub.
"""
import base64
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.github.com"
UA = "readme-breakouts (research; reads public READMEs)"


class ApiError(Exception):
    def __init__(self, status, message=""):
        super().__init__(f"HTTP {status}: {message}".strip())
        self.status = status


def _query(path, params):
    if not params:
        return path
    return path + ("&" if "?" in path else "?") + urllib.parse.urlencode(params)


class Client:
    def __init__(self, delay=3.0, backoff=65.0, transport="auto", retries=3, log=None):
        self.delay = delay
        self.backoff = backoff
        self.retries = retries
        self.log = log or (lambda msg: print(msg, file=sys.stderr))
        self.calls = 0
        self._last = 0.0
        self._token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        self._gh = shutil.which("gh")
        if transport == "auto":
            transport = "token" if self._token else ("gh" if self._gh else "anon")
        if transport == "gh" and not self._gh:
            raise RuntimeError("transport gh needs the GitHub CLI on PATH")
        if transport == "token" and not self._token:
            raise RuntimeError("transport token needs GITHUB_TOKEN or GH_TOKEN")
        self.transport = transport

    def _wait(self):
        gap = self.delay - (time.monotonic() - self._last)
        if gap > 0:
            time.sleep(gap)

    def _urllib(self, path, params, accept):
        req = urllib.request.Request(API + _query(path, params))
        req.add_header("Accept", accept)
        req.add_header("User-Agent", UA)
        req.add_header("X-GitHub-Api-Version", "2022-11-28")
        if self.transport == "token":
            req.add_header("Authorization", "Bearer " + self._token)
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()

    def _via_gh(self, path, params, accept):
        cmd = [self._gh, "api", "--include", "-X", "GET", "-H", "Accept: " + accept, path]
        for k, v in (params or {}).items():
            cmd += ["-f", f"{k}={v}"]
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        head, _, body = p.stdout.replace("\r\n", "\n").partition("\n\n")
        first = head.split("\n", 1)[0] if head else ""
        parts = first.split()
        if len(parts) >= 2 and parts[0].startswith("HTTP") and parts[1].isdigit():
            status = int(parts[1])
        else:
            status = 0
            for tok in p.stderr.split():
                if tok.isdigit() and len(tok) == 3:
                    status = int(tok)
                    break
        if not body and p.stderr and status >= 400:
            body = json.dumps({"message": p.stderr.strip()})
        return (status or (200 if p.returncode == 0 else 500)), body.encode("utf-8")

    def get_json(self, path, params=None, accept="application/vnd.github+json"):
        for attempt in range(self.retries + 1):
            self._wait()
            if self.transport == "gh":
                status, body = self._via_gh(path, params, accept)
            else:
                status, body = self._urllib(path, params, accept)
            self._last = time.monotonic()
            self.calls += 1
            if status in (403, 429) and attempt < self.retries:
                self.log(f"  HTTP {status}: waiting {self.backoff:.0f}s before retry {attempt + 1}")
                time.sleep(self.backoff)
                continue
            try:
                data = json.loads(body.decode("utf-8") or "null")
            except ValueError:
                data = None
            if status >= 400:
                msg = data.get("message", "") if isinstance(data, dict) else ""
                raise ApiError(status, msg)
            return data
        raise ApiError(0, "retries exhausted")


def decode_readme(payload):
    """Decode the JSON returned by GET /repos/{owner}/{repo}/readme."""
    raw = base64.b64decode(payload.get("content", "")) if payload.get("encoding") == "base64" else b""
    return raw.decode("utf-8", errors="replace"), payload.get("name", ""), payload.get("sha", "")
