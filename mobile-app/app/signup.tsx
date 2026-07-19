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
import { login, signup } from '../lib/api';
import { saveNicknameFromAuth } from '../lib/user';

export default function SignupScreen() {
  const router = useRouter();

  const [userId, setUserId] = useState('');
  const [password, setPassword] = useState('');
  const [nickname, setNickname] = useState('');

  const handleSignup = async () => {
    try {
      await signup(userId, password, nickname);
      const result = await login(userId, password);

      await AsyncStorage.multiSet([
        ['access_token', result.access_token],
        ['hasOnboarded', 'false'],
      ]);
      await saveNicknameFromAuth(result);
      router.replace({
        pathname: '/(tabs)/diagnose_chat',
        params: { reset: Date.now().toString() },
      });
    } catch (error: any) {
      Alert.alert('회원가입 실패', error.message);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>회원가입</Text>

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
        secureTextEntry
        value={password}
        onChangeText={setPassword}
      />

      <TextInput
        style={styles.input}
        placeholder="닉네임"
        value={nickname}
        onChangeText={setNickname}
      />

      <TouchableOpacity
        style={styles.button}
        onPress={handleSignup}
      >
        <Text style={styles.buttonText}>회원가입</Text>
      </TouchableOpacity>

      <TouchableOpacity
        onPress={() => router.replace('/login')}
      >
        <Text style={styles.link}>
          이미 계정이 있나요? 로그인
        </Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F7F4EF',
    justifyContent: 'center',
    padding: 24,
  },
  title: {
    fontSize: 34,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 40,
    color: '#333',
  },
  input: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    fontSize: 16,
  },
  button: {
    backgroundColor: '#6DBF87',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 8,
  },
  buttonText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 16,
  },
  link: {
    marginTop: 20,
    textAlign: 'center',
    color: '#6DBF87',
    fontWeight: 'bold',
  },
});
