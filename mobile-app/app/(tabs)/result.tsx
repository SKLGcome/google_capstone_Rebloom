import { FontAwesome } from '@expo/vector-icons';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useEffect, useState } from 'react';
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';

import { getDisplayNickname } from '../../lib/user';
import { typeMap } from '../../lib/typeMapper';

type ScoreKey = 'energy' | 'direction' | 'action';

type Scores = Partial<Record<ScoreKey, number>>;

const scoreMeta: Record<ScoreKey, { label: string; description: string }> = {
  energy: {
    label: '에너지',
    description: '매일 움직일 수 있는 기본 체력',
  },
  direction: {
    label: '방향성',
    description: '목표가 얼마나 또렷한지',
  },
  action: {
    label: '실행력',
    description: '작게라도 시작하고 이어가는 힘',
  },
};

const focusAdvice: Record<ScoreKey, string> = {
  energy: '오늘은 할 일을 늘리기보다 회복 시간을 먼저 확보해보세요.',
  direction: '목표 직무 하나를 정하고, 필요한 역량을 3개만 적어보세요.',
  action: '완성보다 시작에 맞춰 20분짜리 행동 하나를 정해보세요.',
};

const parseJsonParam = <T,>(value: string | string[] | undefined, fallback: T): T => {
  const rawValue = Array.isArray(value) ? value[0] : value;

  if (!rawValue) {
    return fallback;
  }

  try {
    return JSON.parse(rawValue) as T;
  } catch {
    return fallback;
  }
};

const getPrimaryFocus = (scores: Scores): ScoreKey => {
  const entries = (Object.keys(scoreMeta) as ScoreKey[]).map((key) => ({
    key,
    value: scores[key] ?? 0,
  }));

  return entries.sort((a, b) => a.value - b.value)[0]?.key ?? 'action';
};

const getTodayAction = (focus: ScoreKey, needTopics: string[], goal?: string) => {
  const firstNeed = needTopics[0];

  if (focus === 'energy') {
    return '무리한 계획 대신 15분 산책이나 휴식 기록처럼 몸이 먼저 풀리는 일을 해보세요.';
  }

  if (focus === 'direction') {
    return `${goal ? `${goal} 목표에 맞춰 ` : ''}관심 직무 공고 1개를 보고 필요한 역량을 3개만 표시해보세요.`;
  }

  return `${firstNeed ? `${firstNeed}을(를) ` : '가장 부담되는 준비를 '}20분만 해보고, 한 줄로 오늘 한 일을 남겨보세요.`;
};

export default function Result() {
  const router = useRouter();
  const [nickname, setNickname] = useState('나');
  const {
    type,
    summary,
    strengthTopics,
    needTopics,
    goal,
    scores: scoresParam,
    reset,
  } = useLocalSearchParams();

  const recoveryType = Array.isArray(type) ? type[0] : type;
  const typeInfo = typeMap[recoveryType as keyof typeof typeMap];
  const strengths = parseJsonParam<string[]>(strengthTopics, []);
  const needs = parseJsonParam<string[]>(needTopics, []);
  const scores = parseJsonParam<Scores>(scoresParam, {});
  const focus = getPrimaryFocus(scores);
  const retryReset = Array.isArray(reset) ? reset[0] : reset;
  const goalText = Array.isArray(goal) ? goal[0] : goal;
  const summaryText = Array.isArray(summary) ? summary[0] : summary;

  useEffect(() => {
    getDisplayNickname().then(setNickname);
  }, []);

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.hero}>
        <Text style={styles.eyebrow}>진단 결과</Text>
        <View style={styles.typeRow}>
          <Text style={styles.typeName}>{typeInfo?.name ?? '현재 회복 유형'}</Text>
          {recoveryType ? <Text style={styles.typeCode}>{recoveryType}</Text> : null}
        </View>
        <Text style={styles.description}>
          {typeInfo?.description ??
            '지금의 상태를 바탕으로 다음 행동을 작게 정리했어요.'}
        </Text>
      </View>

      {summaryText ? (
        <View style={styles.summaryCard}>
          <Text style={styles.cardLabel}>지금 나에게 필요한 해석</Text>
          <Text style={styles.summary}>{summaryText}</Text>
        </View>
      ) : null}

      <View style={styles.focusCard}>
        <View style={styles.focusIcon}>
          <FontAwesome name="compass" size={18} color="#2F7D55" />
        </View>
        <View style={styles.focusBody}>
          <Text style={styles.cardLabel}>가장 먼저 챙길 부분</Text>
          <Text style={styles.focusTitle}>{scoreMeta[focus].label}</Text>
          <Text style={styles.focusText}>{focusAdvice[focus]}</Text>
        </View>
      </View>

      <Text style={styles.sectionTitle}>{nickname}의 능력</Text>
      <View style={styles.tagSection}>
        {strengths.length > 0 ? (
          strengths.map((topic) => (
            <View key={topic} style={[styles.tag, styles.strengthTag]}>
              <Text style={styles.strengthTagText}>{topic}</Text>
            </View>
          ))
        ) : (
          <Text style={styles.emptyText}>대화가 쌓이면 강점이 더 또렷해져요.</Text>
        )}
      </View>

      <Text style={styles.sectionTitle}>보완하면 좋아질 부분</Text>
      <View style={styles.tagSection}>
        {needs.length > 0 ? (
          needs.map((topic) => (
            <View key={topic} style={[styles.tag, styles.needTag]}>
              <Text style={styles.needTagText}>{topic}</Text>
            </View>
          ))
        ) : (
          <Text style={styles.emptyText}>지금은 큰 보완 주제가 감지되지 않았어요.</Text>
        )}
      </View>

      <View style={styles.scoreCard}>
        <Text style={styles.cardLabel}>현재 균형</Text>
        {(Object.keys(scoreMeta) as ScoreKey[]).map((key) => {
          const value = Math.max(0, Math.min(scores[key] ?? 0, 3));

          return (
            <View key={key} style={styles.scoreRow}>
              <View style={styles.scoreHeader}>
                <Text style={styles.scoreLabel}>{scoreMeta[key].label}</Text>
                <Text style={styles.scoreValue}>{value}/3</Text>
              </View>
              <View style={styles.scoreTrack}>
                <View style={[styles.scoreFill, { width: `${(value / 3) * 100}%` }]} />
              </View>
              <Text style={styles.scoreDescription}>{scoreMeta[key].description}</Text>
            </View>
          );
        })}
      </View>

      <View style={styles.actionCard}>
        <Text style={styles.cardLabel}>오늘의 한 걸음</Text>
        <Text style={styles.actionText}>{getTodayAction(focus, needs, goalText)}</Text>
      </View>

      <TouchableOpacity
        style={styles.retryButton}
        onPress={() =>
          router.push({
            pathname: '/diagnose_chat',
            params: { reset: retryReset ?? Date.now().toString() },
          })
        }
      >
        <Text style={styles.retryButtonText}>다시 진단하기</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F7F4EF',
  },
  content: {
    padding: 24,
    paddingTop: 72,
    paddingBottom: 120,
  },
  hero: {
    marginBottom: 18,
  },
  eyebrow: {
    color: '#4D9E68',
    fontSize: 14,
    fontWeight: '800',
    marginBottom: 10,
  },
  typeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: 10,
    marginBottom: 12,
  },
  typeName: {
    color: '#2F3A33',
    fontSize: 32,
    fontWeight: '800',
    lineHeight: 40,
  },
  typeCode: {
    backgroundColor: '#E4F3E9',
    borderRadius: 999,
    color: '#2F7D55',
    fontSize: 13,
    fontWeight: '800',
    overflow: 'hidden',
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  description: {
    color: '#6A716B',
    fontSize: 16,
    lineHeight: 24,
  },
  summaryCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 8,
    padding: 18,
    marginBottom: 14,
  },
  cardLabel: {
    color: '#343C36',
    fontSize: 15,
    fontWeight: '800',
    marginBottom: 8,
  },
  summary: {
    color: '#343C36',
    fontSize: 17,
    lineHeight: 26,
    fontWeight: '600',
  },
  focusCard: {
    alignItems: 'flex-start',
    backgroundColor: '#ECF7F0',
    borderRadius: 8,
    flexDirection: 'row',
    gap: 14,
    marginBottom: 26,
    padding: 18,
  },
  focusIcon: {
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 8,
    height: 38,
    justifyContent: 'center',
    width: 38,
  },
  focusBody: {
    flex: 1,
  },
  focusTitle: {
    color: '#2F7D55',
    fontSize: 23,
    fontWeight: '800',
    marginBottom: 6,
  },
  focusText: {
    color: '#526157',
    fontSize: 15,
    lineHeight: 22,
  },
  sectionTitle: {
    color: '#343C36',
    fontSize: 18,
    fontWeight: '800',
    marginBottom: 10,
  },
  tagSection: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 22,
  },
  tag: {
    borderRadius: 999,
    paddingHorizontal: 13,
    paddingVertical: 8,
  },
  strengthTag: {
    backgroundColor: '#FFFFFF',
  },
  strengthTagText: {
    color: '#2F7D55',
    fontSize: 14,
    fontWeight: '800',
  },
  needTag: {
    backgroundColor: '#FFF3DF',
  },
  needTagText: {
    color: '#966118',
    fontSize: 14,
    fontWeight: '800',
  },
  emptyText: {
    color: '#7A827B',
    fontSize: 14,
    lineHeight: 21,
  },
  scoreCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 8,
    marginBottom: 14,
    padding: 18,
  },
  scoreRow: {
    marginTop: 14,
  },
  scoreHeader: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  scoreLabel: {
    color: '#343C36',
    fontSize: 16,
    fontWeight: '800',
  },
  scoreValue: {
    color: '#4D9E68',
    fontSize: 14,
    fontWeight: '800',
  },
  scoreTrack: {
    backgroundColor: '#EEF0EC',
    borderRadius: 999,
    height: 8,
    overflow: 'hidden',
  },
  scoreFill: {
    backgroundColor: '#6DBF87',
    borderRadius: 999,
    height: '100%',
  },
  scoreDescription: {
    color: '#7A827B',
    fontSize: 13,
    lineHeight: 19,
    marginTop: 6,
  },
  actionCard: {
    backgroundColor: '#C6E6D0',
    borderRadius: 8,
    marginBottom: 18,
    padding: 20,
  },
  actionText: {
    color: '#526157',
    fontSize: 18,
    fontWeight: '800',
    lineHeight: 27,
  },
  retryButton: {
    alignItems: 'center',
    backgroundColor: '#6DBF87',
    borderRadius: 24,
    paddingVertical: 15,
  },
  retryButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '800',
  },
});
