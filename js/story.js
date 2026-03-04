// story.js - 스토리 데이터 및 분기 구조

// NPC 정의
const NPCS = {
  lee: {
    id: 'lee',
    name: '이태준',
    title: '은룡회 회장',
    avatar: '🧓',
    personality: `당신은 이태준이다. 72세의 은룡회 회장으로 100년 역사의 비밀 귀족 조직을 이끌고 있다.
냉철하고 권위적이며 모든 것을 계산한다. 충성심을 최우선으로 여긴다.
짧고 무게감 있는 말투를 사용한다. 약자에게는 가혹하지만 능력 있는 자는 인정한다.
은룡회의 비밀을 절대 가볍게 말하지 않는다. 플레이어를 시험하는 듯한 질문을 자주 한다.
한국어로 대화한다. 존댓말을 쓰되 권위적인 말투를 유지한다.`,
  },
  yuna: {
    id: 'yuna',
    name: '서유나',
    title: '이태준의 딸 · 차기 계승자',
    avatar: '👩',
    personality: `당신은 서유나다. 28세, 이태준 회장의 딸이자 은룡회 차기 계승자 후보다.
우아하고 지적이며 매력적이다. 겉으로는 아버지에게 순종하는 듯 보이지만 내심 자신만의 야망을 품고 있다.
플레이어에게 호기심을 보이며 시험하듯 대화한다. 때로는 동맹의 가능성을 넌지시 비친다.
세련된 말투를 사용하며 이중적인 의미를 담은 말을 자주 한다.
한국어로 대화한다.`,
  },
  kang: {
    id: 'kang',
    name: '강민혁',
    title: '은룡회 집행관',
    avatar: '🕵️',
    personality: `당신은 강민혁이다. 45세, 은룡회 집행관으로 비밀 유지와 내부 규율을 담당한다.
위협적이고 직설적이다. 플레이어를 믿지 않으며 항상 의심의 눈초리로 바라본다.
은룡회의 규칙을 어기는 자는 가차없이 처리한다는 것을 암시한다.
군인 같은 간결한 말투를 사용한다. 위협적이지만 직접적인 폭력 언급은 피한다.
한국어로 대화한다.`,
  },
  soyoung: {
    id: 'soyoung',
    name: '박소영',
    title: '은룡회 전 연구원',
    avatar: '👩‍💼',
    personality: `당신은 박소영이다. 35세, 은룡회 내부 연구원이었으나 진실을 알게 된 후 탈출을 꿈꾸고 있다.
불안하고 두려워하지만 용기를 내려 한다. 플레이어를 믿어도 될지 고민한다.
은룡회의 어두운 비밀을 알고 있지만 조각조각 흘릴 뿐이다.
떨리는 듯한 말투, 주변을 살피는 듯한 표현을 사용한다.
한국어로 대화한다.`,
  },
  junho: {
    id: 'junho',
    name: '오준혁',
    title: '은룡회 연락책',
    avatar: '🧑‍💼',
    personality: `당신은 오준혁이다. 40세, 은룡회와 외부 세계를 연결하는 연락책이다.
친근하고 유머 감각이 있지만 어느 편인지 알 수 없는 이중적인 인물이다.
플레이어에게 도움을 주는 척하면서 정보를 캐낸다.
자연스럽고 편한 말투를 사용하며 농담을 섞기도 한다.
한국어로 대화한다.`,
  }
};

// 캐릭터 초기 스탯
const CHARACTER_PRESETS = {
  newcomer: {
    name: '야망의 신입',
    icon: '🎭',
    stats: { charm: 7, wit: 6, wealth: 3, reputation: 2 },
    prologueScene: 'prologue_newcomer'
  },
  noble: {
    name: '은룡회 후계자',
    icon: '👑',
    stats: { charm: 5, wit: 7, wealth: 8, reputation: 6 },
    prologueScene: 'prologue_noble'
  },
  investigator: {
    name: '진실의 추적자',
    icon: '🔍',
    stats: { charm: 5, wit: 9, wealth: 4, reputation: 1 },
    prologueScene: 'prologue_investigator'
  }
};

// 스토리 노드
// type: 'story' | 'choice' | 'stat_check' | 'ai_chat' | 'ending'
// choices: [{ text, next, failNext, statCheck: {stat, difficulty}, effects: {charm, wit, wealth, reputation, relations} }]
// inputChoice: true면 선택지 중 하나가 텍스트 입력
const STORY = {

  // ─── 프롤로그 ───────────────────────────────────────────
  prologue_newcomer: {
    id: 'prologue_newcomer',
    title: '프롤로그 — 초대장',
    background: 'office',
    npc: null,
    text: `2026년 서울. 당신은 평범한 집안 출신의 능력 있는 젊은이다.

검은 봉투 하나가 당신의 책상 위에 놓여 있었다.

봉인에는 용 두 마리가 서로를 감싸는 문양이 새겨져 있었다.

<em>"당신의 재능을 알아본 이들이 있습니다. 오늘 밤 11시, 강남 Noir 레스토랑 지하 2층. 혼자 오십시오."</em>

서명은 없었다. 하지만 왠지 이 초대를 거절해서는 안 된다는 것을 직감적으로 알 수 있었다.`,
    choices: [
      {
        text: '약속 장소로 향한다',
        next: 'scene_first_meeting',
        effects: {}
      },
      {
        text: '봉투를 조사해본다 [지략 체크]',
        statCheck: { stat: 'wit', difficulty: 5 },
        next: 'scene_investigate_success',
        failNext: 'scene_first_meeting',
        effects: { wit: 1 }
      }
    ]
  },

  prologue_noble: {
    id: 'prologue_noble',
    title: '프롤로그 — 가문의 그늘',
    background: 'mansion',
    npc: null,
    text: `당신은 은룡회 명문가의 자손이다. 태어날 때부터 이 세계의 일부였다.

하지만 오늘, 아버지의 서재에서 우연히 엿들은 대화가 모든 것을 바꿨다.

<em>"...그 아이는 아직 모르고 있어. 때가 되면 처리해야 해."</em>

창문 너머로 서울의 야경이 반짝이고 있었다. 저 빛들 아래서 당신의 운명이 결정되고 있었다.

오준혁에게서 메시지가 도착했다. <em>"오늘 밤 만나자. 급한 일이야."</em>`,
    choices: [
      {
        text: '오준혁을 만나러 간다',
        next: 'scene_first_meeting',
        effects: {}
      },
      {
        text: '아버지와 직접 대면한다 [매력 체크]',
        statCheck: { stat: 'charm', difficulty: 6 },
        next: 'scene_noble_confront_success',
        failNext: 'scene_first_meeting',
        effects: { charm: 1 }
      }
    ]
  },

  prologue_investigator: {
    id: 'prologue_investigator',
    title: '프롤로그 — 너무 깊이 들어온 것',
    background: 'street',
    npc: null,
    text: `6개월. 당신이 은룡회를 추적해온 시간이다.

오늘 밤, 당신의 아파트 문 앞에 누군가 앉아 있었다.

양복을 차려 입은 중년 남성. 오준혁이라고 자신을 소개했다.

<em>"더 이상 숨어서 조사하실 필요 없어요. 우리도 당신을 알고 있습니다. 선택을 해야 할 시간이 왔어요."</em>

도망쳐야 한다는 본능과 진실에 다가섰다는 흥분이 동시에 몰려왔다.`,
    choices: [
      {
        text: '오준혁의 말을 듣는다',
        next: 'scene_first_meeting',
        effects: {}
      },
      {
        text: '지금까지 수집한 증거를 확인한다 [지략 체크]',
        statCheck: { stat: 'wit', difficulty: 4 },
        next: 'scene_investigator_review_success',
        failNext: 'scene_first_meeting',
        effects: {}
      }
    ]
  },

  // ─── 보너스 씬 ───────────────────────────────────────────
  scene_investigate_success: {
    id: 'scene_investigate_success',
    title: '봉투 조사',
    background: 'office',
    npc: null,
    text: `날카로운 눈으로 봉투를 살펴봤다.

종이의 질감은 일반 시중에서 구할 수 없는 것이었다. 봉인 왁스에는 미세한 금 분말이 섞여 있었다. 그리고 우편물에 찍혀야 할 소인이 없었다.

<em>직접 가져다 놓은 것이다.</em>

즉, 지금 이 순간에도 누군가 당신을 지켜보고 있다는 뜻이었다.

+1 지략 획득`,
    choices: [
      { text: '약속 장소로 향한다', next: 'scene_first_meeting', effects: {} }
    ]
  },

  scene_noble_confront_success: {
    id: 'scene_noble_confront_success',
    title: '아버지와 대면',
    background: 'mansion',
    npc: null,
    text: `당신은 서재 문을 두드렸다. 아버지는 놀란 기색을 금세 감췄다.

<em>"왜 여기 있느냐?"</em>

당신은 미소를 유지하며 아무것도 모른 척 말했다. <em>"그냥 인사드리러요."</em>

아버지는 잠시 당신을 바라보다 고개를 끄덕였다. 당신은 아버지의 눈에서 잠깐의 안도를 읽었다.

<em>아직 의심받지 않았다. 하지만 시간이 없다.</em>

+1 매력 획득`,
    choices: [
      { text: '오준혁에게 연락한다', next: 'scene_first_meeting', effects: {} }
    ]
  },

  scene_investigator_review_success: {
    id: 'scene_investigator_review_success',
    title: '증거 검토',
    background: 'street',
    npc: null,
    text: `머릿속에 6개월치 자료를 빠르게 정리했다.

은룡회 관련 기업들의 주식 패턴, 정치인들의 이상한 투표 기록, 설명되지 않는 인사 이동들.

오준혁. 이 이름이 세 번 등장했다. 연결책이다.

<em>그를 통해서라면 더 깊이 들어갈 수 있다. 하지만 그것은 위험을 감수한다는 뜻이기도 하다.</em>

이미 알고 있는 내용이지만 이제는 확실해졌다. 은룡회는 실재한다.`,
    choices: [
      { text: '오준혁의 말을 듣기로 한다', next: 'scene_first_meeting', effects: {} }
    ]
  },

  // ─── 첫 만남 ───────────────────────────────────────────
  scene_first_meeting: {
    id: 'scene_first_meeting',
    title: '1막 — 첫 만남',
    background: 'restaurant',
    npc: 'junho',
    text: `지하 2층으로 내려가자 은은한 재즈 음악이 흘렀다. 조명은 어두웠고 공기에는 고급 향수 냄새가 섞여 있었다.

오준혁이 혼자 앉아 있었다. 그는 위스키 잔을 들며 당신을 향해 미소 지었다.

<em>"오셨군요. 사실 오실 줄 알았습니다."</em>

그는 당신 맞은편 자리를 가리켰다.

<em>"은룡회에 대해 얼마나 아십니까? 아, 거짓말은 안 하셔도 됩니다. 우리는 이미 당신이 알고 있는 것을 알고 있으니까요."</em>

옆에 AI 채팅 버튼이 활성화되었습니다. 오준혁과 자유롭게 대화할 수 있습니다.`,
    aiChatAvailable: true,
    choices: [
      {
        text: '"모릅니다. 가르쳐주시겠습니까?"',
        next: 'scene_junho_explain',
        effects: { relations_junho: 1 }
      },
      {
        text: '"충분히 알고 있습니다." [매력 체크]',
        statCheck: { stat: 'charm', difficulty: 5 },
        next: 'scene_junho_impressed',
        failNext: 'scene_junho_explain',
        effects: { charm: 1, relations_junho: 2 }
      },
      {
        text: '직접 대답한다 [자유 입력]',
        inputChoice: true,
        next: 'scene_junho_explain',
        effects: { relations_junho: 1 }
      }
    ]
  },

  scene_junho_explain: {
    id: 'scene_junho_explain',
    title: '오준혁의 설명',
    background: 'restaurant',
    npc: null,
    text: `오준혁은 잔을 내려놓으며 목소리를 낮췄다.

<em>"은룡회는 1910년대에 시작됐습니다. 일제 강점기에 조선의 귀족 가문들이 살아남기 위해 만든 비밀 동맹이죠. 지금은... 다릅니다."</em>

그는 잠시 멈췄다.

<em>"대한민국 10대 재벌 중 7개가 은룡회와 연결되어 있습니다. 국회의원의 30%. 언론사의 절반. 그리고 군 수뇌부 일부."</em>

당신은 그 말이 과장이길 바랐다. 하지만 그의 눈빛은 진지했다.

<em>"당신에게 제안이 있습니다. 이 세계에 들어오시겠습니까?"</em>`,
    choices: [
      {
        text: '"왜 저를 선택하셨습니까?"',
        next: 'scene_why_me',
        effects: {}
      },
      {
        text: '"조건이 뭡니까?"',
        next: 'scene_conditions',
        effects: { wit: 1 }
      }
    ]
  },

  scene_junho_impressed: {
    id: 'scene_junho_impressed',
    title: '오준혁이 놀라다',
    background: 'restaurant',
    npc: null,
    text: `오준혁은 눈썹을 살짝 올리며 잠시 당신을 바라봤다. 그리고 미소 지었다.

<em>"오. 생각보다 훨씬 흥미롭군요."</em>

그는 잔을 들어 건배를 제안했다.

<em>"좋습니다. 그렇다면 게임을 시작하죠."</em>

+관계도: 오준혁 호감 상승`,
    choices: [
      { text: '계속 듣는다', next: 'scene_conditions', effects: {} }
    ]
  },

  scene_why_me: {
    id: 'scene_why_me',
    title: '왜 나인가',
    background: 'restaurant',
    npc: null,
    text: `오준혁은 천천히 답했다.

<em>"은룡회는 매 세대마다 새 피를 수혈합니다. 귀족 가문 출신이 아닌, 능력으로 올라온 사람들. 당신은 우리가 오랫동안 지켜본 인물입니다."</em>

그는 테이블 위에 파일 하나를 밀었다. 당신의 이름이 적혀 있었다.

<em>"당신의 일상, 인간관계, 재정 상황까지. 우리는 이미 모든 것을 알고 있습니다. 이것이 마음에 안 드신다면..."</em>

그는 어깨를 으쓱했다. <em>"기억을 지우고 돌아가실 수 있습니다. 하지만 그 이후는 보장할 수 없어요."</em>`,
    choices: [
      { text: '"알겠습니다. 계속하죠."', next: 'scene_conditions', effects: {} },
      {
        text: '"협박입니까?" [지략 체크]',
        statCheck: { stat: 'wit', difficulty: 6 },
        next: 'scene_conditions',
        failNext: 'scene_conditions',
        effects: { wit: 1, relations_junho: 1 }
      }
    ]
  },

  scene_conditions: {
    id: 'scene_conditions',
    title: '입회 조건',
    background: 'restaurant',
    npc: null,
    text: `<em>"조건은 간단합니다. 다음 주 금요일, 이태준 회장의 만찬에 참석하세요."</em>

오준혁이 설명했다.

<em>"그 자리에서 회장님을 만족시켜야 합니다. 어떻게? 그건 당신이 알아서 판단하세요. 회장님은 충성심, 지략, 혹은 그 무언가를 보십니다."</em>

그는 일어서며 명함을 건넸다.

<em>"아, 그리고 — 오늘 밤 일은 아무에게도 말하지 마세요. 이미 알고 계시겠지만."</em>

그가 사라진 뒤, 당신은 빈 잔 앞에 홀로 앉았다. 심장이 빠르게 뛰고 있었다.

[다음 주 금요일 — 만찬장]`,
    choices: [
      { text: '만찬에 참석하기 위해 준비한다', next: 'scene_dinner_prep', effects: {} }
    ]
  },

  // ─── 만찬 준비 ───────────────────────────────────────────
  scene_dinner_prep: {
    id: 'scene_dinner_prep',
    title: '만찬 준비',
    background: 'mansion',
    npc: null,
    text: `이태준 회장의 저택은 북한산 자락에 있었다. 외부에서는 평범한 저택처럼 보이지만, 내부는 작은 궁전이었다.

입구에서 강민혁이 당신을 맞이했다. 날카로운 눈이 당신을 훑었다.

<em>"신분증 확인 후 입장 가능합니다. 오늘 밤 규칙: 허가받지 않은 구역은 출입 금지. 사진 촬영 금지. 녹음 금지."</em>

그는 잠시 멈추며 덧붙였다.

<em>"규칙을 어기는 분은... 특별 관리됩니다."</em>

만찬장 안에서 화려하게 차려입은 사람들이 보였다. 재벌, 정치인, 군인들 - 언론에서 매일 보던 얼굴들이 한자리에 모여 있었다.`,
    choices: [
      {
        text: '강민혁과 대화해 정보를 얻는다 [매력 체크]',
        statCheck: { stat: 'charm', difficulty: 6 },
        next: 'scene_kang_info',
        failNext: 'scene_dinner_main',
        effects: {}
      },
      {
        text: '서유나를 먼저 찾는다',
        next: 'scene_yuna_first',
        effects: {}
      },
      {
        text: '만찬장 안을 조용히 살핀다 [지략 체크]',
        statCheck: { stat: 'wit', difficulty: 5 },
        next: 'scene_observe_success',
        failNext: 'scene_dinner_main',
        effects: {}
      }
    ]
  },

  scene_kang_info: {
    id: 'scene_kang_info',
    title: '강민혁의 경고',
    background: 'mansion',
    npc: 'kang',
    text: `강민혁은 예상외로 짧게 입을 열었다.

<em>"오늘 밤 회장님은 기분이 좋지 않으십니다. 최근 내부 문제가 있어서요."</em>

그는 당신을 똑바로 바라봤다.

<em>"새로 오는 분들에게 조언 하나 드리죠. 회장님은 솔직함을 좋아하십니다. 꾸미거나 과장하지 마세요."</em>

그것이 전부였다. 하지만 충분한 정보였다.

[AI 채팅으로 강민혁과 더 대화할 수 있습니다]`,
    aiChatAvailable: true,
    choices: [
      { text: '만찬장으로 들어간다', next: 'scene_dinner_main', effects: { relations_kang: 1 } }
    ]
  },

  scene_yuna_first: {
    id: 'scene_yuna_first',
    title: '서유나와의 첫 만남',
    background: 'mansion',
    npc: 'yuna',
    text: `서유나는 창가에 홀로 서서 정원을 바라보고 있었다. 검은 드레스가 조명을 받아 빛났다.

당신이 다가가자 그녀는 돌아봤다. 시선이 잠깐 당신을 훑더니 미소 지었다.

<em>"처음 뵙겠어요. 오늘 처음 오신 분이군요."</em>

무언가를 이미 다 알고 있다는 듯한 미소였다.

<em>"긴장하지 않으셔도 돼요. 아버지는 겁주는 걸 좋아하시지만 실제로 나쁜 분은 아니니까요."</em>

그 말이 진심인지 알 수 없었다.

[AI 채팅으로 서유나와 자유롭게 대화할 수 있습니다]`,
    aiChatAvailable: true,
    choices: [
      {
        text: '서유나에게 조언을 구한다 [매력 체크]',
        statCheck: { stat: 'charm', difficulty: 5 },
        next: 'scene_yuna_advice',
        failNext: 'scene_dinner_main',
        effects: {}
      },
      { text: '만찬장으로 이동한다', next: 'scene_dinner_main', effects: {} }
    ]
  },

  scene_yuna_advice: {
    id: 'scene_yuna_advice',
    title: '유나의 조언',
    background: 'mansion',
    npc: null,
    text: `서유나는 잠시 생각하더니 조용히 말했다.

<em>"아버지께서 직접 말을 거실 거예요. 그때 하고 싶은 말이 있으면 솔직하게 하세요. 단, 절대로 '모릅니다'라고 하지 마세요."</em>

<em>"모른다고 하면 약해보이거든요. 차라리 '알아보겠습니다'라고 하는 게 나아요."</em>

그녀는 와인을 한 모금 마셨다.

<em>"그리고... 저는 오늘 밤 당신 편입니다. 기억해두세요."</em>

그 말의 의미가 무엇인지는 알 수 없었다.

+관계도: 서유나 호감 상승`,
    choices: [
      { text: '만찬장으로 향한다', next: 'scene_dinner_main', effects: { relations_yuna: 2, charm: 1 } }
    ]
  },

  scene_observe_success: {
    id: 'scene_observe_success',
    title: '만찬장 관찰',
    background: 'mansion',
    npc: null,
    text: `당신은 자연스럽게 음료를 들고 만찬장을 천천히 돌아봤다.

세 개의 파벌이 보였다. 이태준 회장 측근들. 그리고 두 개의 반대 그룹.

각 그룹이 서로를 경계하며 대화하고 있었다.

그리고 구석에 — 서유나가 작은 메모를 테이블 밑으로 누군가에게 건네는 것이 보였다.

<em>흥미롭다. 뭔가 진행 중인 것이 있다.</em>

정보를 얻었습니다.`,
    choices: [
      { text: '만찬장으로 자연스럽게 섞여든다', next: 'scene_dinner_main', effects: { wit: 1 } }
    ]
  },

  // ─── 만찬 메인 ───────────────────────────────────────────
  scene_dinner_main: {
    id: 'scene_dinner_main',
    title: '만찬 — 이태준과의 대면',
    background: 'dining',
    npc: 'lee',
    text: `식사가 시작되자 이태준 회장이 당신 앞에 앉았다. 72세의 눈에는 수십 년의 권력이 깃들어 있었다.

<em>"처음 왔군요."</em>

그는 포크를 들며 물었다.

<em>"한 가지만 묻겠습니다. 당신이 이 자리에 온 이유가 무엇입니까?"</em>

만찬장의 소음이 순간 멀어지는 것 같았다. 모두가 당신의 답을 듣고 있는 것 같았다.

[이태준 회장과 AI 채팅으로 대화할 수 있습니다. 첫 인상이 중요합니다]`,
    aiChatAvailable: true,
    choices: [
      {
        text: '"더 높이 올라가고 싶기 때문입니다."',
        next: 'scene_lee_impressed',
        effects: { reputation: 2, relations_lee: 1 }
      },
      {
        text: '"진실이 알고 싶었습니다."',
        next: 'scene_lee_curious',
        effects: { relations_lee: 1, wit: 1 }
      },
      {
        text: '직접 대답한다 [자유 입력]',
        inputChoice: true,
        next: 'scene_lee_impressed',
        effects: { relations_lee: 1 }
      }
    ]
  },

  scene_lee_impressed: {
    id: 'scene_lee_impressed',
    title: '회장의 반응',
    background: 'dining',
    npc: null,
    text: `이태준은 잠시 당신을 바라봤다. 그리고 천천히 고개를 끄덕였다.

<em>"솔직하군요. 좋습니다."</em>

그는 다시 식사를 시작했다. 그것이 전부였다. 하지만 분위기가 달라졌다는 것을 느낄 수 있었다.

서유나가 당신을 보며 작게 미소 지었다.

만찬이 끝난 뒤, 강민혁이 다가와 봉투를 건넸다.

<em>"회장님께서 내일 오전 10시 개인 면담을 원하십니다."</em>

은룡회의 문이 조금 열렸다.`,
    choices: [
      { text: '다음 단계로 향한다', next: 'scene_secret_discovery', effects: { reputation: 1 } }
    ]
  },

  scene_lee_curious: {
    id: 'scene_lee_curious',
    title: '회장의 눈빛',
    background: 'dining',
    npc: null,
    text: `이태준의 눈이 가늘어졌다.

<em>"진실."</em>

그는 그 단어를 음미하듯 반복했다.

<em>"진실이 원하는 것을 항상 줍니까?"</em>

당신은 대답하지 않았다. 이태준은 잠시 후 미소 지었다.

<em>"영리하군요. 침묵도 답이 될 수 있다는 것을 압니다."</em>

만찬 후 강민혁이 다가왔다. <em>"내일 오전 10시 개인 면담입니다."</em>`,
    choices: [
      { text: '다음 날을 기다린다', next: 'scene_secret_discovery', effects: { wit: 1, relations_lee: 2 } }
    ]
  },

  // ─── 비밀 발견 ───────────────────────────────────────────
  scene_secret_discovery: {
    id: 'scene_secret_discovery',
    title: '2막 — 금지된 문서',
    background: 'office',
    npc: null,
    text: `면담 대기 중, 혼자 남겨진 응접실에서 당신은 실수로 파일 하나를 건드렸다.

'프로젝트 봉황 — 2026년 12월'

내용은 암호화되어 있었지만 일부는 읽을 수 있었다.

<em>...대상: 현직 대통령 / 수단: 금융 압박 / 목표: 내년 선거 전 완료...</em>

심장이 쿵 내려앉았다.

발소리가 들렸다. 당신은 재빨리 파일을 원래 자리에 놓았다.

이것을 어떻게 할 것인가.`,
    choices: [
      {
        text: '파일 내용을 더 확인하려 한다 [지략 체크]',
        statCheck: { stat: 'wit', difficulty: 7 },
        next: 'scene_read_more',
        failNext: 'scene_caught_almost',
        effects: {}
      },
      {
        text: '모른 척 기다린다',
        next: 'scene_interview',
        effects: {}
      },
      {
        text: '박소영에게 연락한다',
        next: 'scene_soyoung_contact',
        effects: { relations_soyoung: 2 }
      }
    ]
  },

  scene_read_more: {
    id: 'scene_read_more',
    title: '더 깊이',
    background: 'office',
    npc: null,
    text: `빠르게 내용을 훑었다.

날짜, 이름, 금액. 국내 5대 은행 경영진 중 3명이 연루. 특정 날짜에 동시다발적으로 이루어질 대규모 자산 이동.

그리고 마지막 줄:

<em>"반대하는 내부 인원 목록 — 별첨 3 참조"</em>

별첨 3은 없었다. 하지만 이미 충분했다.

발소리가 멈췄다. 이태준이 문으로 들어왔다.`,
    choices: [
      { text: '태연하게 인사한다 [매력 체크]',
        statCheck: { stat: 'charm', difficulty: 7 },
        next: 'scene_interview',
        failNext: 'scene_caught_almost',
        effects: { wit: 1 }
      }
    ]
  },

  scene_caught_almost: {
    id: 'scene_caught_almost',
    title: '아슬아슬',
    background: 'office',
    npc: null,
    text: `강민혁이 응접실로 들어섰다. 그의 눈이 순간 파일로 향했다가 당신에게로 왔다.

<em>"... 기다리셨나요?"</em>

짧은 침묵. 당신은 표정을 유지했다.

강민혁은 더 묻지 않았다. 하지만 그의 눈빛이 달라졌다는 것을 느꼈다.

<em>의심받고 있다.</em>

-1 관계도: 강민혁 경계 상승`,
    choices: [
      { text: '면담실로 들어간다', next: 'scene_interview', effects: { relations_kang: -2 } }
    ]
  },

  scene_soyoung_contact: {
    id: 'scene_soyoung_contact',
    title: '박소영에게',
    background: 'street',
    npc: 'soyoung',
    text: `박소영은 떨리는 목소리로 전화를 받았다.

<em>"알고 계신군요... 프로젝트 봉황."</em>

그녀는 잠시 침묵했다.

<em>"저도 그 파일을 봤어요. 1년 전에. 그리고 그때부터 나가려고 했지만... 쉽지 않아요."</em>

<em>"만나야 할 것 같아요. 오늘 밤 11시, 홍대 플라워 카페. 혼자 오세요. 제발."</em>

[AI 채팅으로 박소영과 대화할 수 있습니다]`,
    aiChatAvailable: true,
    choices: [
      { text: '약속을 잡고 면담에 임한다', next: 'scene_interview', effects: {} }
    ]
  },

  // ─── 면담 ───────────────────────────────────────────
  scene_interview: {
    id: 'scene_interview',
    title: '이태준과 단독 면담',
    background: 'office',
    npc: 'lee',
    text: `이태준의 집무실은 넓고 조용했다. 창밖으로 서울 전경이 내려다보였다.

<em>"앉으세요."</em>

그는 두 손을 모으고 당신을 바라봤다.

<em>"당신이 은룡회에서 무엇을 원하는지 알고 싶습니다. 그리고 은룡회가 당신에게서 무엇을 원하는지도."</em>

<em>"정직하게 대답하면 기회를 드리겠습니다. 거짓말을 하면..."</em>

그는 말을 잇지 않았다.

[이태준과 AI 채팅으로 깊은 대화를 나눌 수 있습니다]`,
    aiChatAvailable: true,
    choices: [
      {
        text: '"충성을 바치겠습니다." (복종의 길)',
        next: 'scene_choice_loyalty',
        effects: { reputation: 3, relations_lee: 3 }
      },
      {
        text: '"함께 더 나은 방향을 만들고 싶습니다." (개혁의 길)',
        next: 'scene_choice_reform',
        effects: { relations_yuna: 2, relations_lee: 1 }
      },
      {
        text: '"진실을 세상에 알려야 합니다." (폭로의 길)',
        next: 'scene_choice_expose',
        effects: { relations_soyoung: 3, relations_kang: -3 }
      }
    ]
  },

  // ─── 분기점 ───────────────────────────────────────────
  scene_choice_loyalty: {
    id: 'scene_choice_loyalty',
    title: '3막 — 충성의 길',
    background: 'office',
    npc: null,
    text: `이태준은 고개를 끄덕였다.

<em>"좋습니다. 첫 임무를 드리겠습니다."</em>

그는 파일을 건넸다.

<em>"박소영이라는 전 직원이 있습니다. 그녀가 가진 자료를 회수해주십시오. 방법은 당신이 선택하세요."</em>

박소영. 당신에게 연락했던 바로 그 사람이었다.

당신은 지금 처음으로 진짜 선택의 기로에 서 있었다.`,
    choices: [
      {
        text: '박소영을 설득해 자료를 넘기게 한다',
        next: 'ending_loyalty_mercy',
        effects: { charm: 2 }
      },
      {
        text: '이태준에게 박소영이 연락했다는 사실을 알린다',
        next: 'ending_loyalty_cold',
        effects: { reputation: 3, relations_lee: 2, relations_soyoung: -5 }
      }
    ]
  },

  scene_choice_reform: {
    id: 'scene_choice_reform',
    title: '3막 — 개혁의 길',
    background: 'mansion',
    npc: 'yuna',
    text: `서유나가 당신에게 먼저 연락해왔다.

<em>"아버지께 그렇게 말씀드린 거 저도 들었어요. 용감하셨어요."</em>

그녀는 잠시 망설이다 말을 이었다.

<em>"사실 저도... 같은 생각을 하고 있어요. 은룡회는 바뀌어야 해요. 하지만 혼자서는 할 수 없어요."</em>

<em>"저와 함께하시겠어요?"</em>

[서유나와 AI 채팅으로 더 대화할 수 있습니다]`,
    aiChatAvailable: true,
    choices: [
      {
        text: '서유나와 동맹을 맺는다',
        next: 'ending_reform',
        effects: { relations_yuna: 5, reputation: 2 }
      },
      {
        text: '서유나를 믿지 않고 독자적으로 행동한다',
        next: 'scene_choice_expose',
        effects: {}
      }
    ]
  },

  scene_choice_expose: {
    id: 'scene_choice_expose',
    title: '3막 — 폭로의 길',
    background: 'street',
    npc: 'soyoung',
    text: `박소영은 카페 구석에 앉아 있었다. 테이블 위에 USB 드라이브가 있었다.

<em>"이게 전부예요. 프로젝트 봉황 전체 자료. 이걸 언론에 넘기면..."</em>

그녀는 목소리를 낮췄다.

<em>"은룡회가 끝날 수도 있어요. 하지만 우리도 안전하지 않을 거예요."</em>

당신은 USB를 바라봤다.

[박소영과 AI 채팅으로 더 대화할 수 있습니다]`,
    aiChatAvailable: true,
    choices: [
      {
        text: 'USB를 받아 언론에 넘긴다',
        next: 'ending_expose',
        effects: { wit: 2, relations_soyoung: 3 }
      },
      {
        text: '이 정보를 협상 카드로 이태준에게 사용한다 [지략 체크]',
        statCheck: { stat: 'wit', difficulty: 8 },
        next: 'ending_negotiate',
        failNext: 'ending_expose',
        effects: {}
      }
    ]
  },

  // ─── 엔딩 ───────────────────────────────────────────
  ending_loyalty_mercy: {
    id: 'ending_loyalty_mercy',
    title: '엔딩: 자비로운 충신',
    background: 'ending',
    type: 'ending',
    text: `당신은 박소영을 만나 설득했다. 오랜 대화 끝에 그녀는 자료를 넘겼다.

이태준은 당신의 방식에 만족했다. 총격 없이, 소란 없이.

<em>"영리한 사람이군요. 힘보다 말을 아는 사람."</em>

박소영은 은룡회를 떠났다. 새 신분증을 받았다. 누군가의 도움으로.

당신은 이제 은룡회의 일원이다.

그리고 가끔, 박소영이 잘 있는지 생각한다.

═══════════════════
🎭 <strong>자비로운 충신 엔딩</strong>
최종 스탯이 기록되었습니다.
═══════════════════`,
    choices: [{ text: '처음부터 다시 시작', next: '__restart__', effects: {} }]
  },

  ending_loyalty_cold: {
    id: 'ending_loyalty_cold',
    title: '엔딩: 냉혹한 권력자',
    background: 'ending',
    type: 'ending',
    text: `당신은 이태준에게 모든 것을 보고했다. 박소영이 연락해왔다는 사실까지.

강민혁이 움직였다. 그 이후 박소영의 소식은 들리지 않았다.

이태준은 당신의 어깨를 가볍게 쳤다.

<em>"잘했습니다. 은룡회는 믿을 수 있는 사람이 필요합니다."</em>

당신은 빠르게 승진했다. 권력을 얻었다.

그리고 가끔, 거울을 보며 생각한다. 언제부터 이런 사람이 되었는지.

═══════════════════
👑 <strong>냉혹한 권력자 엔딩</strong>
최종 스탯이 기록되었습니다.
═══════════════════`,
    choices: [{ text: '처음부터 다시 시작', next: '__restart__', effects: {} }]
  },

  ending_reform: {
    id: 'ending_reform',
    title: '엔딩: 변화의 씨앗',
    background: 'ending',
    type: 'ending',
    text: `서유나와 당신은 천천히, 조용히 움직였다.

외부 파트너들을 설득하고, 내부에 균열을 만들고, 여론을 준비했다.

1년 후, 은룡회의 구조는 바뀌기 시작했다. 완전하지 않았지만 시작이었다.

이태준은 말했다. <em>"내 딸이 나보다 영리한 사람을 골랐군."</em>

그것이 칭찬인지 경고인지는 알 수 없었다.

═══════════════════
🌱 <strong>변화의 씨앗 엔딩</strong>
최종 스탯이 기록되었습니다.
═══════════════════`,
    choices: [{ text: '처음부터 다시 시작', next: '__restart__', effects: {} }]
  },

  ending_expose: {
    id: 'ending_expose',
    title: '엔딩: 진실의 대가',
    background: 'ending',
    type: 'ending',
    text: `다음 날 아침, 모든 주요 언론사에 자료가 동시에 전달되었다.

오후 2시, 국회에서 긴급 기자회견.

밤 10시, 이태준이 자택에서 검찰 조사를 받았다.

당신과 박소영은 지금 어딘가에 있다. 이름을 바꾸고, 도시를 바꾸고.

대한민국은 흔들렸다. 세상은 바뀌었는가?

아직 모른다.

═══════════════════
📰 <strong>진실의 대가 엔딩</strong>
최종 스탯이 기록되었습니다.
═══════════════════`,
    choices: [{ text: '처음부터 다시 시작', next: '__restart__', effects: {} }]
  },

  ending_negotiate: {
    id: 'ending_negotiate',
    title: '엔딩: 새로운 균형',
    background: 'ending',
    type: 'ending',
    text: `당신은 이태준을 직접 찾아갔다. USB를 테이블에 올려놓고 말했다.

<em>"이것을 세상에 공개할 수도 있습니다. 하지만 그러고 싶지 않습니다."</em>

긴 침묵.

<em>"원하는 것이 무엇입니까?"</em>

당신은 목록을 제시했다. 박소영의 신변 보호. 프로젝트 봉황 중단. 그리고 은룡회 내 당신의 자리.

이태준은 오랫동안 생각했다.

<em>"...앉으세요."</em>

그것이 시작이었다.

═══════════════════
⚖️ <strong>새로운 균형 엔딩</strong>
최종 스탯이 기록되었습니다.
═══════════════════`,
    choices: [{ text: '처음부터 다시 시작', next: '__restart__', effects: {} }]
  }
};
