import { createApp } from 'vue'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'
import App from './App.vue'

const vuetify = createVuetify({
  components,
  directives,
  icons: {
    defaultSet: 'mdi',
  },
  theme: {
    defaultTheme: 'sprinklerLight',
    themes: {
      sprinklerLight: {
        dark: false,
        colors: {
          primary: '#2E7D32',
          secondary: '#66BB6A',
          accent: '#29B6F6',
          success: '#A5D6A7',
          warning: '#FFA726',
          error: '#EF5350',
          background: '#F1F8E9',
          surface: '#FFFFFF',
          'on-primary': '#FAFAFA',
          'on-secondary': '#FAFAFA',
        },
      },
    },
  },
})

createApp(App).use(vuetify).mount('#app')
