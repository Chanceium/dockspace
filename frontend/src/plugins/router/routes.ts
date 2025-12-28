export const routes = [
  { path: '/', redirect: '/login' },
  {
    path: '/',
    component: () => import('@/layouts/default.vue'),
    children: [
      {
        path: 'settings',
        component: () => import('@/pages/settings.vue'),
      },
      {
        path: 'management',
        component: () => import('@/pages/management.vue'),
      },
    ],
  },
  {
    path: '/',
    component: () => import('@/layouts/blank.vue'),
    children: [
      {
        path: 'login',
        component: () => import('@/pages/login.vue'),
      },
      {
        path: 'register',
        component: () => import('@/pages/register.vue'),
      },
      {
        path: 'reset-password',
        component: () => import('@/pages/reset-password.vue'),
      },
      {
        path: 'access-denied',
        component: () => import('@/pages/access-denied.vue'),
      },
      {
        path: 'two-factor-required',
        component: () => import('@/pages/two-factor-required.vue'),
      },
      {
        path: 'two-factor-missing',
        component: () => import('@/pages/two-factor-missing.vue'),
      },
      {
        path: 'setup',
        component: () => import('@/pages/setup.vue'),
      },
      {
        path: '/:pathMatch(.*)*',
        component: () => import('@/pages/[...error].vue'),
      },
    ],
  },
]
