import { createRouter, createWebHistory } from 'vue-router';
import HomeView from '../views/HomeView.vue';
import HostView from '../views/HostView.vue';
import StudentLoginView from '../views/StudentLoginView.vue';
import StudentRoomView from '../views/StudentRoomView.vue';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'root', redirect: 'join' },
    { path: '/home', name: 'home', component: HomeView },
    { path: '/host', name: 'host', component: HostView },
    { path: '/join', name: 'join', component: StudentLoginView },
    {
      path: '/room/:pin/:student_id/:pwd',
      name: 'room',
      component: StudentRoomView
    }
  ]
});

export default router;
