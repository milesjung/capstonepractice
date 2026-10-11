"""A shared, in-memory mock board. Run with python server.py."""
import json
import os
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

FRIENDS = ['Alex', 'Jamie', 'Sam', 'Taylor']
ideas = [
    {'id': 1, 'title': 'Picnic in the park', 'author': 'Alex'},
    {'id': 2, 'title': 'Board game night', 'author': 'Jamie'},
    {'id': 3, 'title': 'Try the new taco spot', 'author': 'Sam'},
]
votes = {'Alex': 1, 'Jamie': 2}
lock = threading.Lock()


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(Path(__file__).parent / 'static'), **kwargs)

    def respond(self, status, data):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == '/api/board':
            with lock:
                self.respond(200, {'friends': FRIENDS, 'ideas': [dict(i, votes=sum(v == i['id'] for v in votes.values())) for i in ideas], 'choices': dict(votes)})
        elif self.path.startswith('/api/'):
            self.respond(404, {'error': 'Unknown endpoint.'})
        else:
            super().do_GET()

    def do_POST(self):
        if self.path not in ('/api/ideas', '/api/vote'):
            return self.respond(404, {'error': 'Unknown endpoint.'})
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 4096:
                return self.respond(400, {'error': 'Request must be between 1 and 4096 bytes.'})
            data = json.loads(self.rfile.read(size))
            if not isinstance(data, dict):
                raise ValueError()
        except (ValueError, UnicodeDecodeError):
            return self.respond(400, {'error': 'Send a valid JSON object.'})
        friend = data.get('friend')
        if not isinstance(friend, str) or friend not in FRIENDS:
            return self.respond(400, {'error': 'Choose a mock friend.'})
        with lock:
            if self.path == '/api/ideas':
                title = data.get('title')
                if not isinstance(title, str) or not 1 <= len(title.strip()) <= 100:
                    return self.respond(400, {'error': 'Write an idea between 1 and 100 characters.'})
                idea = {'id': max((i['id'] for i in ideas), default=0) + 1, 'title': title.strip(), 'author': friend}
                ideas.append(idea)
                self.respond(201, idea)
            else:
                target = data.get('idea_id')
                if type(target) is not int or not any(i['id'] == target for i in ideas):
                    return self.respond(404, {'error': 'That idea is no longer available. Refresh the board.'})
                votes[friend] = target
                self.respond(200, {'ok': True})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', '8000'))
    print(f'Idea board listening on port {port}', flush=True)
    ThreadingHTTPServer(('0.0.0.0', port), Handler).serve_forever()
