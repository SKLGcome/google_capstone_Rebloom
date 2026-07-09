import AsyncStorage from '@react-native-async-storage/async-storage';
import { useRouter } from 'expo-router';
import { useEffect, useState } from 'react';
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';

import { getDisplayNickname, NICKNAME_KEY } from '../../lib/user';

export default function MyPage() {
  const router = useRouter();
  const [nickname, setNickname] = useState('나');

  useEffect(() => {
    getDisplayNickname().then(setNickname);
  }, []);

  const handleLogout = async () => {
    await AsyncStorage.removeItem('access_token');
    await AsyncStorage.removeItem(NICKNAME_KEY);
    await AsyncStorage.removeItem('hasOnboarded');
    router.replace('/login');
  };

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>{nickname}의 회복 경로</Text>
      <Text style={styles.subtitle}>작은 행동들이 쌓이고 있어요.</Text>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>미션 달성률</Text>
        <Text style={styles.bigNumber}>63%</Text>
        <Text style={styles.desc}>최근 7일 기준</Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>자기효능감 변화</Text>
        <View style={styles.fakeChart}>
          <Text style={styles.chartText}>📈 성장 그래프 영역</Text>
        </View>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>회복 경로 프리뷰</Text>
        <Text style={styles.pathText}>
          일기 쓰기 → 산책하기 → 관심 직무 탐색 → 작은 지원 경험
        </Text>
      </View>

      <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
        <Text style={styles.logoutText}>로그아웃</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F7F4EF',
    padding: 24,
  },
  title: {
    fontSize: 26,
    fontWeight: 'bold',
    color: '#3D3D3D',
    marginTop: 56,
  },
  subtitle: {
    fontSize: 14,
    color: '#777',
    marginTop: 8,
    marginBottom: 24,
  },
  card: {
    backgroundColor: '#fff',
    borderRadius: 20,
    padding: 22,
    marginBottom: 18,
  },
  cardTitle: {
    fontSize: 17,
    fontWeight: 'bold',
    color: '#3D3D3D',
    marginBottom: 12,
  },
  bigNumber: {
    fontSize: 42,
    fontWeight: 'bold',
    color: '#6DBF87',
  },
  desc: {
    fontSize: 13,
    color: '#777',
  },
  fakeChart: {
    height: 140,
    backgroundColor: '#F3F3F3',
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  chartText: {
    color: '#777',
  },
  pathText: {
    fontSize: 15,
    color: '#555',
    lineHeight: 24,
  },
  logoutButton: {
    marginTop: 30,
    backgroundColor: '#E74C3C',
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
  },
  logoutText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});
