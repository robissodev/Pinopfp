# servidor de dev sem cache e sem log (log bloqueava o processo)
import http.server

class NoCache(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

    def log_message(self, *args):
        pass

http.server.ThreadingHTTPServer(('', 8420), NoCache).serve_forever()
