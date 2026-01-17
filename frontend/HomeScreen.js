import React, { useState, useEffect } from 'react';
import { View, Text, Button, Image, ScrollView, StyleSheet, ActivityIndicator } from 'react-native';
import * as ImagePicker from 'expo-image-picker';

export default function HomeScreen() {
  const [imageUri, setImageUri] = useState(null);
  const [resultText, setResultText] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
  (async () => {
    const { status } = await ImagePicker.requestCameraPermissionsAsync();

    if (status !== 'granted') {
      alert('Camera permission is required to take photos');
    }
  })();
  }, []);

  const pickImage = async (fromCamera) => {
    const opts = { mediaTypes: 'Images', quality: 1, base64: true };
    const res = fromCamera
      ? await ImagePicker.launchCameraAsync(opts)
      : await ImagePicker.launchImageLibraryAsync(opts);

    if (res.canceled) return;

    const { uri, base64 } = res.assets[0];
    setImageUri(uri);
    runOCR(base64, uri.split('/').pop());
  };

  const runOCR = async (imageUri) => {
    try {
      setLoading(true);

      const form = new FormData();
      form.append('file', {
        uri: imageUri,
        name: 'receipt.jpg',
        type: 'image/jpeg',
      });

      const resp = await fetch('<YOUR_IP_HERE>:8000/parse_receipt/', {
        method: 'POST',
        body: form,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const json = await resp.json();
      console.log('OCR Result:', json);

      if (!json) {
        console.warn('OCR returned empty text');
      }

      setResultText(JSON.stringify(json, null, 2));
    } catch (e) {
      console.error('OCR error:', e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Grocery Price Tracker</Text>

      <View style={styles.buttonRow}>
        <Button title="Pick Receipt" onPress={() => pickImage(false)} />
        <Button title="Take Photo" onPress={() => pickImage(true)} />
      </View>

      {imageUri && <Image source={{ uri: imageUri }} style={styles.image} />}

      {loading && <ActivityIndicator size="large" color="green" />}

      {!!resultText && (
        <View style={styles.results}>
          <Text style={styles.resultLabel}>OCR Result:</Text>
          <Text style={styles.resultText}>{resultText}</Text>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: 20, alignItems: 'center' },
  title: { fontSize: 22, fontWeight: '700', marginTop: 60, marginBottom: 20 },
  buttonRow: { flexDirection: 'row', marginBottom: 20, gap: 10 },
  image: { width: 300, height: 300, marginBottom: 20 },
  results: { width: '100%', marginTop: 10 },
  resultLabel: { fontSize: 18, fontWeight: '600', marginBottom: 5 },
  resultText: { fontSize: 16 },
});