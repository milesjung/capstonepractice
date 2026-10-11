import copy
import json
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from http.server import ThreadingHTTPServer
import server


class BoardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.http = ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
        cls.url = f'http://127.0.0.1:{cls.http.server_port}'
        cls.thread = threading.Thread(target=cls.http.serve_forever, daemon=True)
        cls.thread.start()
        cls.seed = copy.deepcopy(server.ideas)

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.http.server_close()
        cls.thread.join()

    def setUp(self):
        server.ideas[:] = copy.deepcopy(self.seed)
        server.votes.clear()

    def call(self, path='/api/board', data=None, raw=None):
        body = raw if raw is not None else json.dumps(data).encode() if data is not None else None
        req = Request(self.url + path, data=body, headers={'Content-Type': 'application/json'})
        try:
            response = urlopen(req)
        except HTTPError as error:
            response = error
        with response:
            return response.status, json.loads(response.read())

    def test_multiple_friends_submit_and_share_board(self):
        for name, title in [('Sam', 'Go hiking'), ('Taylor', 'Watch a movie')]:
            self.assertEqual(self.call('/api/ideas', {'friend': name, 'title': title})[0], 201)
        first = self.call()[1]
        second = self.call()[1]
        self.assertEqual(first, second)
        self.assertEqual(len(first['ideas']), 5)
        self.assertEqual(first['ideas'][-1]['author'], 'Taylor')

    def test_votes_winner_repeat_and_move(self):
        for name in ['Alex', 'Jamie', 'Sam']:
            self.assertEqual(self.call('/api/vote', {'friend': name, 'idea_id': 2})[0], 200)
        self.call('/api/vote', {'friend': 'Alex', 'idea_id': 2})
        self.assertEqual(self.call()[1]['ideas'][1]['votes'], 3)
        self.call('/api/vote', {'friend': 'Alex', 'idea_id': 1})
        ideas = self.call()[1]['ideas']
        self.assertEqual([i['votes'] for i in ideas], [1, 2, 0])
        self.assertEqual(max(ideas, key=lambda i: i['votes'])['id'], 2)

    def test_tie_and_no_votes(self):
        self.assertTrue(all(i['votes'] == 0 for i in self.call()[1]['ideas']))
        self.call('/api/vote', {'friend': 'Alex', 'idea_id': 1})
        self.call('/api/vote', {'friend': 'Jamie', 'idea_id': 2})
        self.assertEqual([i['votes'] for i in self.call()[1]['ideas']], [1, 1, 0])

    def test_invalid_ideas_and_friend(self):
        for title in ['', '   ', 'x' * 101, None, 42]:
            self.assertEqual(self.call('/api/ideas', {'friend': 'Alex', 'title': title})[0], 400)
        self.assertEqual(self.call('/api/ideas', {'friend': 'Stranger', 'title': 'Hi'})[0], 400)
        self.assertEqual(len(self.call()[1]['ideas']), 3)

    def test_invalid_votes_and_payloads(self):
        for value in [999, True, '1', None]:
            self.assertEqual(self.call('/api/vote', {'friend': 'Alex', 'idea_id': value})[0], 404)
        for raw in [b'{', b'[]', b'x' * 4097]:
            self.assertEqual(self.call('/api/ideas', raw=raw)[0], 400)
        self.assertEqual(self.call('/api/missing')[0], 404)
        self.assertEqual(self.call()[1]['choices'], {})

    def test_title_boundaries_and_literal_markup(self):
        for title in ['x', 'x' * 100, '<script>alert(1)</script>']:
            status, idea = self.call('/api/ideas', {'friend': 'Sam', 'title': title})
            self.assertEqual(status, 201)
            self.assertEqual(idea['title'], title)

    def test_empty_board(self):
        server.ideas.clear()
        self.assertEqual(self.call()[1]['ideas'], [])
        self.assertEqual(self.call('/api/ideas', {'friend': 'Alex', 'title': 'First'})[1]['id'], 1)

    def test_page_and_assets(self):
        for path, expected in [('/', b'The idea board'), ('/app.js', b'textContent'), ('/style.css', b'@media')]:
            with urlopen(self.url + path) as response:
                self.assertEqual(response.status, 200)
                self.assertIn(expected, response.read())


if __name__ == '__main__':
    unittest.main()
