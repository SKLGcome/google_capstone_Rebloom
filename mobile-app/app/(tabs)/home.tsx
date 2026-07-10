import { useRouter } from 'expo-router';
import { ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';

export default function Home() {
  const router = useRouter();

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <View>
          <Text style={styles.title}>안녕하세요 👋</Text>
          <Text style={styles.subtitle}>오늘은 이것 하나만 해도 충분해요.</Text>
        </View>

        <TouchableOpacity
          style={styles.diagnoseButton}
          onPress={() =>
            router.push({
              pathname: '/diagnose_chat',
              params: { reset: Date.now().toString() },
            })
          }
        >
          <Text style={styles.diagnoseButtonText}>상태 진단</Text>
        </TouchableOpacity>
      </View>

      <Text style={styles.sectionTitle}>오늘의 1개 미션</Text>

      <View style={styles.bigCard}>
        <Text style={styles.emoji}>📓</Text>
        <Text style={styles.missionTitle}>오늘 한 일 1개 기록하기</Text>
        <Text style={styles.missionDesc}>
          침대에서 일어난 것, 씻은 것, 밥을 먹은 것도 좋아요.
        </Text>
      </View>

      <Text style={styles.sectionTitle}>미션 인증</Text>
      <TextInput
        style={styles.input}
        placeholder="오늘 한 일을 한 줄로 남겨보세요."
      />

      <TouchableOpacity style={styles.button}>
        <Text style={styles.buttonText}>인증 완료하기</Text>
      </TouchableOpacity>

      <Text style={styles.sectionTitle}>추천 청년정책</Text>

      <View style={styles.policyCard}>
        <Text style={styles.policyTitle}>청년도전지원사업</Text>
        <Text style={styles.policyDesc}>
          구직단념 청년의 사회 진입을 돕는 프로그램
        </Text>
      </View>

      <View style={styles.policyCard}>
        <Text style={styles.policyTitle}>국민취업지원제도</Text>
        <Text style={styles.policyDesc}>
          취업 준비와 생활 안정을 함께 지원하는 제도
        </Text>
      </View>

      <TouchableOpacity onPress={() => router.push('/chat_room')}>
        <Text style={styles.link}>커뮤니티로 이동하기 →</Text>
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
  header: {
    marginTop: 56,
    marginBottom: 28,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  title: {
    fontSize: 25,
    fontWeight: 'bold',
    color: '#3D3D3D',
  },
  subtitle: {
    fontSize: 14,
    color: '#777',
    marginTop: 8,
  },
  diagnoseButton: {
    backgroundColor: '#E4F3E9',
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderRadius: 20,
  },
  diagnoseButtonText: {
    color: '#4D9E68',
    fontWeight: '700',
    fontSize: 13,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#3D3D3D',
    marginBottom: 12,
  },
  bigCard: {
    backgroundColor: '#fff',
    borderRadius: 24,
    padding: 28,
    marginBottom: 28,
  },
  emoji: {
    fontSize: 40,
    marginBottom: 16,
  },
  missionTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#3D3D3D',
    marginBottom: 12,
  },
  missionDesc: {
    fontSize: 15,
    color: '#777',
    lineHeight: 23,
  },
  input: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 16,
    fontSize: 15,
    marginBottom: 12,
  },
  button: {
    backgroundColor: '#6DBF87',
    paddingVertical: 15,
    borderRadius: 24,
    alignItems: 'center',
    marginBottom: 28,
  },
  buttonText: {
    color: '#fff',
    fontWeight: '700',
  },
  policyCard: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 18,
    marginBottom: 12,
  },
  policyTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#3D3D3D',
    marginBottom: 6,
  },
  policyDesc: {
    fontSize: 13,
    color: '#777',
  },
  link: {
    color: '#6DBF87',
    fontWeight: '700',
    marginTop: 8,
    marginBottom: 40,
  },
});
