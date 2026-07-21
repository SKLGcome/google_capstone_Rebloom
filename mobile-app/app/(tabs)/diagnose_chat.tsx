import { Audio } from 'expo-av';
import { useLocalSearchParams, useRouter } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Speech from 'expo-speech';
import { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';

import { apiFetch, runDiagnosis } from '../../lib/api';
import { getDisplayNickname } from '../../lib/user';

type Message = {
  id: string;
  role: 'ai' | 'assistant' | 'user';
  content: string;
};

const initialMessages: Message[] = [
  {
    id: 'ai-0',
    role: 'ai',
    content: '최근 하루를 어떻게 보내고 있나요?',
  },
];

const VOICE_RECORDING_OPTIONS: Audio.RecordingOptions = {
  isMeteringEnabled: false,
  android: {
    extension: '.m4a',
    outputFormat: Audio.AndroidOutputFormat.MPEG_4,
    audioEncoder: Audio.AndroidAudioEncoder.AAC,
    sampleRate: 16000,
    numberOfChannels: 1,
    bitRate: 64000,
  },
  ios: {
    extension: '.m4a',
    outputFormat: Audio.IOSOutputFormat.MPEG4AAC,
    audioQuality: Audio.IOSAudioQuality.MEDIUM,
    sampleRate: 16000,
    numberOfChannels: 1,
    bitRate: 64000,
  },
  web: {
    mimeType: 'audio/webm',
    bitsPerSecond: 64000,
  },
};

export default function Diagnose() {
  const router = useRouter();
  const { reset } = useLocalSearchParams();

  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [loading, setLoading] = useState(false);
  const [diagnosing, setDiagnosing] = useState(false);
  const [recording, setRecording] = useState<Audio.Recording | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [nickname, setNickname] = useState('나');

  useEffect(() => {
    setMessages(initialMessages);
    setLoading(false);
    setDiagnosing(false);
    setRecording(null);
    setIsRecording(false);
  }, [reset]);

  useEffect(() => {
    getDisplayNickname().then(setNickname);
  }, []);

  const normalizeMessages = (rawMessages: any[]): Message[] => {
    return rawMessages.map((message, index) => ({
      id: message.id ?? `${message.role}-${Date.now()}-${index}`,
      role: message.role === 'assistant' ? 'ai' : message.role,
      content: message.content,
    }));
  };

  const goResultIfReady = async (messages: Message[]) => {
    const result = await runDiagnosis(messages);
    await AsyncStorage.setItem('hasOnboarded', 'true');

    router.replace({
      pathname: '/(tabs)/result',
      params: {
        type: result.recovery_type,
        summary: result.summary,
        strengthTopics: JSON.stringify(result.strength_topics ?? []),
        needTopics: JSON.stringify(result.need_topics ?? []),
        goal: result.goal,
        scores: JSON.stringify(result.scores ?? {}),
        reset: Date.now().toString(),
      },
    });
  };

  const startRecording = async () => {
    try {
      const permission = await Audio.requestPermissionsAsync();
      if (!permission.granted) {
        Alert.alert('권한 필요', '음성 녹음을 위해 마이크 권한이 필요합니다.');
        return;
      }

      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
      });

      const { recording } = await Audio.Recording.createAsync(
        VOICE_RECORDING_OPTIONS
      );

      setRecording(recording);
      setIsRecording(true);
    } catch (error) {
      console.error(error);
      Alert.alert('오류', '녹음을 시작하지 못했습니다.');
    }
  };

  const stopRecording = async () => {
    try {
      if (!recording) return;

      setIsRecording(false);
      await recording.stopAndUnloadAsync();
      const uri = recording.getURI();
      setRecording(null);

      if (!uri) {
        Alert.alert('오류', '녹음 파일을 찾지 못했습니다.');
        return;
      }

      await sendVoiceMessage(uri);
    } catch (error) {
      console.error(error);
      Alert.alert('오류', '녹음을 종료하지 못했습니다.');
    }
  };

  const sendVoiceMessage = async (uri: string) => {
    try {
      setDiagnosing(false);
      setLoading(true);

      const formData = new FormData();
      formData.append('file', {
        uri,
        name: Platform.OS === 'web' ? 'voice.webm' : 'voice.m4a',
        type: Platform.OS === 'web' ? 'audio/webm' : 'audio/mp4',
      } as any);

      const transcriptionResponse = await apiFetch('/chat/transcribe', {
        method: 'POST',
        body: formData,
      });
      const transcriptionData = await transcriptionResponse.json();

      if (!transcriptionResponse.ok) {
        throw new Error(transcriptionData.detail || '음성 변환 실패');
      }

      const userMessage: Message = {
        id: `user-${Date.now()}`,
        role: 'user',
        content: transcriptionData.user_text,
      };
      const messagesWithUser = [...messages, userMessage];
      setMessages(messagesWithUser);

      const responseFormData = new FormData();
      responseFormData.append('messages', JSON.stringify(messagesWithUser));
      const response = await apiFetch('/chat/respond', {
        method: 'POST',
        body: responseFormData,
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || '대화 응답 생성 실패');
      }

      const normalizedMessages = normalizeMessages(data.messages);
      setMessages(normalizedMessages);

      Speech.speak(data.assistant_text, {
        language: 'ko-KR',
        rate: 0.95,
      });

      if (data.is_diagnosis_ready) {
        await new Promise((resolve) => setTimeout(resolve, 1000));

        setDiagnosing(true);

        await goResultIfReady(normalizedMessages);
        return;
      }
    } catch (error) {
      console.error(error);
      Alert.alert('오류', '음성 메시지 처리에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const renderItem = ({ item }: { item: Message }) => {
    const isUser = item.role === 'user';

    return (
      <View
        style={[
          styles.messageBubble,
          isUser ? styles.userBubble : styles.aiBubble,
        ]}
      >
        <Text style={isUser ? styles.userText : styles.aiText}>
          {item.content}
        </Text>
      </View>
    );
  };

  if (diagnosing) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#6DBF87" />
        <Text style={styles.loadingTitle}>분석 중입니다</Text>
        <Text style={styles.loadingText}>
          상담 내용을 바탕으로 회복 유형을 진단하고 있어요.
        </Text>
      </View>
    );
  }

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <Text style={styles.title}>처음 만나는 회복 진단</Text>

      <Text style={styles.subtitle}>
        AI와 대화하며 현재 {nickname}의 에너지, 방향성, 실행력을 확인해볼게요.
      </Text>

      <FlatList
        data={messages}
        keyExtractor={(item) => item.id}
        renderItem={renderItem}
        contentContainerStyle={styles.messageList}
      />

      <TouchableOpacity
        style={[
          styles.voiceButton,
          isRecording && styles.voiceButtonRecording,
        ]}
        onPress={isRecording ? stopRecording : startRecording}
        disabled={loading}
      >
        {loading ? (
          <ActivityIndicator color="#FFFFFF" />
        ) : (
          <Text style={styles.voiceButtonText}>
            {isRecording ? '녹음 종료' : '음성으로 말하기'}
          </Text>
        )}
      </TouchableOpacity>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F7F4EF',
    padding: 24,
  },
  loadingContainer: {
    flex: 1,
    backgroundColor: '#F7F4EF',
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 24,
  },
  loadingTitle: {
    marginTop: 16,
    fontSize: 20,
    fontWeight: '700',
    color: '#3D3D3D',
  },
  loadingText: {
    marginTop: 8,
    fontSize: 15,
    color: '#777',
    textAlign: 'center',
    lineHeight: 22,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#3D3D3D',
    marginBottom: 12,
    marginTop: 20,
  },
  subtitle: {
    fontSize: 16,
    color: '#777',
    lineHeight: 24,
    marginBottom: 20,
  },
  messageList: {
    flexGrow: 1,
    paddingBottom: 20,
  },
  messageBubble: {
    maxWidth: '82%',
    padding: 14,
    borderRadius: 18,
    marginBottom: 10,
  },
  aiBubble: {
    alignSelf: 'flex-start',
    backgroundColor: '#FFFFFF',
  },
  userBubble: {
    alignSelf: 'flex-end',
    backgroundColor: '#6DBF87',
  },
  aiText: {
    fontSize: 15,
    color: '#333',
    lineHeight: 22,
  },
  userText: {
    fontSize: 15,
    color: '#FFFFFF',
    lineHeight: 22,
  },
  voiceButton: {
    backgroundColor: '#6BAA75',
    paddingVertical: 14,
    paddingHorizontal: 18,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 10,
  },
  voiceButtonRecording: {
    backgroundColor: '#E74C3C',
  },
  voiceButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});
