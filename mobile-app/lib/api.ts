import AsyncStorage from '@react-native-async-storage/async-storage';
import { router } from 'expo-router';

export const API_URL =
  process.env.EXPO_PUBLIC_API_URL?.trim().replace(/\/$/, '') ??
  'http://192.168.219.108:8000';

let apiRequestSequence = 0;

console.info('[API] configuration', {
  baseUrl: API_URL,
  source: process.env.EXPO_PUBLIC_API_URL ? 'EXPO_PUBLIC_API_URL' : 'fallback',
});

export async function apiFetch(path: string, options: RequestInit = {}) {
  const requestId = ++apiRequestSequence;
  const method = options.method?.toUpperCase() ?? 'GET';
  const url = `${API_URL}${path}`;
  const startedAt = Date.now();

  console.info(`[API #${requestId}] -> ${method} ${url}`);

  try {
    const response = await fetch(url, options);

    console.info(
      `[API #${requestId}] <- ${response.status} ${method} ${url} (${Date.now() - startedAt}ms)`
    );

    return response;
  } catch (error) {
    console.error(`[API #${requestId}] !! ${method} ${url}`, {
      elapsedMs: Date.now() - startedAt,
      name: error instanceof Error ? error.name : undefined,
      message: error instanceof Error ? error.message : String(error),
      cause: error instanceof Error ? error.cause : undefined,
    });
    throw error;
  }
}

// 로그인 세션만 제거하고, 최초 진단 완료 여부는 기기에 유지합니다.
const AUTH_STORAGE_KEYS = ['access_token', 'nickname'];
const SESSION_EXPIRED_MESSAGE = '로그인이 만료되었습니다. 다시 로그인해주세요.';

let isRedirectingToLogin = false;

const clearSessionAndRedirectToLogin = async () => {
  await AsyncStorage.multiRemove(AUTH_STORAGE_KEYS);

  if (!isRedirectingToLogin) {
    isRedirectingToLogin = true;
    router.replace('/login');
  }
};

const parseJsonSafely = async (response: Response) => {
  return response.json().catch(() => null);
};

const handleApiResponse = async (response: Response, fallbackMessage: string): Promise<any> => {
  const data = await parseJsonSafely(response);

  if (response.status === 401) {
    await clearSessionAndRedirectToLogin();
    throw new Error(data?.detail || SESSION_EXPIRED_MESSAGE);
  }

  if (!response.ok) {
    throw new Error(data?.detail || fallbackMessage);
  }

  return data;
};

export async function fetchWithAuth(path: string, options: RequestInit = {}) {
  const token = await AsyncStorage.getItem('access_token');

  if (!token) {
    await clearSessionAndRedirectToLogin();
    throw new Error(SESSION_EXPIRED_MESSAGE);
  }

  return apiFetch(path, {
    ...options,
    headers: {
      ...options.headers,
      Authorization: `Bearer ${token}`,
    },
  });
}

export async function getRecommendation(type: string) {
  const response = await apiFetch('/recommend', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ type }),
  });

  return await response.json();
}

export async function login(user_id: string, password: string) {
  const response = await apiFetch('/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      user_id,
      password,
    }),
  });

  return handleApiResponse(response, '로그인 실패');
}

export async function signup(
  user_id: string,
  password: string,
  nickname: string
) {
  const response = await apiFetch('/signup', {
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

  return handleApiResponse(response, '회원가입 실패');
}

type DiagnosisMessage = {
  role: 'ai' | 'assistant' | 'user';
  content: string;
};

export async function runDiagnosis(messages: DiagnosisMessage[]) {
  const response = await fetchWithAuth('/diagnosis', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      messages,
    }),
  });

  return handleApiResponse(response, '진단 실패');
}

export const getLatestDiagnosis = async () => {
  const response = await fetchWithAuth('/diagnosis/latest');

  return handleApiResponse(response, '최근 진단 결과 조회 실패');
};

export async function getRoomMessages(roomId: string) {
  const response = await fetchWithAuth(`/rooms/${roomId}/messages`);

  return handleApiResponse(response, '메시지 조회 실패');
}

export async function sendRoomMessage(roomId: string, content: string) {
  const response = await fetchWithAuth(`/rooms/${roomId}/send`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ content }),
  });

  return handleApiResponse(response, '메시지 전송 실패');
}

export type DailyMission = {
  id: number;
  mission_name: string;
  mission_date: string;
  recovery_type: string;
  mission_content: string;
  created_at: string;
  is_completed: boolean;
  completed_at: string | null;
};

export async function getRoomDailyMission(roomId: string): Promise<DailyMission> {
  const response = await fetchWithAuth(
    `/missions/rooms/${encodeURIComponent(roomId)}/today`
  );

  return handleApiResponse(response, '오늘의 미션 조회 실패');
}

export async function completeRoomDailyMission(roomId: string) {
  const response = await fetchWithAuth(
    `/missions/rooms/${encodeURIComponent(roomId)}/today/complete`,
    { method: 'POST' }
  );

  return handleApiResponse(response, '미션 인증 실패');
}
