import AsyncStorage from '@react-native-async-storage/async-storage';

import { API_URL } from './api';

export const NICKNAME_KEY = 'nickname';

type UserResponse = {
  nickname?: string;
};

type AuthResponse = {
  user?: UserResponse;
};

const normalizeNickname = (nickname?: string | null) => {
  const trimmed = nickname?.trim();
  return trimmed ? trimmed : null;
};

export const saveNicknameFromAuth = async (result: AuthResponse) => {
  const nickname = normalizeNickname(result.user?.nickname);

  if (nickname) {
    await AsyncStorage.setItem(NICKNAME_KEY, nickname);
  }
};

export const getDisplayNickname = async () => {
  const storedNickname = normalizeNickname(await AsyncStorage.getItem(NICKNAME_KEY));

  if (storedNickname) {
    return storedNickname;
  }

  const token = await AsyncStorage.getItem('access_token');

  if (!token) {
    return '나';
  }

  try {
    const response = await fetch(`${API_URL}/me`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      return '나';
    }

    const user = (await response.json()) as UserResponse;
    const nickname = normalizeNickname(user.nickname);

    if (nickname) {
      await AsyncStorage.setItem(NICKNAME_KEY, nickname);
      return nickname;
    }
  } catch {
    return '나';
  }

  return '나';
};
