(() => {
  const root = document.getElementById('travel-chat');
  if (!root) return;
  const toggle = root.querySelector('[data-chat-toggle]');
  const panel = root.querySelector('.chat-panel');
  const close = root.querySelector('[data-chat-close]');
  const form = root.querySelector('form');
  const input = root.querySelector('textarea');
  const send = root.querySelector('[type="submit"]');
  const messages = root.querySelector('.chat-messages');
  const history = [];
  let busy = false;

  const scrollToBottom = () => { messages.scrollTop = messages.scrollHeight; };
  function appendInline(parent, text) {
    const pattern = /(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)/g;
    let cursor = 0;
    for (const match of text.matchAll(pattern)) {
      parent.append(document.createTextNode(text.slice(cursor, match.index)));
      const token = match[0];
      let node;
      if (token.startsWith('**')) { node = document.createElement('strong'); node.textContent = token.slice(2, -2); }
      else if (token.startsWith('`')) { node = document.createElement('code'); node.textContent = token.slice(1, -1); }
      else { node = document.createElement('em'); node.textContent = token.slice(1, -1); }
      parent.append(node);
      cursor = match.index + token.length;
    }
    parent.append(document.createTextNode(text.slice(cursor)));
  }

  function renderFormatted(body, text) {
    let paragraph = null;
    let list = null;
    let listType = '';
    const flushParagraph = () => { paragraph = null; };
    const flushList = () => { list = null; listType = ''; };
    for (const rawLine of String(text || '').split(/\r?\n/)) {
      const line = rawLine.trim();
      if (!line) { flushParagraph(); flushList(); continue; }
      if (/^[-*_]{3,}$/.test(line)) { flushParagraph(); flushList(); body.append(document.createElement('hr')); continue; }
      const heading = line.match(/^#{1,3}\s+(.+)$/);
      if (heading) {
        flushParagraph(); flushList();
        const title = document.createElement('h4');
        appendInline(title, heading[1]);
        body.append(title);
        continue;
      }
      const ordered = line.match(/^\d+[.)]\s+(.+)$/);
      const bullet = line.match(/^[-*•]\s+(.+)$/);
      if (ordered || bullet) {
        flushParagraph();
        const nextType = ordered ? 'ol' : 'ul';
        if (!list || listType !== nextType) {
          flushList();
          listType = nextType;
          list = document.createElement(nextType);
          body.append(list);
        }
        const item = document.createElement('li');
        appendInline(item, (ordered || bullet)[1]);
        list.append(item);
        continue;
      }
      flushList();
      if (!paragraph) { paragraph = document.createElement('p'); body.append(paragraph); }
      else paragraph.append(document.createTextNode(' '));
      appendInline(paragraph, line);
    }
  }

  function addMessage(role, text, citations = []) {
    const item = document.createElement('article');
    item.className = `chat-message ${role}`;
    const label = document.createElement('span');
    label.className = 'chat-message-label';
    label.textContent = role === 'assistant' ? 'Trà Journey' : 'Bạn';
    const content = document.createElement('div');
    content.className = 'chat-message-body';
    if (role === 'assistant') renderFormatted(content, text);
    else { const paragraph = document.createElement('p'); paragraph.textContent = text; content.append(paragraph); }
    item.append(label, content);
    if (citations.length) {
      const list = document.createElement('div');
      list.className = 'chat-citations';
      const heading = document.createElement('span');
      heading.textContent = 'Nguồn tham khảo';
      list.append(heading);
      for (const citation of citations) {
        const link = citation.url ? document.createElement('a') : document.createElement('span');
        link.textContent = citation.title;
        if (citation.url) {
          link.href = citation.url;
          link.target = '_blank';
          link.rel = 'noopener noreferrer';
        }
        list.append(link);
      }
      item.append(list);
    }
    messages.append(item);
    scrollToBottom();
    return item;
  }

  function setOpen(open) {
    panel.hidden = !open;
    toggle.setAttribute('aria-expanded', String(open));
    if (open) window.setTimeout(() => input.focus(), 50);
  }
  toggle.addEventListener('click', () => setOpen(panel.hidden));
  close.addEventListener('click', () => { setOpen(false); toggle.focus(); });
  root.querySelectorAll('[data-chat-prompt]').forEach((button) => button.addEventListener('click', () => {
    input.value = button.dataset.chatPrompt || '';
    form.requestSubmit();
  }));
  input.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); form.requestSubmit(); }
  });
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const message = input.value.trim();
    if (!message || busy) return;
    addMessage('user', message);
    history.push({ role: 'user', content: message });
    input.value = '';
    busy = true;
    send.disabled = true;
    const loading = addMessage('assistant', 'Mình đang tìm thông tin phù hợp…');
    loading.classList.add('chat-loading');
    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, history: history.slice(-8, -1) }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.error || data.detail || `Chatbot chưa sẵn sàng (HTTP ${response.status}). Vui lòng thử lại sau.`);
      loading.remove();
      addMessage('assistant', data.answer, data.citations || []);
      history.push({ role: 'assistant', content: data.answer });
    } catch (error) {
      loading.remove();
      addMessage('assistant', error.message || 'Không kết nối được chatbot. Vui lòng thử lại.');
    } finally {
      busy = false;
      send.disabled = false;
      input.focus();
    }
  });
})();
