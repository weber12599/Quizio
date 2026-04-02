<template>
    <div class="login-view">
        <h1>Join a Game</h1>

        <div class="form-card">
            <div class="form-group">
                <label>Room PIN: </label>
                <input v-model="roomPin" placeholder="Enter Game PIN" />
            </div>
            <div class="form-group">
                <label>Student ID: </label>
                <input v-model="studentId" placeholder="e.g., 112001" />
            </div>
            <div class="form-group">
                <label>Password: </label>
                <input
                    v-model="password"
                    type="password"
                    placeholder="Enter your password"
                />
            </div>

            <button @click="joinGame" class="join-btn">Enter</button>
            <p v-if="errorMessage" class="error-msg">{{ errorMessage }}</p>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const roomPin = ref('')
const studentId = ref('')
const password = ref('')
const errorMessage = ref('')

// Validate inputs and navigate to the room view
const joinGame = () => {
    if (!roomPin.value || !studentId.value || !password.value) {
        errorMessage.value = 'Please fill in all fields.'
        return
    }

    // Navigate to StudentRoomView with parameters
    router.push({
        name: 'room',
        params: {
            pin: roomPin.value,
            student_id: studentId.value,
            pwd: password.value
        }
    })
}
</script>

<style scoped>
.login-view {
    display: flex;
    flex-direction: column;
    align-items: center;
    margin-top: 50px;
}
.form-card {
    padding: 20px;
    border: 1px solid #ccc;
    border-radius: 8px;
    width: 300px;
}
.form-group {
    margin-bottom: 15px;
    display: flex;
    flex-direction: column;
}
.form-group label {
    font-weight: bold;
    margin-bottom: 5px;
}
.join-btn {
    width: 100%;
    padding: 10px;
    background-color: #4caf50;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 16px;
}
.join-btn:hover {
    background-color: #45a049;
}
.error-msg {
    color: red;
    margin-top: 10px;
    text-align: center;
}
</style>
