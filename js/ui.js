// ui.js - UI 렌더링 관리

// ─── 화면 전환 ───────────────────────────────────────────
function showScreen(id) {
  document.querySelectorAll('.screen').forEach(s => s.classList.add('hidden'));
  document.getElementById(id).classList.remove('hidden');
}

// ─── 알림 ───────────────────────────────────────────
function showNotification(msg, type = 'info') {
  const el = document.getElementById('notification');
  el.textContent = msg;
  el.className = `notification show ${type}`;
  clearTimeout(el._timer);
  el._timer = setTimeout(() => el.classList.remove('show'), 3000);
}

// ─── 스탯 업데이트 ───────────────────────────────────────────
function updateStats() {
  const stats = game.stats;
  const statMap = {
    charm: 'stat-charm',
    wit: 'stat-wit',
    wealth: 'stat-wealth',
    reputation: 'stat-rep'
  };
  for (const [key, prefix] of Object.entries(statMap)) {
    const val = stats[key] || 0;
    const bar = document.getElementById(prefix);
    const valEl = document.getElementById(prefix + '-val');
    if (bar) bar.style.width = `${(val / 10) * 100}%`;
    if (valEl) valEl.textContent = val;
  }
}

// ─── 씬 렌더링 ───────────────────────────────────────────
function renderScene(scene) {
  if (!scene) return;

  // 배경 클래스
  const storyContainer = document.querySelector('.story-container');
  storyContainer.className = `story-container bg-${scene.background || 'default'}`;

  // 제목
  document.getElementById('scene-title').textContent = scene.title || '';

  // 본문 (타이핑 효과)
  const textEl = document.getElementById('story-text');
  textEl.innerHTML = '';
  typeText(textEl, scene.text || '', () => {
    renderChoices(scene);
  });

  // AI 채팅 버튼
  const chatBtn = document.getElementById('ai-chat-btn');
  if (chatBtn) {
    if (scene.aiChatAvailable && scene.npc) {
      chatBtn.classList.remove('hidden');
      chatBtn.dataset.npc = scene.npc;
    } else {
      chatBtn.classList.add('hidden');
    }
  }

  updateStats();
}

// 타이핑 효과
function typeText(el, html, callback, speed = 12) {
  el.innerHTML = '';
  // HTML을 파싱해서 텍스트 노드와 태그를 처리
  const temp = document.createElement('div');
  temp.innerHTML = html;
  const fullText = temp.innerHTML;

  let i = 0;
  const timer = setInterval(() => {
    i += 2;
    if (i >= fullText.length) {
      el.innerHTML = fullText;
      clearInterval(timer);
      if (callback) callback();
    } else {
      // HTML 태그가 잘리지 않도록 처리
      let chunk = fullText.substring(0, i);
      // 열린 태그가 닫히지 않은 경우 닫기
      el.innerHTML = chunk;
    }
  }, speed);

  // 클릭 시 즉시 완성
  el.onclick = () => {
    clearInterval(timer);
    el.innerHTML = fullText;
    el.onclick = null;
    if (callback) callback();
  };
}

// ─── 선택지 렌더링 ───────────────────────────────────────────
function renderChoices(scene) {
  const container = document.getElementById('choices-container');
  const inputContainer = document.getElementById('input-container');
  container.innerHTML = '';
  inputContainer.classList.add('hidden');

  if (!scene.choices || scene.type === 'ending') {
    if (scene.choices && scene.type === 'ending') {
      const btn = document.createElement('button');
      btn.className = 'choice-btn restart-btn';
      btn.textContent = scene.choices[0].text;
      btn.onclick = () => handleChoice(scene.choices[0]);
      container.appendChild(btn);
    }
    return;
  }

  scene.choices.forEach((choice, idx) => {
    if (choice.inputChoice) {
      // 자유 입력 버튼
      const btn = document.createElement('button');
      btn.className = 'choice-btn input-choice-btn';
      btn.innerHTML = `✏️ ${choice.text}`;
      btn.onclick = () => activateInputChoice(choice);
      container.appendChild(btn);
    } else {
      const btn = document.createElement('button');
      btn.className = 'choice-btn';

      let label = choice.text;
      if (choice.statCheck) {
        const statNames = { charm: '매력', wit: '지략', wealth: '재력', reputation: '명성' };
        const statName = statNames[choice.statCheck.stat] || choice.statCheck.stat;
        label += ` <span class="stat-check-tag">[${statName} 체크]</span>`;
      }
      btn.innerHTML = label;
      btn.onclick = () => handleChoice(choice);
      container.appendChild(btn);
    }
  });
}

// 자유 입력 모드 활성화
function activateInputChoice(choice) {
  game.pendingInputChoice = choice;
  const inputContainer = document.getElementById('input-container');
  const textarea = document.getElementById('player-input');
  inputContainer.classList.remove('hidden');
  textarea.value = '';
  textarea.focus();

  // 다른 선택지 비활성화
  document.querySelectorAll('.choice-btn').forEach(btn => {
    btn.disabled = true;
    btn.style.opacity = '0.4';
  });
  document.querySelector('.input-choice-btn').disabled = false;
  document.querySelector('.input-choice-btn').style.opacity = '1';
}

// ─── 선택지 처리 ───────────────────────────────────────────
function handleChoice(choice) {
  const result = game.processChoice(choice);

  // 선택지 버튼 비활성화
  document.querySelectorAll('.choice-btn').forEach(b => b.disabled = true);
  document.getElementById('input-container').classList.add('hidden');

  // 스탯 체크 결과 표시
  if (result.statCheckResult) {
    showStatCheckResult(result.statCheckResult, () => {
      proceedToScene(result.nextScene);
    });
  } else {
    setTimeout(() => proceedToScene(result.nextScene), 300);
  }
}

// 자유 입력 제출
function handleInputSubmit() {
  const text = document.getElementById('player-input').value.trim();
  if (!text) return;

  const choice = game.pendingInputChoice;
  if (!choice) return;

  game.lastInputText = text;
  game.pendingInputChoice = null;

  document.getElementById('input-container').classList.add('hidden');
  handleChoice(choice);
}

// 스탯 체크 결과 애니메이션
function showStatCheckResult(result, callback) {
  const statNames = { charm: '매력', wit: '지략', wealth: '재력', reputation: '명성' };
  const statName = statNames[result.stat] || result.stat;
  const msg = result.success
    ? `✅ ${statName} 체크 성공! (${result.total} ≥ ${result.difficulty + 5})`
    : `❌ ${statName} 체크 실패 (${result.total} < ${result.difficulty + 5})`;

  showNotification(msg, result.success ? 'success' : 'fail');
  setTimeout(callback, 1500);
}

function proceedToScene(sceneId) {
  if (sceneId === '__restart__') {
    game.reset();
    showScreen('char-screen');
    return;
  }
  const scene = game.goToScene(sceneId);
  renderScene(scene);
}

// ─── AI 채팅 모달 ───────────────────────────────────────────
let currentChatNpc = null;

function openChatModal(npcId) {
  const npc = NPCS[npcId];
  if (!npc) return;

  currentChatNpc = npcId;

  document.getElementById('chat-npc-avatar').textContent = npc.avatar;
  document.getElementById('chat-npc-name').textContent = npc.name;
  document.getElementById('chat-npc-title').textContent = npc.title;

  const messagesEl = document.getElementById('chat-messages');
  messagesEl.innerHTML = '';

  // 기존 대화 기록 복원
  const history = game.getChatHistory(npcId);
  history.forEach(msg => {
    appendChatBubble(msg.role === 'user' ? '나' : npc.name, msg.content, msg.role);
  });

  // 대화 시작 메시지 (기록 없을 때)
  if (history.length === 0) {
    appendChatBubble(npc.name, `${npc.name}이(가) 당신을 바라보고 있습니다...`, 'system');
  }

  document.getElementById('chat-modal').classList.remove('hidden');
  document.getElementById('chat-input').focus();
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function closeChatModal() {
  document.getElementById('chat-modal').classList.add('hidden');
  currentChatNpc = null;
}

function appendChatBubble(sender, text, role) {
  const messagesEl = document.getElementById('chat-messages');
  const bubble = document.createElement('div');
  bubble.className = `chat-bubble ${role}`;
  bubble.innerHTML = `<span class="chat-sender">${sender}</span><p>${text}</p>`;
  messagesEl.appendChild(bubble);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

async function sendChatMessage() {
  const input = document.getElementById('chat-input');
  const text = input.value.trim();
  if (!text || !currentChatNpc) return;

  input.value = '';
  input.disabled = true;
  document.getElementById('chat-send').disabled = true;

  const npc = NPCS[currentChatNpc];

  // 사용자 메시지 표시
  appendChatBubble('나', text, 'user');
  game.addChatMessage(currentChatNpc, 'user', text);

  // 타이핑 인디케이터
  const typingEl = document.createElement('div');
  typingEl.className = 'chat-bubble assistant typing-bubble';
  typingEl.innerHTML = `<span class="chat-sender">${npc.name}</span><div class="typing-dots"><span></span><span></span><span></span></div>`;
  document.getElementById('chat-messages').appendChild(typingEl);
  document.getElementById('chat-messages').scrollTop = 99999;

  try {
    const history = game.getChatHistory(currentChatNpc);
    const response = await chatWithNPC(
      currentChatNpc,
      history.slice(0, -1), // 방금 추가한 user 메시지 제외하고 기존 기록
      text,
      game.getStateForAI()
    );

    typingEl.remove();
    appendChatBubble(npc.name, response, 'assistant');
    game.addChatMessage(currentChatNpc, 'assistant', response);

    // 대화에 따른 관계도 미세 변동
    game.applyEffects({ [`relations_${currentChatNpc}`]: 1 });
    updateStats();

  } catch (err) {
    typingEl.remove();
    appendChatBubble('시스템', `오류: ${err.message}`, 'system');
  }

  input.disabled = false;
  document.getElementById('chat-send').disabled = false;
  input.focus();
}

// ─── 관계도 모달 ───────────────────────────────────────────
function openRelationshipModal() {
  const content = document.getElementById('relationship-content');
  content.innerHTML = '';

  const npcOrder = ['lee', 'yuna', 'kang', 'soyoung', 'junho'];
  npcOrder.forEach(npcId => {
    const npc = NPCS[npcId];
    const label = game.getRelationLabel(npcId);
    const val = game.relations[npcId] || 0;

    const item = document.createElement('div');
    item.className = 'relation-item';
    item.innerHTML = `
      <div class="relation-npc">
        <span class="relation-avatar">${npc.avatar}</span>
        <div>
          <div class="relation-name">${npc.name}</div>
          <div class="relation-title">${npc.title}</div>
        </div>
      </div>
      <div class="relation-status">
        <span class="relation-label" style="color:${label.color}">${label.text}</span>
        <div class="relation-bar-container">
          <div class="relation-bar" style="width:${((val + 10) / 20) * 100}%;background:${label.color}"></div>
        </div>
      </div>
    `;
    content.appendChild(item);
  });

  document.getElementById('relationship-modal').classList.remove('hidden');
}

function closeRelationshipModal() {
  document.getElementById('relationship-modal').classList.add('hidden');
}
