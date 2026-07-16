import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/welcome',
    name: 'welcome',
    component: () => import('../views/WelcomeView.vue'),
    meta: { layout: 'immersive' },
  },
  { path: '/', name: 'contents', component: () => import('../views/ContentListView.vue') },
  { path: '/map', name: 'map', component: () => import('../views/MapView.vue') },
  {
    path: '/contents/:id',
    name: 'content-detail',
    component: () => import('../views/ContentDetailView.vue'),
    props: true,
  },
  {
    path: '/auth',
    name: 'auth',
    component: () => import('../views/AuthView.vue'),
  },
  {
    path: '/community',
    name: 'community',
    component: () => import('../views/CommunityListView.vue'),
  },
  {
    path: '/community/new',
    name: 'post-new',
    component: () => import('../views/PostFormView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/community/:id/edit',
    name: 'post-edit',
    component: () => import('../views/PostFormView.vue'),
    props: true,
    meta: { requiresAuth: true },
  },
  {
    path: '/community/:id',
    name: 'post-detail',
    component: () => import('../views/PostDetailView.vue'),
    props: true,
  },
  { path: '/chat', name: 'chat', component: () => import('../views/ChatView.vue') },
  { path: '/planner', name: 'planner', component: () => import('../views/PlannerView.vue') },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('../views/NotFoundView.vue'),
  },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) return savedPosition
    if (to.path !== from.path) return { top: 0 }
    return undefined
  },
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (!auth.ready) await auth.bootstrap()

  if (
    to.name === 'contents'
    && !auth.isAuthenticated
    && localStorage.getItem('smsm:onboarding:v1') !== 'seen'
    && !router.currentRoute.value.name
  ) {
    return { name: 'welcome' }
  }

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { name: 'auth', query: { mode: 'login', redirect: to.fullPath } }
  }

  if (to.name === 'auth' && auth.isAuthenticated) {
    const redirect = typeof to.query.redirect === 'string' ? to.query.redirect : '/'
    return redirect.startsWith('/') && !redirect.startsWith('//') ? redirect : '/'
  }

  return true
})
