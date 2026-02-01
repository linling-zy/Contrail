import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import './styles/index.scss'

import Particles from "particles.vue3";

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.use(Particles)
app.mount('#app')
