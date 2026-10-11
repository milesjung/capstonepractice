# Let's pick — idea voting board

For friends deciding on a fun activity or another lightweight option. The hypothesis is that groups want to make plans but struggle to agree on one thing. The learning question: does a centralized idea board make deciding easier?

Flow: choose a mock friend, submit an idea, see all ideas together, and vote. Each friend has one vote; voting again moves it. The highest-voted idea is the current winner. Ties are explicit; a board with no votes has no winner. This is a prototype, not an authenticated voting system.

## Run

Python 3.12 or later, with no external dependencies:

```sh
cd /workspace/capstonepractice
python server.py
```

The server uses port 8000 (`PORT` overrides it). Open the server in your browser. Separate sessions share the same board; select different mock friends to simulate multiple users. Updates appear within two seconds. Data is in memory and resets to sample ideas and votes on restart. Do not use for sensitive or production data.

## Validate

```sh
python -m unittest -v
node --check static/app.js
```

Acceptance criteria: multiple friends can submit ideas; everyone sees the same board; friends can vote and the highest-voted idea wins. API tests also cover invalid submissions, unknown friends/ideas, vote changes, repeated votes, ties, and malformed requests. Browser checks should cover keyboard interaction, narrow screens, and loss of server connectivity.

Plain HTML/CSS/JavaScript keeps this small. Python's standard-library HTTP server supplies shared state so different sessions can actually collaborate without adding a framework or database. No accounts, rooms, or extra features are required to test the hypothesis. Behavioral validation does not answer the learning question; that needs a trial with real groups.
