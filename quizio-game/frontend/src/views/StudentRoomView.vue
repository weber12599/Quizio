<template>
  <div class="card" style="max-width: 500px">
    <div class="room-header">
      <h2>
        房間代碼: <span class="highlight">{{ pin }}</span>
      </h2>
      <span
        class="status-badge"
        :class="isConnected ? 'connected' : 'disconnected'"
      >
        {{ isConnected ? '已連線' : '連線中...' }}
      </span>
    </div>

    <div v-if="errorMsg" class="error-msg">
      <p>{{ errorMsg }}</p>
      <button
        @click="router.push('/')"
        class="btn-danger"
        style="margin-top: 15px"
      >
        重新登入
      </button>
    </div>

    <div v-else class="waiting-area">
      <h3>準備就緒，學號 {{ studentId }}！</h3>
      <p>請看大螢幕，等待老師發布題目...</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';

const route = useRoute();
const router = useRouter();

// Extract parameters from route
const pin = route.params.pin as string;
const studentId = route.params.student_id as string;
const pwd = route.params.pwd as string;

const isConnected = ref(false);
const errorMsg = ref('');
let ws: WebSocket | null = null;

onMounted(() => {
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = window.location.host;

  // Connect using student_id
  ws = new WebSocket(`${wsProtocol}//${host}/ws/${pin}/${studentId}/${pwd}`);

  ws.onopen = () => {
    isConnected.value = true;
  };

  ws.onclose = (event) => {
    isConnected.value = false;
    // Handle specific close codes from backend
    if (event.code === 1008) {
      errorMsg.value = '登入失敗：密碼錯誤，或該學號已在房間內。';
    } else {
      errorMsg.value = '已與伺服器斷開連線';
    }
  };

  ws.onerror = () => {
    errorMsg.value = 'WebSocket 連線發生錯誤';
  };
});

onUnmounted(() => {
  if (ws) ws.close();
});
</script>

<style scoped>
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
}
.connected {
  background-color: #2ecc71;
  color: white;
}
.disconnected {
  background-color: #e74c3c;
  color: white;
}
.waiting-area {
  text-align: center;
  padding: 40px 0;
}
.waiting-area h3 {
  color: #2ecc71;
  font-size: 24px;
  margin-bottom: 10px;
}
.error-msg {
  text-align: center;
  color: #e74c3c;
  font-weight: bold;
  padding: 20px 0;
}
</style>
