import { createApp } from 'vue'
import vant from 'vant'
import 'vant/lib/index.css'

import App from './App.vue'
import router from './router'

const app = createApp(App)
app.use(vant)
app.use(router)
app.mount('#app')
