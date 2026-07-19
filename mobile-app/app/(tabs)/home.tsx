import { FontAwesome } from '@expo/vector-icons';
import { useFocusEffect, useRouter } from 'expo-router';
import { useCallback, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';

import {
  completeRoomDailyMission,
  DailyMission,
  getLatestDiagnosis,
  getRoomDailyMission,
} from '@/lib/api';

export default function Home() {
  const router = useRouter();
  const [mission, setMission] = useState<DailyMission | null>(null);
  const [roomId, setRoomId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isCompleting, setIsCompleting] = useState(false);

  const loadMission = useCallback(async () => {
    setIsLoading(true);
    try {
      const diagnosis = await getLatestDiagnosis();
      const nextRoomId = `type_${diagnosis.type}`;
      setRoomId(nextRoomId);
      setMission(await getRoomDailyMission(nextRoomId));
    } catch (error) {
      console.warn('홈에서 오늘의 미션을 불러오지 못했습니다.', error);
      setMission(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useFocusEffect(useCallback(() => void loadMission(), [loadMission]));

  const handleComplete = async () => {
    if (!roomId || !mission || mission.is_completed) return;

    setIsCompleting(true);
    try {
      const completion = await completeRoomDailyMission(roomId);
      setMission((current) =>
        current
          ? { ...current, is_completed: true, completed_at: completion.completed_at }
          : current
      );
      Alert.alert('미션 인증 완료', '오늘의 한 걸음을 멋지게 남겼어요!');
    } catch (error) {
      Alert.alert(
        '인증하지 못했어요',
        error instanceof Error ? error.message : '잠시 후 다시 시도해 주세요.'
      );
    } finally {
      setIsCompleting(false);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.header}>
        <View style={styles.headerCopy}>
          <Text style={styles.eyebrow}>RE:BLOOM TODAY</Text>
          <Text style={styles.title}>오늘도 한 걸음이면 충분해요</Text>
          <Text style={styles.subtitle}>같은 회복 유형의 커뮤니티와 함께해요.</Text>
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
          <FontAwesome name="compass" size={15} color="#2F7D55" />
          <Text style={styles.diagnoseButtonText}>상태 진단</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.sectionHeader}>
        <Text style={styles.sectionTitle}>오늘의 커뮤니티 미션</Text>
        {mission ? (
          <View style={styles.typeBadge}>
            <Text style={styles.typeBadgeText}>{mission.recovery_type}</Text>
          </View>
        ) : null}
      </View>

      <View style={styles.missionCard}>
        {isLoading ? (
          <View style={styles.loadingBox}>
            <ActivityIndicator color="#2F7D55" />
            <Text style={styles.loadingText}>오늘의 미션을 불러오고 있어요</Text>
          </View>
        ) : mission ? (
          <>
            <View style={styles.missionTopRow}>
              <View style={styles.iconCircle}>
                <FontAwesome
                  name={mission.is_completed ? 'check' : 'leaf'}
                  size={19}
                  color="#FFFFFF"
                />
              </View>
              <Text style={styles.dayLabel}>오늘 딱 하나</Text>
              <Text style={styles.communityLabel}>우리 커뮤니티 공동 미션</Text>
            </View>

            <Text style={styles.missionTitle}>{mission.mission_name}</Text>
            <Text style={styles.missionDescription}>{mission.mission_content}</Text>

            <View style={styles.divider} />
            <View style={styles.progressRow}>
              <View style={[styles.stepDot, styles.stepDotDone]}>
                <FontAwesome name="check" size={10} color="#FFFFFF" />
              </View>
              <View style={[styles.stepLine, mission.is_completed && styles.stepLineDone]} />
              <View style={[styles.stepDot, mission.is_completed && styles.stepDotDone]}>
                {mission.is_completed ? (
                  <FontAwesome name="check" size={10} color="#FFFFFF" />
                ) : null}
              </View>
            </View>
            <View style={styles.progressLabels}>
              <Text style={styles.progressLabelDone}>미션 확인</Text>
              <Text style={mission.is_completed ? styles.progressLabelDone : styles.progressLabel}>
                오늘 인증
              </Text>
            </View>

            <TouchableOpacity
              style={[styles.completeButton, mission.is_completed && styles.completedButton]}
              onPress={handleComplete}
              disabled={isCompleting || mission.is_completed}
              activeOpacity={0.85}
            >
              {isCompleting ? (
                <ActivityIndicator color="#FFFFFF" />
              ) : (
                <>
                  <FontAwesome
                    name={mission.is_completed ? 'check-circle' : 'camera'}
                    size={17}
                    color="#FFFFFF"
                  />
                  <Text style={styles.completeButtonText}>
                    {mission.is_completed ? '오늘의 미션 인증 완료' : '미션 인증하기'}
                  </Text>
                </>
              )}
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.communityLink}
              onPress={() => router.push('/chat_room')}
            >
              <Text style={styles.communityLinkText}>커뮤니티 이야기 보러 가기</Text>
              <FontAwesome name="angle-right" size={18} color="#2F7D55" />
            </TouchableOpacity>
          </>
        ) : (
          <View style={styles.emptyBox}>
            <View style={styles.emptyIcon}>
              <FontAwesome name="leaf" size={22} color="#6DBF87" />
            </View>
            <Text style={styles.emptyTitle}>오늘의 미션을 준비하고 있어요</Text>
            <Text style={styles.emptyText}>진단을 완료하거나 잠시 후 다시 확인해 주세요.</Text>
            <TouchableOpacity style={styles.retryButton} onPress={loadMission}>
              <Text style={styles.retryButtonText}>다시 불러오기</Text>
            </TouchableOpacity>
          </View>
        )}
      </View>

      <Text style={styles.sectionTitle}>작은 실천을 이어가요</Text>
      <View style={styles.tipCard}>
        <View style={styles.tipIcon}>
          <FontAwesome name="heart" size={16} color="#D8756C" />
        </View>
        <View style={styles.tipBody}>
          <Text style={styles.tipTitle}>완벽하게 하지 않아도 괜찮아요</Text>
          <Text style={styles.tipText}>오늘 할 수 있는 만큼 실천하고 인증하면 충분해요.</Text>
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F6F3ED' },
  content: { paddingHorizontal: 22, paddingTop: 62, paddingBottom: 120 },
  header: { flexDirection: 'row', alignItems: 'flex-start', marginBottom: 34, gap: 12 },
  headerCopy: { flex: 1 },
  eyebrow: { color: '#2F7D55', fontSize: 11, fontWeight: '900', letterSpacing: 1.4, marginBottom: 7 },
  title: { color: '#27352D', fontSize: 25, fontWeight: '800', lineHeight: 33 },
  subtitle: { color: '#7A817C', fontSize: 14, marginTop: 7 },
  diagnoseButton: { flexDirection: 'row', alignItems: 'center', gap: 6, backgroundColor: '#E3F1E7', borderRadius: 999, paddingHorizontal: 13, paddingVertical: 10 },
  diagnoseButtonText: { color: '#2F7D55', fontSize: 12, fontWeight: '800' },
  sectionHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 12 },
  sectionTitle: { color: '#313A34', fontSize: 18, fontWeight: '800', marginBottom: 12 },
  typeBadge: { marginLeft: 'auto', backgroundColor: '#E3F1E7', borderRadius: 999, paddingHorizontal: 10, paddingVertical: 5 },
  typeBadgeText: { color: '#2F7D55', fontSize: 11, fontWeight: '900' },
  missionCard: { backgroundColor: '#FFFFFF', borderRadius: 28, padding: 22, marginBottom: 30, shadowColor: '#395642', shadowOffset: { width: 0, height: 8 }, shadowOpacity: 0.08, shadowRadius: 20, elevation: 4 },
  loadingBox: { alignItems: 'center', paddingVertical: 48, gap: 14 },
  loadingText: { color: '#7A817C', fontSize: 14 },
  missionTopRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 20 },
  iconCircle: { width: 38, height: 38, borderRadius: 19, backgroundColor: '#5FAF78', alignItems: 'center', justifyContent: 'center', marginRight: 10 },
  dayLabel: { color: '#2F7D55', fontSize: 13, fontWeight: '900' },
  communityLabel: { color: '#9A9F9B', fontSize: 11, marginLeft: 'auto' },
  missionTitle: { color: '#27352D', fontSize: 24, fontWeight: '900', lineHeight: 32, marginBottom: 11 },
  missionDescription: { color: '#68716B', fontSize: 15, lineHeight: 23 },
  divider: { height: 1, backgroundColor: '#EDF0ED', marginVertical: 22 },
  progressRow: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 25 },
  stepDot: { width: 20, height: 20, borderRadius: 10, borderWidth: 2, borderColor: '#D8DDD9', backgroundColor: '#FFFFFF', alignItems: 'center', justifyContent: 'center' },
  stepDotDone: { borderColor: '#65B77E', backgroundColor: '#65B77E' },
  stepLine: { flex: 1, height: 3, backgroundColor: '#E3E7E4' },
  stepLineDone: { backgroundColor: '#65B77E' },
  progressLabels: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 8, paddingHorizontal: 5, marginBottom: 20 },
  progressLabel: { color: '#9A9F9B', fontSize: 11, fontWeight: '700' },
  progressLabelDone: { color: '#2F7D55', fontSize: 11, fontWeight: '800' },
  completeButton: { minHeight: 52, borderRadius: 17, backgroundColor: '#4FA66B', flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 9 },
  completedButton: { backgroundColor: '#8BB99A' },
  completeButtonText: { color: '#FFFFFF', fontSize: 15, fontWeight: '900' },
  communityLink: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 7, paddingTop: 17 },
  communityLinkText: { color: '#2F7D55', fontSize: 13, fontWeight: '800' },
  emptyBox: { alignItems: 'center', paddingVertical: 30 },
  emptyIcon: { width: 54, height: 54, borderRadius: 27, backgroundColor: '#E9F5EC', alignItems: 'center', justifyContent: 'center', marginBottom: 15 },
  emptyTitle: { color: '#313A34', fontSize: 17, fontWeight: '800', marginBottom: 7 },
  emptyText: { color: '#858B87', fontSize: 13, textAlign: 'center', lineHeight: 20 },
  retryButton: { marginTop: 18, backgroundColor: '#E3F1E7', borderRadius: 14, paddingHorizontal: 18, paddingVertical: 10 },
  retryButtonText: { color: '#2F7D55', fontSize: 13, fontWeight: '800' },
  tipCard: { backgroundColor: '#FFF9F5', borderRadius: 20, padding: 18, flexDirection: 'row', alignItems: 'center', borderWidth: 1, borderColor: '#F2E8E0' },
  tipIcon: { width: 38, height: 38, borderRadius: 19, backgroundColor: '#FBEAE5', alignItems: 'center', justifyContent: 'center', marginRight: 12 },
  tipBody: { flex: 1 },
  tipTitle: { color: '#4A3E39', fontSize: 14, fontWeight: '800', marginBottom: 4 },
  tipText: { color: '#8A7A73', fontSize: 12, lineHeight: 18 },
});
