// src/router/index.ts
import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '../stores/auth';

import LoginView from '../views/LoginView.vue';
import AdminLayout from '../layouts/AdminLayout.vue';
import StudentsView from '../views/StudentsView.vue';
import QuestionsView from '../views/QuestionsView.vue';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/admin/students'
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView
    },
    {
      path: '/admin',
      component: AdminLayout,
      // Require authentication for all routes under /admin
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          redirect: '/admin/students'
        },
        {
          path: 'students',
          name: 'students',
          component: StudentsView
        },
        {
          path: 'questions',
          name: 'questions',
          component: QuestionsView
        }
      ]
    }
  ]
});

// Navigation Guard to protect admin routes
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore();

  if (to.meta.requiresAuth && !authStore.isAuthenticated()) {
    // Redirect to login if not authenticated
    next('/login');
  } else if (to.path === '/login' && authStore.isAuthenticated()) {
    // Redirect to admin if already logged in and trying to access login page
    next('/admin/students');
  } else {
    next();
  }
});

export default router;
