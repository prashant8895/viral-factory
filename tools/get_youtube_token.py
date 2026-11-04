"""One-time: get the YouTube refresh token. Run on your own laptop.

    pip install requests
    python tools/get_youtube_token.py CLIENT_ID CLIENT_SECRET

A browser opens, you sign in with the channel's Google account and click Allow.
The script prints the refresh token. Paste it into GitHub as YT_REFRESH_TOKEN.
"""
import http.server
import sys
import threading
import urllib.parse
import webbrowser

import requests

SCOPES = "https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.readonly"
PORT = 8765
REDIRECT = f"http://localhost:{PORT}"


def main(client_id: str, secret: str) -> None:
    got = {}

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            got["code"] = q.get("code", [None])[0]
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Done. You can close this tab and go back to the terminal.")

        def log_message(self, *a):
            pass

    srv = http.server.HTTPServer(("localhost", PORT), H)
    threading.Thread(target=srv.handle_request, daemon=True).start()
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
        "client_id": client_id, "redirect_uri": REDIRECT, "response_type": "code",
        "scope": SCOPES, "access_type": "offline", "prompt": "consent"})
    print("Opening:", url)
    webbrowser.open(url)
    while "code" not in got:
        pass
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "code": got["code"], "client_id": client_id, "client_secret": secret,
        "redirect_uri": REDIRECT, "grant_type": "authorization_code"}, timeout=30)
    r.raise_for_status()
    print("\nYT_REFRESH_TOKEN =", r.json()["refresh_token"])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
