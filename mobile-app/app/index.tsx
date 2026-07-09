import AsyncStorage from '@react-native-async-storage/async-storage';
import { useRouter } from 'expo-router';
import { useEffect } from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';

export default function Index() {
  const router = useRouter();

  useEffect(() => {
    const checkAppStart = async () => {
      const accessToken = await AsyncStorage.getItem('access_token');

      if (!accessToken) {
        router.replace('/login');
        return;
      }

      const hasOnboarded = await AsyncStorage.getItem('hasOnboarded');

      if (hasOnboarded === 'true') {
        router.replace('/(tabs)/home');
      } else {
        router.replace('/(tabs)/diagnose_chat');
      }
    };

    checkAppStart();
  }, []);

  return (
    <View style={styles.container}>
      <Text style={styles.logo}>RE:Bloom 🌱</Text>
      <ActivityIndicator size="large" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F7F4EF',
    alignItems: 'center',
    justifyContent: 'center',
  },
  logo: {
    fontSize: 30,
    fontWeight: 'bold',
    color: '#3D3D3D',
    marginBottom: 20,
  },
});