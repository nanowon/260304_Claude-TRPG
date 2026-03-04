// crypto.js - API 키 암호화/복호화 모듈
// Web Crypto API (PBKDF2 + AES-GCM) 사용

const STORAGE_KEY = 'eunryonghoe_encrypted_key';
const SESSION_KEY = 'eunryonghoe_session';

// 문자열 → ArrayBuffer
function strToBuffer(str) {
  return new TextEncoder().encode(str);
}

// ArrayBuffer → Base64
function bufferToBase64(buffer) {
  return btoa(String.fromCharCode(...new Uint8Array(buffer)));
}

// Base64 → ArrayBuffer
function base64ToBuffer(base64) {
  const binary = atob(base64);
  const buffer = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) buffer[i] = binary.charCodeAt(i);
  return buffer.buffer;
}

// 비밀번호로부터 AES 키 유도 (PBKDF2)
async function deriveKey(password, salt) {
  const keyMaterial = await crypto.subtle.importKey(
    'raw',
    strToBuffer(password),
    { name: 'PBKDF2' },
    false,
    ['deriveKey']
  );
  return crypto.subtle.deriveKey(
    {
      name: 'PBKDF2',
      salt: salt,
      iterations: 250000,
      hash: 'SHA-256'
    },
    keyMaterial,
    { name: 'AES-GCM', length: 256 },
    false,
    ['encrypt', 'decrypt']
  );
}

// API 키 암호화 후 localStorage에 저장
async function encryptAndStore(apiKey, password) {
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const key = await deriveKey(password, salt);

  const encrypted = await crypto.subtle.encrypt(
    { name: 'AES-GCM', iv },
    key,
    strToBuffer(apiKey)
  );

  const data = {
    salt: bufferToBase64(salt),
    iv: bufferToBase64(iv),
    data: bufferToBase64(encrypted)
  };

  localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
}

// localStorage에서 복호화하여 API 키 반환
async function decryptStored(password) {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (!stored) throw new Error('저장된 키 없음');

  const { salt, iv, data } = JSON.parse(stored);
  const key = await deriveKey(password, base64ToBuffer(salt));

  try {
    const decrypted = await crypto.subtle.decrypt(
      { name: 'AES-GCM', iv: base64ToBuffer(iv) },
      key,
      base64ToBuffer(data)
    );
    return new TextDecoder().decode(decrypted);
  } catch {
    throw new Error('잘못된 암호입니다');
  }
}

// 저장된 키가 있는지 확인
function hasStoredKey() {
  return localStorage.getItem(STORAGE_KEY) !== null;
}

// 세션에 복호화된 키 임시 저장 (탭 닫으면 삭제)
function saveSession(apiKey) {
  sessionStorage.setItem(SESSION_KEY, apiKey);
}

function getSession() {
  return sessionStorage.getItem(SESSION_KEY);
}

function clearSession() {
  sessionStorage.removeItem(SESSION_KEY);
}

// 전체 초기화 (키 + 세션 삭제)
function resetAll() {
  localStorage.removeItem(STORAGE_KEY);
  sessionStorage.removeItem(SESSION_KEY);
}
