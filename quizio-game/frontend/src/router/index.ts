import { createRouter, createWebHistory } from 'vue-router'
import HostView from '../views/HostView.vue'
import ClientView from '../views/ClientView.vue'
import ScreenView from '../views/ScreenView.vue'

const router = createRouter({
    history: createWebHistory(),
    routes: [
        { path: '/', name: 'root', redirect: 'client' },
        { path: '/host', name: 'host', component: HostView },
        { path: '/screen', name: 'screen', component: ScreenView },
        { path: '/client', name: 'client', component: ClientView }
    ]
})

export default router
