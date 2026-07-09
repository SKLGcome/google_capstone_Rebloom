import { getLatestDiagnosis, getRoomMessages, sendRoomMessage } from '@/lib/api';
import { useEffect, useState } from 'react';
import { Alert, Button, ScrollView, Text, TextInput, View } from 'react-native';

export default function ChatRoom() {
  const [roomId, setRoomId] = useState<string | null>(null);
  const [messages, setMessages] = useState<any[]>([]);
  const [input, setInput] = useState('');

  const loadRoom = async () => {
    try {
      const diagnosis = await getLatestDiagnosis();
      const type = diagnosis.type;
      const nextRoomId = `type_${type}`;

      setRoomId(nextRoomId);

      const data = await getRoomMessages(nextRoomId);
      setMessages(data);
    } catch (error) {
      console.error(error);
      Alert.alert(
        '오류',
        error instanceof Error ? error.message : '채팅방을 불러오지 못했습니다.'
      );
    }
  };

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

  useEffect(() => {
    loadRoom();
  }, []);

  if (!roomId) {
    return (
      <View style={{ flex: 1, padding: 20 }}>
        <Text>채팅방을 불러오는 중...</Text>
      </View>
    );
  }

  return (
    <View style={{ flex: 1, padding: 20 }}>
      <Text style={{ marginBottom: 12, fontWeight: 'bold' }}>
        {roomId} 채팅방
      </Text>

      <ScrollView style={{ flex: 1 }}>
        {messages.map((msg) => (
          <View key={msg.id} style={{ marginBottom: 12 }}>
            <Text>user {msg.user_id}</Text>
            <Text>{msg.content}</Text>
          </View>
        ))}
      </ScrollView>

      <TextInput
        value={input}
        onChangeText={setInput}
        placeholder="메시지를 입력하세요"
        style={{
          borderWidth: 1,
          padding: 12,
          borderRadius: 8,
          marginBottom: 8,
        }}
      />

      <Button title="전송" onPress={handleSend} />
    </View>
  );
}
