// api.js - OpenAI API 연동 모듈

let _apiKey = null;

function setApiKey(key) {
  _apiKey = key;
}

function getApiKey() {
  return _apiKey;
}

// NPC와 AI 대화
async function chatWithNPC(npcId, chatHistory, userMessage, gameState) {
  if (!_apiKey) throw new Error('API 키가 설정되지 않았습니다');

  const npc = NPCS[npcId];
  if (!npc) throw new Error('NPC를 찾을 수 없습니다');

  // 게임 상태를 시스템 프롬프트에 추가
  const statsContext = `
현재 플레이어 정보:
- 캐릭터: ${gameState.characterName}
- 매력: ${gameState.stats.charm}/10
- 지략: ${gameState.stats.wit}/10
- 재력: ${gameState.stats.wealth}/10
- 명성: ${gameState.stats.reputation}/10
- 이 NPC와의 관계: ${gameState.relations[npcId] || 0} (음수=적대, 양수=우호)
`;

  const systemPrompt = npc.personality + '\n\n' + statsContext +
    '\n\n중요: 2-4문장으로 간결하게 답하세요. 게임 내 대화임을 기억하고 몰입감을 유지하세요.';

  const messages = [
    { role: 'system', content: systemPrompt },
    ...chatHistory,
    { role: 'user', content: userMessage }
  ];

  const response = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${_apiKey}`
    },
    body: JSON.stringify({
      model: 'gpt-4o-mini',
      messages,
      max_tokens: 300,
      temperature: 0.85
    })
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.error?.message || `API 오류: ${response.status}`);
  }

  const data = await response.json();
  return data.choices[0].message.content;
}
