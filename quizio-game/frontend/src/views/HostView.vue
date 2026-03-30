<template>
  <div class="card host-card">
    <div class="room-header">
      <h2>
        房間代碼: <span class="highlight">{{ roomPin }}</span>
      </h2>
      <span class="status-badge connected">等待學生加入中...</span>
    </div>

    <div class="join-info">
      <div class="qr-section">
        <p>用平板掃描加入</p>
        <qrcode-vue v-if="joinUrl" :value="joinUrl" :size="200" level="H" />
      </div>

      <div class="url-section">
        <p>或使用筆電輸入網址：</p>
        <div class="short-url">{{ joinUrl }}</div>
      </div>
    </div>

    <div class="players-section">
      <h3>目前已加入的學生 ({{ players.length }} 人)</h3>
      <ul class="players-list">
        <li v-for="player in players" :key="player">
          <span class="avatar">👦🏻</span> {{ player }}
        </li>
      </ul>
    </div>

    <button @click="leaveRoom" class="btn-danger">關閉房間</button>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import QrcodeVue from 'qrcode.vue';

const router = useRouter();
const roomPin = ref<string>('');
const players = ref<string[]>([]);
const joinUrl = ref<string>('');
const shortUrl = ref<string>('');
let ws: WebSocket | null = null;

onMounted(async () => {
  // Generate random 4-digit PIN
  roomPin.value = Math.floor(1000 + Math.random() * 9000).toString();

  const protocol = window.location.protocol;
  const host = window.location.host;

  // Point the QR code to the student login page with the PIN in the query string
  const fullJoinUrl = `${protocol}//${host}/join?pin=${roomPin.value}`;
  joinUrl.value = fullJoinUrl;

  // Connect to WebSocket as Host
  const wsProtocol = protocol === 'https:' ? 'wss:' : 'ws:';
  ws = new WebSocket(
    `${wsProtocol}//${host}/ws/${roomPin.value}/Host_Teacher/Host_Teacher`
  );

  ws.onmessage = (event) => {
    try {
      const message = JSON.parse(event.data);
      if (message.type === 'room_state') {
        // Filter out the host from the display list
        players.value = message.data.players.filter(
          (p: string) => p !== 'Host_Teacher'
        );
      }
    } catch (e) {
      console.error('Parse error', e);
    }
  };
});

const leaveRoom = () => {
  if (ws) ws.close();
  router.push('/');
};

onUnmounted(() => {
  if (ws) ws.close();
});
</script>

<style scoped>
.host-card {
  max-width: 800px;
}
.room-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 2px solid #ecf0f1;
  padding-bottom: 15px;
  margin-bottom: 20px;
}
.room-header h2 {
  margin: 0;
  color: #2c3e50;
}
.highlight {
  color: #3498db;
  font-size: 1.2em;
}
.status-badge {
  padding: 5px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: bold;
  background-color: #2ecc71;
  color: white;
}
.join-info {
  display: flex;
  align-items: center;
  justify-content: space-around;
  background: #f8f9fa;
  padding: 20px;
  border-radius: 12px;
  margin-bottom: 30px;
}
.qr-section p,
.url-section p {
  font-weight: bold;
  color: #34495e;
  margin-bottom: 15px;
  text-align: center;
}
.short-url {
  font-size: 24px;
  font-weight: bold;
  color: #e74c3c;
  background: #fff;
  padding: 10px 20px;
  border-radius: 8px;
  border: 2px dashed #e74c3c;
  letter-spacing: 1px;
}
.players-list {
  list-style-type: none;
  padding: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
.players-list li {
  padding: 10px 15px;
  background-color: #e8f4f8;
  border: 1px solid #3498db;
  border-radius: 20px;
  display: flex;
  align-items: center;
  font-size: 16px;
  font-weight: bold;
}
.avatar {
  margin-right: 8px;
}
</style>
