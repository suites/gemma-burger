const sessionId = uuid.v4();
let currentMessageDiv = null;
let lastSpeaker = '';

// 🟢 무한 시뮬레이션 루프 시작 함수
async function startSimulation() {
  const simBtn = document.getElementById('simBtn');
  const sendBtn = document.getElementById('sendBtn');
  const inputField = document.getElementById('userInput');

  simBtn.disabled = true;
  sendBtn.disabled = true;
  inputField.disabled = true;

  addSystemMessage('Sara has entered the shop...');

  try {
    // NestJS의 /chat/simulate 엔드포인트 호출
    const response = await fetch('/chat/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sessionId: sessionId }),
    });

    if (!response.ok) throw new Error('Simulation failed');
    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      parseAndRenderChunk(chunk);
    }
  } catch (error) {
    addSystemMessage('Error during simulation: ' + error.message);
  } finally {
    simBtn.disabled = false;
    sendBtn.disabled = false;
    inputField.disabled = false;
    addSystemMessage('Simulation finished.');
  }
}

function parseAndRenderChunk(chunk) {
  const chatWindow = document.getElementById('chatWindow');

  // 1. 화자 전환 감지 (태그가 포함되어 있는지 확인)
  if (chunk.includes('[SARA]:')) {
    currentSpeaker = 'sara';
    currentMessageDiv = createMessageDiv('sara');
  } else if (chunk.includes('[ROSY]:')) {
    currentSpeaker = 'rosy';
    currentMessageDiv = createMessageDiv('rosy');
  } else if (chunk.includes('[GORDON]:')) {
    currentSpeaker = 'gordon';
    currentMessageDiv = createMessageDiv('gordon');
  }

  // 2. 태그 제거 및 순수 텍스트 추출
  // 정규표현식을 사용하여 태그와 종료 문구를 제거합니다.
  const cleanText = chunk
    .replace(/\[SARA\]:|\[ROSY\]:|\[GORDON\]:|--- Simulation Ended ---/g, '')
    .replace(/\n\n/g, '') // 불필요한 줄바꿈 제거
    .trim();

  // 3. 내용 추가 (현재 활성화된 말풍선이 있을 경우에만)
  if (cleanText && currentMessageDiv) {
    // 기존 텍스트 뒤에 공백 하나를 추가하여 단어 연결을 자연스럽게 합니다.
    currentMessageDiv.innerText +=
      (currentMessageDiv.innerText.length > 6 ? ' ' : '') + cleanText;
    chatWindow.scrollTop = chatWindow.scrollHeight;
  }
}

function createMessageDiv(type) {
  const chatWindow = document.getElementById('chatWindow');
  const div = document.createElement('div');
  div.className = `message ${type}`;

  // 화자 이름 설정
  const nameLabel = type.charAt(0).toUpperCase() + type.slice(1);
  div.innerText = `${nameLabel}: `;

  chatWindow.appendChild(div);
  chatWindow.scrollTop = chatWindow.scrollHeight;
  return div;
}

function addSystemMessage(text) {
  const chatWindow = document.getElementById('chatWindow');
  const div = document.createElement('div');
  div.className = 'system-msg';
  div.innerText = `— ${text} —`;
  chatWindow.appendChild(div);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

// 기존 1:1 채팅 함수 (유지)
async function sendMessage() {
  const inputField = document.getElementById('userInput');
  const text = inputField.value.trim();
  if (!text) return;

  addMessage(text, 'user');
  inputField.value = '';
  const aiMessageDiv = createMessageDiv('rosy');

  const response = await fetch('/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: text, sessionId: sessionId }),
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    aiMessageDiv.innerText += decoder.decode(value, { stream: true });
  }
}

function addMessage(text, sender) {
  const chatWindow = document.getElementById('chatWindow');
  const div = document.createElement('div');
  div.className = `message ${sender}`;
  div.innerText = text;
  chatWindow.appendChild(div);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function handleEnter(e) {
  if (e.key === 'Enter') sendMessage();
}
