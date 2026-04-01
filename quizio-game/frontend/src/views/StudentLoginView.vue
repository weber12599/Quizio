<template>
    <div class="card" style="max-width: 500px">
        <h2>加入遊戲房間</h2>

        <div class="form-group">
            <label>房間代碼 (PIN):</label>
            <input
                v-model="roomPin"
                type="text"
                placeholder="例如: 1234"
                @keyup.enter="joinRoom"
            />
        </div>

        <div class="form-group">
            <label>學號 (Student ID):</label>
            <input
                v-model="studentId"
                type="text"
                placeholder="例如: 112001"
                @keyup.enter="joinRoom"
            />
        </div>

        <div class="form-group">
            <label>專屬密碼:</label>
            <input
                v-model="password"
                type="password"
                placeholder="輸入 4 位數密碼"
                @keyup.enter="joinRoom"
            />
        </div>

        <button @click="joinRoom" :disabled="!isFormValid" class="btn-primary">
            進入房間
        </button>
    </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

const roomPin = ref<string>('')
const studentId = ref<string>('')
const password = ref<string>('')

onMounted(() => {
    // Read pin from URL query if available
    if (route.query.pin) {
        roomPin.value = route.query.pin as string
    }
})

const isFormValid = computed(
    () =>
        roomPin.value.trim() !== '' &&
        studentId.value.trim() !== '' &&
        password.value.trim() !== ''
)

const joinRoom = () => {
    if (!isFormValid.value) return

    // Navigate to the room route with the new parameters
    router.push({
        name: 'room',
        params: {
            pin: roomPin.value.trim(),
            student_id: studentId.value.trim(),
            pwd: password.value.trim()
        }
    })
}
</script>

<style scoped>
.form-group {
    margin-bottom: 20px;
}
.form-group label {
    display: block;
    margin-bottom: 8px;
    font-weight: bold;
    color: #34495e;
}
.form-group input {
    width: 100%;
    padding: 12px;
    border: 2px solid #bdc3c7;
    border-radius: 8px;
    font-size: 16px;
    box-sizing: border-box;
}
</style>
