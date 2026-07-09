import { useRouter } from 'expo-router';
import { useEffect, useState } from 'react';
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';

import { getDisplayNickname } from '../../lib/user';

export default function Community() {
  const router = useRouter();
  const [nickname, setNickname] = useState('나');

  useEffect(() => {
    getDisplayNickname().then(setNickname);
  }, []);

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>소규모 챌린지방</Text>

      <View style={styles.roomHeader}>
        <Text style={styles.roomTitle}>개발직무 재도전 5기</Text>
        <Text style={styles.roomDesc}>일상 루틴 회복방 · 7명 참여 중</Text>
      </View>

      <View style={styles.feed}>
        <Text style={styles.user}>민지님</Text>
        <Text style={styles.content}>오늘은 이력서 파일만 열어봤어요. 그래도 시작!</Text>
        <TouchableOpacity style={styles.cheerButton}>
          <Text style={styles.cheerText}>토닥토닥 응원하기 💚 12</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.feed}>
        <Text style={styles.user}>준호님</Text>
        <Text style={styles.content}>산책 10분 완료했습니다.</Text>
        <TouchableOpacity style={styles.cheerButton}>
          <Text style={styles.cheerText}>토닥토닥 응원하기 💚 8</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.guideBox}>
        <Text style={styles.guideText}>
          오늘 미션을 못 해도 괜찮아요. 내일 다시 시도하면 됩니다.
        </Text>
      </View>

      <TouchableOpacity onPress={() => router.push('/mypage')}>
        <Text style={styles.link}>{nickname}의 회복 경로 보기 →</Text>
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
    marginBottom: 20,
  },
  roomHeader: {
    backgroundColor: '#E4F3E9',
    borderRadius: 20,
    padding: 20,
    marginBottom: 24,
  },
  roomTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#3D3D3D',
    marginBottom: 6,
  },
  roomDesc: {
    fontSize: 14,
    color: '#666',
  },
  feed: {
    backgroundColor: '#fff',
    borderRadius: 18,
    padding: 18,
    marginBottom: 16,
  },
  user: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#3D3D3D',
    marginBottom: 8,
  },
  content: {
    fontSize: 15,
    color: '#555',
    lineHeight: 22,
    marginBottom: 14,
  },
  cheerButton: {
    backgroundColor: '#F0F7F2',
    paddingVertical: 10,
    borderRadius: 20,
    alignItems: 'center',
  },
  cheerText: {
    color: '#4D9E68',
    fontWeight: '700',
  },
  guideBox: {
    backgroundColor: '#fff8df',
    borderRadius: 16,
    padding: 16,
    marginTop: 8,
    marginBottom: 24,
  },
  guideText: {
    color: '#7A6A3D',
    fontSize: 14,
    lineHeight: 22,
  },
  link: {
    color: '#6DBF87',
    fontWeight: '700',
    marginBottom: 40,
  },
});
