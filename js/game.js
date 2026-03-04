// game.js - 게임 상태 관리 엔진

const SAVE_KEY = 'eunryonghoe_save';
const STAT_MAX = 10;

class Game {
  constructor() {
    this.characterType = null;
    this.characterName = '';
    this.stats = { charm: 0, wit: 0, wealth: 0, reputation: 0 };
    this.relations = {
      lee: 0, yuna: 0, kang: 0, soyoung: 0, junho: 0
    };
    this.currentScene = null;
    this.visitedScenes = new Set();
    this.chatHistories = {}; // npcId → [{role, content}]
    this.pendingInputChoice = null; // 자유 입력 대기 중인 선택지
    this.lastInputText = ''; // 마지막 자유 입력 내용
  }

  // 캐릭터 선택 및 초기화
  startGame(characterType) {
    const preset = CHARACTER_PRESETS[characterType];
    this.characterType = characterType;
    this.characterName = preset.name;
    this.stats = { ...preset.stats };
    this.relations = { lee: 0, yuna: 0, kang: 0, soyoung: 0, junho: 0 };
    this.visitedScenes = new Set();
    this.chatHistories = {};
    this.currentScene = preset.prologueScene;
    this.saveGame();
  }

  // 씬 이동
  goToScene(sceneId) {
    if (sceneId === '__restart__') {
      this.reset();
      return null;
    }
    const scene = STORY[sceneId];
    if (!scene) { console.error('씬 없음:', sceneId); return null; }
    this.currentScene = sceneId;
    this.visitedScenes.add(sceneId);
    this.saveGame();
    return scene;
  }

  // 선택지 처리 (스탯 체크 포함)
  processChoice(choice) {
    let success = true;
    let statCheckResult = null;

    if (choice.statCheck) {
      const { stat, difficulty } = choice.statCheck;
      const roll = Math.floor(Math.random() * 10) + 1; // 1~10
      const total = this.stats[stat] + roll;
      success = total >= difficulty + 5; // stat + 랜덤 vs difficulty+5
      statCheckResult = { stat, roll, total, difficulty, success };
    }

    const nextScene = success
      ? choice.next
      : (choice.failNext || choice.next);

    // 성공 시에만 효과 적용
    if (success && choice.effects) {
      this.applyEffects(choice.effects);
    }

    this.saveGame();
    return { success, nextScene, statCheckResult };
  }

  applyEffects(effects) {
    const statKeys = ['charm', 'wit', 'wealth', 'reputation'];
    for (const [key, value] of Object.entries(effects)) {
      if (statKeys.includes(key)) {
        this.stats[key] = Math.max(0, Math.min(STAT_MAX, (this.stats[key] || 0) + value));
      } else if (key.startsWith('relations_')) {
        const npc = key.replace('relations_', '');
        this.relations[npc] = Math.max(-10, Math.min(10, (this.relations[npc] || 0) + value));
      }
    }
  }

  // NPC 채팅 기록 관리
  addChatMessage(npcId, role, content) {
    if (!this.chatHistories[npcId]) this.chatHistories[npcId] = [];
    this.chatHistories[npcId].push({ role, content });
    // 최대 20개 메시지 유지
    if (this.chatHistories[npcId].length > 20) {
      this.chatHistories[npcId] = this.chatHistories[npcId].slice(-20);
    }
  }

  getChatHistory(npcId) {
    return this.chatHistories[npcId] || [];
  }

  // 관계도 레이블
  getRelationLabel(npcId) {
    const val = this.relations[npcId] || 0;
    if (val >= 7) return { text: '깊은 신뢰', color: '#4ade80' };
    if (val >= 4) return { text: '우호적', color: '#86efac' };
    if (val >= 1) return { text: '호기심', color: '#fde68a' };
    if (val === 0) return { text: '중립', color: '#94a3b8' };
    if (val >= -3) return { text: '경계', color: '#fca5a5' };
    return { text: '적대', color: '#ef4444' };
  }

  // 저장/불러오기
  saveGame() {
    const data = {
      characterType: this.characterType,
      characterName: this.characterName,
      stats: this.stats,
      relations: this.relations,
      currentScene: this.currentScene,
      visitedScenes: [...this.visitedScenes],
      chatHistories: this.chatHistories
    };
    localStorage.setItem(SAVE_KEY, JSON.stringify(data));
  }

  loadGame() {
    const saved = localStorage.getItem(SAVE_KEY);
    if (!saved) return false;
    try {
      const data = JSON.parse(saved);
      this.characterType = data.characterType;
      this.characterName = data.characterName;
      this.stats = data.stats;
      this.relations = data.relations;
      this.currentScene = data.currentScene;
      this.visitedScenes = new Set(data.visitedScenes || []);
      this.chatHistories = data.chatHistories || {};
      return true;
    } catch {
      return false;
    }
  }

  hasSave() {
    return localStorage.getItem(SAVE_KEY) !== null;
  }

  reset() {
    localStorage.removeItem(SAVE_KEY);
    this.characterType = null;
    this.characterName = '';
    this.stats = { charm: 0, wit: 0, wealth: 0, reputation: 0 };
    this.relations = { lee: 0, yuna: 0, kang: 0, soyoung: 0, junho: 0 };
    this.currentScene = null;
    this.visitedScenes = new Set();
    this.chatHistories = {};
  }

  // 게임 상태 반환 (AI에게 전달용)
  getStateForAI() {
    return {
      characterName: this.characterName,
      stats: { ...this.stats },
      relations: { ...this.relations }
    };
  }
}

const game = new Game();
