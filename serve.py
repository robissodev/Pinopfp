# servidor de dev sem cache: nada fica preso no telefone
import http.server

class NoCache(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

http.server.ThreadingHTTPServer(('', 8420), NoCache).serve_forever()
