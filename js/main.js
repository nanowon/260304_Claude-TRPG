// main.js - 진입점 및 이벤트 연결

document.addEventListener('DOMContentLoaded', async () => {

  // ─── 인증 화면 초기화 ───────────────────────────────────────────
  if (hasStoredKey()) {
    // 세션이 살아있으면 바로 게임으로
    const sessionKey = getSession();
    if (sessionKey) {
      setApiKey(sessionKey);
      initGame();
      return;
    }
    // 로그인 폼 표시
    document.getElementById('login-form').classList.remove('hidden');
  } else {
    // 최초 설정 폼 표시
    document.getElementById('setup-form').classList.remove('hidden');
  }

  // ─── 최초 설정 ───────────────────────────────────────────
  document.getElementById('setup-btn').addEventListener('click', async () => {
    const apiKey = document.getElementById('setup-api-key').value.trim();
    const pw = document.getElementById('setup-password').value;
    const pw2 = document.getElementById('setup-password-confirm').value;
    const errEl = document.getElementById('setup-error');

    if (!apiKey.startsWith('sk-')) {
      showSetupError(errEl, 'OpenAI API 키는 sk-로 시작해야 합니다');
      return;
    }
    if (pw.length < 4) {
      showSetupError(errEl, '암호는 4자 이상이어야 합니다');
      return;
    }
    if (pw !== pw2) {
      showSetupError(errEl, '암호가 일치하지 않습니다');
      return;
    }

    try {
      const btn = document.getElementById('setup-btn');
      btn.textContent = '저장 중...';
      btn.disabled = true;

      await encryptAndStore(apiKey, pw);
      setApiKey(apiKey);
      saveSession(apiKey);
      initGame();
    } catch (e) {
      showSetupError(errEl, '오류: ' + e.message);
      document.getElementById('setup-btn').textContent = '설정 완료';
      document.getElementById('setup-btn').disabled = false;
    }
  });

  // Enter 키로 설정
  document.getElementById('setup-password-confirm').addEventListener('keydown', e => {
    if (e.key === 'Enter') document.getElementById('setup-btn').click();
  });

  // ─── 로그인 ───────────────────────────────────────────
  document.getElementById('login-btn').addEventListener('click', async () => {
    const pw = document.getElementById('login-password').value;
    const errEl = document.getElementById('login-error');

    try {
      const btn = document.getElementById('login-btn');
      btn.textContent = '확인 중...';
      btn.disabled = true;

      const apiKey = await decryptStored(pw);
      setApiKey(apiKey);
      saveSession(apiKey);
      initGame();
    } catch (e) {
      errEl.textContent = e.message || '암호가 올바르지 않습니다';
      errEl.classList.remove('hidden');
      document.getElementById('login-btn').textContent = '입장';
      document.getElementById('login-btn').disabled = false;
    }
  });

  document.getElementById('login-password').addEventListener('keydown', e => {
    if (e.key === 'Enter') document.getElementById('login-btn').click();
  });

  // ─── 초기화 버튼 ───────────────────────────────────────────
  document.getElementById('reset-btn').addEventListener('click', () => {
    if (confirm('API 키와 저장 데이터를 모두 삭제합니다. 계속하시겠습니까?')) {
      resetAll();
      game.reset();
      location.reload();
    }
  });
});

function showSetupError(el, msg) {
  el.textContent = msg;
  el.classList.remove('hidden');
}

// ─── 게임 초기화 ───────────────────────────────────────────
function initGame() {
  setupGameEvents();

  // 저장 데이터 확인
  if (game.loadGame() && game.currentScene) {
    showScreen('game-screen');
    updateStats();
    const scene = STORY[game.currentScene];
    renderScene(scene);
    showNotification('이전 게임을 불러왔습니다', 'info');
  } else {
    showScreen('char-screen');
    setupCharacterSelect();
  }
}

// ─── 캐릭터 선택 ───────────────────────────────────────────
function setupCharacterSelect() {
  document.querySelectorAll('.char-card').forEach(card => {
    card.addEventListener('click', () => {
      document.querySelectorAll('.char-card').forEach(c => c.classList.remove('selected'));
      card.classList.add('selected');

      const charType = card.dataset.char;
      setTimeout(() => {
        game.startGame(charType);
        showScreen('game-screen');
        updateStats();
        const scene = STORY[game.currentScene];
        renderScene(scene);
      }, 400);
    });
  });
}

// ─── 게임 내 이벤트 ───────────────────────────────────────────
function setupGameEvents() {
  // 관계도 버튼
  document.getElementById('relationship-btn').addEventListener('click', openRelationshipModal);
  document.getElementById('close-relationship').addEventListener('click', closeRelationshipModal);
  document.getElementById('relationship-modal').addEventListener('click', e => {
    if (e.target === document.getElementById('relationship-modal')) closeRelationshipModal();
  });

  // AI 채팅 버튼
  const chatBtn = document.createElement('button');
  chatBtn.id = 'ai-chat-btn';
  chatBtn.className = 'btn-ai-chat hidden';
  chatBtn.innerHTML = '💬 대화하기';
  chatBtn.addEventListener('click', () => {
    const scene = STORY[game.currentScene];
    if (scene && scene.npc) openChatModal(scene.npc);
  });
  document.querySelector('.game-header').appendChild(chatBtn);

  // 채팅 모달
  document.getElementById('close-chat').addEventListener('click', closeChatModal);
  document.getElementById('end-chat').addEventListener('click', closeChatModal);
  document.getElementById('chat-send').addEventListener('click', sendChatMessage);
  document.getElementById('chat-input').addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendChatMessage();
    }
  });
  document.getElementById('chat-modal').addEventListener('click', e => {
    if (e.target === document.getElementById('chat-modal')) closeChatModal();
  });

  // 자유 입력 제출
  document.getElementById('submit-input').addEventListener('click', handleInputSubmit);
  document.getElementById('player-input').addEventListener('keydown', e => {
    if (e.key === 'Enter' && e.ctrlKey) handleInputSubmit();
  });
}
