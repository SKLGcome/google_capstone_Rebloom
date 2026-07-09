import AsyncStorage from '@react-native-async-storage/async-storage';
export const API_URL =
  'https://payton-unconfided-reluctantly.ngrok-free.dev';

export async function getRecommendation(type: string) {
  const response = await fetch(`${API_URL}/recommend`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ type }),
  });

  return await response.json();
}

export async function login(user_id: string, password: string) {
  const response = await fetch(`${API_URL}/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      user_id,
      password,
    }),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || '로그인 실패');
  }

  return data;
}

export async function signup(
  user_id: string,
  password: string,
  nickname: string
) {
  const response = await fetch(`${API_URL}/signup`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      user_id,
      password,
      nickname,
    }),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || '회원가입 실패');
  }

  return data;
}

type DiagnosisMessage = {
  role: 'ai' | 'assistant' | 'user';
  content: string;
};

export async function runDiagnosis(messages: DiagnosisMessage[]) {
  const token = await AsyncStorage.getItem('access_token');

  if (!token) {
    throw new Error('로그인이 필요합니다.');
  }

  const response = await fetch(`${API_URL}/diagnosis`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      messages,
    }),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || '진단 실패');
  }

  return data;
}
