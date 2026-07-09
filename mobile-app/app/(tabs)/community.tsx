import { router, type Href } from 'expo-router';
import { View, Button } from 'react-native';

export default function Community() {
  return (
    <View style={{ flex: 1, padding: 20 }}>
      <Button
        title="내 유형 채팅방 입장"
        onPress={() => router.push('/chat_room' as Href)}
      />
    </View>
  );
}
