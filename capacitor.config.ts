import type { CapacitorConfig } from '@capacitor/cli'

const config: CapacitorConfig = {
  appId: 'com.sj0404.noirdet',
  appName: 'Noir-Det',
  webDir: 'dist',
  android: {
    allowMixedContent: false,
    backgroundColor: '#05070c',
  },
}

export default config
