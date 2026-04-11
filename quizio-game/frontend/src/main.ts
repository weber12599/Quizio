import { createApp } from 'vue'
import router from './router'

import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import 'element-plus/theme-chalk/dark/css-vars.css'
import './assets/main.css'
import App from './App.vue'
import i18n from './i18n'

const app = createApp(App)

app.use(i18n)
app.use(router)
app.use(ElementPlus)

for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component)
}

app.mount('#app')
