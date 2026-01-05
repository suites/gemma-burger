const sessionId = uuid.v4();
console.log('Current Session ID:', sessionId);

async function sendMessage() {
  const inputField = document.getElementById('userInput');
  const sendBtn = document.getElementById('sendBtn');
  const chatWindow = document.getElementById('chatWindow');

  const text = inputField.value.trim();
  if (!text) return;

  addMessage(text, 'user');
  inputField.value = '';
  inputField.disabled = true;
  sendBtn.disabled = true;

  const aiMessageDiv = addMessage('', 'ai');
  chatWindow.scrollTop = chatWindow.scrollHeight;

  try {
    const response = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: text,
        sessionId: sessionId, // 🟢 세션 ID 전송
      }),
    });

    if (!response.ok) throw new Error('Server Error');
    if (!response.body) throw new Error('No response body');

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value, { stream: true });
      aiMessageDiv.innerText += chunk;
      chatWindow.scrollTop = chatWindow.scrollHeight;
    }
  } catch (error) {
    aiMessageDiv.innerText += ' [Error connecting to AI]';
    console.error(error);
  } finally {
    inputField.disabled = false;
    sendBtn.disabled = false;
    inputField.focus();
  }
}

function addMessage(text, sender) {
  const chatWindow = document.getElementById('chatWindow');
  const div = document.createElement('div');
  div.className = `message ${sender}`;
  div.innerText = text;
  chatWindow.appendChild(div);
  chatWindow.scrollTop = chatWindow.scrollHeight;
  return div;
}

function handleEnter(e) {
  if (e.key === 'Enter') sendMessage();
}
