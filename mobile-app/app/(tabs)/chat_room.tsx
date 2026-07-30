import {
  DailyMission,
  getLatestDiagnosis,
  getRoomDailyMission,
  getRoomMessages,
  sendRoomMessage,
} from '@/lib/api';
import { useFocusEffect } from 'expo-router';
import { useCallback, useRef, useState } from 'react';
import {
  Alert,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';

const ROOM_STALE_TIME_MS = 60_000;

export default function ChatRoom() {
  const [roomId, setRoomId] = useState<string | null>(null);
  const [messages, setMessages] = useState<any[]>([]);
  const [mission, setMission] = useState<DailyMission | null>(null);
  const [isMissionLoading, setIsMissionLoading] = useState(true);
  const [input, setInput] = useState('');
  const lastLoadedAt = useRef(0);
  const isLoading = useRef(false);

  const loadRoom = useCallback(async () => {
    if (isLoading.current) return;

    isLoading.current = true;
    try {
      const diagnosis = await getLatestDiagnosis();
      const type = diagnosis.type;
      const nextRoomId = `type_${type}`;

      setRoomId(nextRoomId);

      const [messageResult, missionResult] = await Promise.allSettled([
        getRoomMessages(nextRoomId),
        getRoomDailyMission(nextRoomId),
      ]);

      if (messageResult.status === 'rejected') {
        throw messageResult.reason;
      }

      setMessages(messageResult.value);
      lastLoadedAt.current = Date.now();

      if (missionResult.status === 'fulfilled') {
        setMission(missionResult.value);
      } else {
        console.warn('오늘의 미션을 불러오지 못했습니다.', missionResult.reason);
        setMission(null);
      }
    } catch (error) {
      console.error(error);
      Alert.alert(
        '오류',
        error instanceof Error ? error.message : '채팅방을 불러오지 못했습니다.'
      );
    } finally {
      isLoading.current = false;
      setIsMissionLoading(false);
    }
  }, []);

  const handleSend = async () => {
    if (!input.trim() || !roomId) return;

    try {
      const newMessage = await sendRoomMessage(roomId, input);
      setMessages((prev) => [...prev, newMessage]);
      setInput('');
    } catch (error) {
      console.error(error);
      Alert.alert(
        '오류',
        error instanceof Error ? error.message : '메시지를 보내지 못했습니다.'
      );
    }
  };

  useFocusEffect(
    useCallback(() => {
      if (Date.now() - lastLoadedAt.current >= ROOM_STALE_TIME_MS) {
        void loadRoom();
      }
    }, [loadRoom])
  );

  if (!roomId) {
    return (
      <View style={styles.loadingContainer}>
        <Text style={styles.loadingText}>채팅방을 불러오는 중...</Text>
      </View>
    );
  }

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <View style={styles.header}>
        <Text style={styles.headerLabel}>내 유형 커뮤니티</Text>
        <Text style={styles.headerTitle}>{roomId} 채팅방</Text>
        <Text style={styles.headerSubtext}>
          같은 회복 유형의 사람들과 가볍게 이야기를 나눠보세요.
        </Text>
      </View>

      <View style={styles.missionCard}>
        <View style={styles.missionBadge}>
          <Text style={styles.missionBadgeIcon}>🌱</Text>
          <Text style={styles.missionBadgeText}>오늘의 우리 미션</Text>
        </View>

        {isMissionLoading ? (
          <Text style={styles.missionStatus}>오늘의 미션을 준비하고 있어요...</Text>
        ) : mission ? (
          <>
            <Text style={styles.missionTitle}>{mission.mission_name}</Text>
            <Text style={styles.missionContent}>{mission.mission_content}</Text>
            <Text style={styles.missionHint}>
              부담 갖지 말고, 가능한 만큼만 함께 해봐요.
            </Text>
          </>
        ) : (
          <>
            <Text style={styles.missionEmptyTitle}>오늘의 미션을 준비 중이에요</Text>
            <Text style={styles.missionStatus}>
              잠시 후 다시 들어오면 새로운 미션을 확인할 수 있어요.
            </Text>
          </>
        )}
      </View>

      <ScrollView
        style={styles.messageArea}
        contentContainerStyle={styles.messageList}
        showsVerticalScrollIndicator={false}
      >
        {messages.length > 0 ? (
          messages.map((msg) => (
            <View key={msg.id} style={styles.messageBubble}>
              <Text style={styles.messageAuthor}>{msg.nickname}</Text>
              <Text style={styles.messageText}>{msg.content}</Text>
            </View>
          ))
        ) : (
          <View style={styles.emptyBox}>
            <Text style={styles.emptyTitle}>아직 메시지가 없어요</Text>
            <Text style={styles.emptyText}>첫 이야기를 남겨보세요.</Text>
          </View>
        )}
      </ScrollView>

      <View style={styles.inputBar}>
        <TextInput
          value={input}
          onChangeText={setInput}
          placeholder="메시지를 입력하세요"
          placeholderTextColor="#8A938D"
          style={styles.input}
          multiline
        />

        <TouchableOpacity
          style={[styles.sendButton, !input.trim() && styles.sendButtonDisabled]}
          onPress={handleSend}
          disabled={!input.trim()}
        >
          <Text style={styles.sendButtonText}>전송</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F7F4EF',
    padding: 20,
    paddingTop: 56,
  },
  loadingContainer: {
    alignItems: 'center',
    backgroundColor: '#F7F4EF',
    flex: 1,
    justifyContent: 'center',
    padding: 20,
  },
  loadingText: {
    color: '#526157',
    fontSize: 16,
    fontWeight: '700',
  },
  header: {
    alignItems: 'center',
    backgroundColor: '#C6E6D0',
    borderRadius: 12,
    marginBottom: 12,
    paddingHorizontal: 18,
    paddingVertical: 18,
  },
  headerLabel: {
    color: '#2F7D55',
    fontSize: 13,
    fontWeight: '800',
    marginBottom: 6,
  },
  headerTitle: {
    color: '#2F3A33',
    fontSize: 28,
    fontWeight: '800',
    textAlign: 'center',
  },
  headerSubtext: {
    color: '#526157',
    fontSize: 14,
    lineHeight: 20,
    marginTop: 8,
    textAlign: 'center',
  },
  missionCard: {
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderColor: '#D9EDDF',
    borderRadius: 18,
    borderWidth: 1,
    elevation: 3,
    marginBottom: 16,
    paddingHorizontal: 22,
    paddingVertical: 18,
    shadowColor: '#386248',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 10,
  },
  missionBadge: {
    alignItems: 'center',
    backgroundColor: '#E8F6EC',
    borderRadius: 999,
    flexDirection: 'row',
    marginBottom: 12,
    paddingHorizontal: 12,
    paddingVertical: 7,
  },
  missionBadgeIcon: {
    fontSize: 14,
    marginRight: 6,
  },
  missionBadgeText: {
    color: '#2F7D55',
    fontSize: 12,
    fontWeight: '800',
  },
  missionTitle: {
    color: '#2F3A33',
    fontSize: 20,
    fontWeight: '800',
    lineHeight: 27,
    textAlign: 'center',
  },
  missionContent: {
    color: '#526157',
    fontSize: 14,
    lineHeight: 21,
    marginTop: 8,
    textAlign: 'center',
  },
  missionHint: {
    color: '#7A8C80',
    fontSize: 12,
    marginTop: 12,
    textAlign: 'center',
  },
  missionEmptyTitle: {
    color: '#3E4B42',
    fontSize: 16,
    fontWeight: '800',
    marginBottom: 6,
    textAlign: 'center',
  },
  missionStatus: {
    color: '#7A8C80',
    fontSize: 13,
    lineHeight: 19,
    textAlign: 'center',
  },
  messageArea: {
    flex: 1,
  },
  messageList: {
    paddingBottom: 16,
  },
  messageBubble: {
    alignSelf: 'flex-start',
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    marginBottom: 10,
    maxWidth: '88%',
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  messageAuthor: {
    color: '#6DBF87',
    fontSize: 12,
    fontWeight: '800',
    marginBottom: 5,
  },
  messageText: {
    color: '#343C36',
    fontSize: 15,
    lineHeight: 22,
  },
  emptyBox: {
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    marginTop: 20,
    padding: 24,
  },
  emptyTitle: {
    color: '#343C36',
    fontSize: 17,
    fontWeight: '800',
    marginBottom: 6,
  },
  emptyText: {
    color: '#7A827B',
    fontSize: 14,
  },
  inputBar: {
    alignItems: 'flex-end',
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    flexDirection: 'row',
    gap: 10,
    padding: 10,
  },
  input: {
    color: '#343C36',
    flex: 1,
    fontSize: 15,
    maxHeight: 96,
    minHeight: 42,
    paddingHorizontal: 4,
    paddingVertical: 10,
  },
  sendButton: {
    alignItems: 'center',
    backgroundColor: '#6DBF87',
    borderRadius: 10,
    height: 42,
    justifyContent: 'center',
    paddingHorizontal: 18,
  },
  sendButtonDisabled: {
    backgroundColor: '#B9C7BD',
  },
  sendButtonText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '800',
  },
});
