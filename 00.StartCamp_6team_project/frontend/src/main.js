import { createPinia } from 'pinia'
import { createApp } from 'vue'
import App from './App.vue'
import { router } from './router'
import { reveal } from './directives/reveal'
import './style.css'

createApp(App).directive('reveal', reveal).use(createPinia()).use(router).mount('#app')
