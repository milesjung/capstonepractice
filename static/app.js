const friend = document.querySelector('#friend');
const form = document.querySelector('#idea-form');
const title = document.querySelector('#title');
const status = document.querySelector('#status');
const retry = document.querySelector('#retry');
let board, busy = false;

async function request(path, data) {
  const response = await fetch(path, data ? {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data)} : {cache: 'no-store'});
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || 'The board could not be updated.');
  return payload;
}
function render() {
  const focusedIdea = document.activeElement?.dataset.ideaId;
  document.querySelector('#count').textContent = `${board.ideas.length} ideas · ${Object.keys(board.choices).length} votes`;
  const max = Math.max(0, ...board.ideas.map(i => i.votes));
  const leaders = board.ideas.filter(i => i.votes === max);
  const result = document.querySelector('#result');
  result.replaceChildren();
  result.append(max === 0 ? 'The next plan is up to you.' : leaders.length === 1 ? '✳ Current winner' : '✳ It’s a tie — no single winner yet');
  const heading = document.createElement('strong');
  heading.textContent = max === 0 ? 'Cast the first vote.' : leaders.map(i => i.title).join(' · ');
  result.append(heading);
  const cards = document.querySelector('#ideas');
  cards.replaceChildren();
  if (!board.ideas.length) cards.textContent = 'The board is empty. Add the first idea!';
  for (const idea of board.ideas) {
    const card = document.createElement('article'); card.className = 'card';
    const copy = document.createElement('div');
    const name = document.createElement('h3'); name.textContent = idea.title;
    const author = document.createElement('p'); author.textContent = `Suggested by ${idea.author}`;
    copy.append(name, author);
    const button = document.createElement('button');
    button.dataset.ideaId = String(idea.id);
    const selected = board.choices[friend.value] === idea.id;
    button.className = `vote${selected ? ' selected' : ''}`;
    button.setAttribute('aria-pressed', String(selected));
    button.setAttribute('aria-label', `${selected ? 'Voted for' : 'Vote for'} ${idea.title}, ${idea.votes} votes`);
    button.disabled = busy;
    const count = document.createElement('span'); count.className = 'votes'; count.textContent = idea.votes;
    button.append(count, selected ? 'Your vote ✓' : 'Vote ↑');
    button.addEventListener('click', () => mutate('/api/vote', {friend: friend.value, idea_id: idea.id}));
    card.append(copy, button); cards.append(card);
  }
  if (focusedIdea) cards.querySelector(`[data-idea-id="${focusedIdea}"]`)?.focus();
}
async function refresh() {
  try {
    const next = await request('/api/board');
    if (!board) {
      friend.replaceChildren(...next.friends.map(name => {const option = document.createElement('option'); option.value = name; option.textContent = name; return option;}));
      friend.value = sessionStorage.getItem('friend') || next.friends[0];
      if (!friend.value) friend.value = next.friends[0];
    }
    const changed = JSON.stringify(board) !== JSON.stringify(next);
    board = next;
    if (changed) render();
    if (!retry.hidden) status.textContent = 'Connected to the board.';
    retry.hidden = true;
    return true;
  } catch (error) {
    status.textContent = 'Cannot reach the board. Check the server and retry. Your idea stays in the form.';
    retry.hidden = false; return false;
  }
}
async function mutate(path, data) {
  if (busy) return;
  const focusedIdea = document.activeElement?.dataset.ideaId;
  busy = true; form.querySelector('button').disabled = true; if (board) render();
  try {
    await request(path, data);
    if (path === '/api/ideas') title.value = '';
    status.textContent = path === '/api/ideas' ? 'Idea added to the shared board.' : 'Your vote has been saved.';
    await refresh();
  } catch (error) {status.textContent = error.message;}
  finally {
    busy = false; form.querySelector('button').disabled = false;
    if (board) render();
    if (focusedIdea) document.querySelector(`[data-idea-id="${focusedIdea}"]`)?.focus();
  }
}
form.addEventListener('submit', event => {
  event.preventDefault();
  if (!title.value.trim()) {status.textContent = 'Write an idea before adding it.'; title.focus(); return;}
  mutate('/api/ideas', {friend: friend.value, title: title.value.trim()});
});
friend.addEventListener('change', () => {sessionStorage.setItem('friend', friend.value); if (board) render();});
retry.addEventListener('click', async () => {if (await refresh()) status.textContent = 'Connected to the board.';});
refresh();
setInterval(() => {if (!busy) refresh();}, 2000);
