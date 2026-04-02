import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import HostView from '../views/HostView.vue'
import StudentLoginView from '../views/StudentLoginView.vue'
import StudentRoomView from '../views/StudentRoomView.vue'
import ScreenView from '../views/ScreenView.vue'

const router = createRouter({
    history: createWebHistory(),
    routes: [
        { path: '/', name: 'root', redirect: 'join' },
        { path: '/home', name: 'home', component: HomeView },
        { path: '/host', name: 'host', component: HostView },
        { path: '/screen', name: 'screen', component: ScreenView },
        { path: '/join', name: 'join', component: StudentLoginView },
        {
            path: '/room/:pin/:student_id/:pwd',
            name: 'room',
            component: StudentRoomView
        }
    ]
})

export default router
