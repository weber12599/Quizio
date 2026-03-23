<template>
  <div class="container">
    <h1>Quizio App Connection</h1>
    
    <div>
      Status: 
      <span :class="statusClass">{{ connectionStatus }}</span>
    </div>

    <div v-if="clientId" class="info-box">
      <p><strong>Client ID:</strong> {{ clientId }}</p>
      <p><strong>WebSocket URL:</strong> {{ wsUrl }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';

// Define reactive state variables with explicit types
const connectionStatus = ref<string>('Connecting...');
const clientId = ref<number | null>(null);
const wsUrl = ref<string>('');
let ws: WebSocket | null = null;

// Compute CSS class based on status
const statusClass = computed(() => {
  if (connectionStatus.value === 'Connected') return 'status-connected';
  if (connectionStatus.value === 'Disconnected' || connectionStatus.value === 'Error') return 'status-disconnected';
  return 'status-connecting';
});

onMounted(() => {
  // Generate random client ID
  clientId.value = Math.floor(Math.random() * 10000);
  
  // Determine protocol based on current page URL
  const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const host = window.location.host;
  
  // Construct the full WebSocket URL
  // Vite proxy will intercept this and forward to the backend container
  wsUrl.value = `${wsProtocol}//${host}/ws/${clientId.value}`;
  
  // Initialize WebSocket connection
  ws = new WebSocket(wsUrl.value);

  ws.onopen = () => {
    connectionStatus.value = 'Connected';
  };

  ws.onclose = () => {
    connectionStatus.value = 'Disconnected';
  };

  ws.onerror = (error: Event) => {
    console.error("WebSocket encountered an error:", error);
    connectionStatus.value = 'Error';
  };
});

onUnmounted(() => {
  // Clean up connection
  if (ws) {
    ws.close();
  }
});
</script>

<style scoped>
.container {
  font-family: sans-serif;
  padding: 20px;
}
.status-connected { color: green; font-weight: bold; }
.status-disconnected { color: red; font-weight: bold; }
.status-connecting { color: orange; font-weight: bold; }
.info-box {
  margin-top: 15px;
  padding: 10px;
  background: #f0f0f0;
  border-radius: 5px;
  color: #333;
}
</style>