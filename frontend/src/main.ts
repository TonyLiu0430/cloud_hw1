import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import ElementPlus from 'element-plus'
import { router } from './router.ts'
import 'element-plus/dist/index.css'
import { createPinia } from 'pinia'

const app = createApp(App)
const pinia = createPinia()
app.use(ElementPlus)
   .use(router)
   .use(pinia)
   .mount('#app')
