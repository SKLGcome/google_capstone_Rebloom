import AsyncStorage from '@react-native-async-storage/async-storage';
import { useRouter } from 'expo-router';
import { useState } from 'react';
import {
  Alert,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { login } from '../lib/api';
import { saveNicknameFromAuth } from '../lib/user';

export default function LoginScreen() {
  const router = useRouter();

  const [userId, setUserId] = useState('');
  const [password, setPassword] = useState('');

  const handleLogin = async () => {
    try {
      const result = await login(userId, password);

      await AsyncStorage.setItem('access_token', result.access_token);
      await saveNicknameFromAuth(result);
      // 일반 로그인과 만료 후 재로그인은 온보딩을 반복하지 않고 홈으로 이동합니다.
      router.replace('/(tabs)/home');
    } catch (error: any) {
      Alert.alert('로그인 실패', error.message);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>RE:Bloom</Text>
      <Text style={styles.subtitle}>다시 피어나는 시작</Text>

      <TextInput
        style={styles.input}
        placeholder="아이디"
        value={userId}
        onChangeText={setUserId}
        autoCapitalize="none"
      />

      <TextInput
        style={styles.input}
        placeholder="비밀번호"
        value={password}
        onChangeText={setPassword}
        secureTextEntry
      />

      <TouchableOpacity style={styles.button} onPress={handleLogin}>
        <Text style={styles.buttonText}>로그인</Text>
      </TouchableOpacity>

      <TouchableOpacity onPress={() => router.push('/signup')}>
        <Text style={styles.link}>아직 계정이 없나요? 회원가입</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F7F4EF',
    padding: 24,
    justifyContent: 'center',
  },
  title: {
    fontSize: 36,
    fontWeight: 'bold',
    color: '#333',
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 16,
    color: '#777',
    textAlign: 'center',
    marginBottom: 40,
  },
  input: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    fontSize: 16,
  },
  button: {
    backgroundColor: '#6DBF87',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    marginTop: 8,
  },
  buttonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: 'bold',
  },
  link: {
    marginTop: 20,
    textAlign: 'center',
    color: '#6DBF87',
    fontWeight: 'bold',
  },
});
