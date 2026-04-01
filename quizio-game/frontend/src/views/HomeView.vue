<template>
    <div class="card" style="max-width: 500px">
        <h2 style="text-align: center; margin-bottom: 20px">請選擇你的身分</h2>
        <div class="role-buttons">
            <button @click="router.push('/host')" class="btn-primary">
                👨‍🏫 我是老師 (建立房間)
            </button>
            <button @click="router.push('/join')" class="btn-secondary">
                👦🏻 我是學生 (加入房間)
            </button>
        </div>
    </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
const router = useRouter()
</script>

<style scoped>
.role-buttons {
    display: flex;
    gap: 20px;
    justify-content: center;
}
</style>
