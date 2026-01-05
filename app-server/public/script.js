const sessionId = uuid.v4();
console.log('Current Session ID:', sessionId);

async function sendMessage() {
  const inputField = document.getElementById('userInput');
  const sendBtn = document.getElementById('sendBtn');
  const chatWindow = document.getElementById('chatWindow');

  const text = inputField.value.trim();
  if (!text) return;

  // 1. 사용자 메시지 추가
  addMessage(text, 'user');
  inputField.value = '';
  inputField.disabled = true;
  sendBtn.disabled = true;

  // 🟢 2. 요청 시작 전: "생각 중..." 애니메이션 표시
  showLoading();

  // (기존에 있던 빈 말풍선 생성 코드는 여기서 삭제함)
  let aiMessageDiv = null; // 나중에 첫 데이터가 오면 할당할 변수

  try {
    const response = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: text,
        sessionId: sessionId,
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

      // 🟢 3. 첫 번째 데이터 청크가 도착했을 때 (아직 말풍선이 없다면)
      if (!aiMessageDiv) {
        removeLoading(); // 로딩 애니메이션 제거
        aiMessageDiv = addMessage('', 'ai'); // 진짜 텍스트 말풍선 생성
      }

      // 텍스트 추가
      aiMessageDiv.innerText += chunk;
      chatWindow.scrollTop = chatWindow.scrollHeight;
    }
  } catch (error) {
    // 에러 발생 시 로딩이 떠있다면 제거하고 에러 메시지 표시
    removeLoading();
    if (!aiMessageDiv) aiMessageDiv = addMessage('', 'ai');
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

// 로딩 말풍선 표시
function showLoading() {
  const chatWindow = document.getElementById('chatWindow');
  const loaderDiv = document.createElement('div');
  loaderDiv.id = 'loading-bubble'; // 나중에 지우기 위해 ID 부여
  loaderDiv.className = 'typing-indicator'; // CSS 클래스 적용

  // 점 3개 생성
  loaderDiv.innerHTML = `
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
  `;

  chatWindow.appendChild(loaderDiv);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

// 로딩 말풍선 제거
function removeLoading() {
  const loaderDiv = document.getElementById('loading-bubble');
  if (loaderDiv) {
    loaderDiv.remove();
  }
}
