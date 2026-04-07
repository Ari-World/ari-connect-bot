import { defineConfig } from 'vitepress'

export default defineConfig({
  title: 'Ari Connect',
  description: 'Cross-Server Discord Bot with Web Integration — Connect communities safely, run events, and grow engagement across servers.',
  head: [
    ['link', { rel: 'icon', type: 'image/png', sizes: '192x192', href: '/android-chrome-192x192.png' }],
    ['link', { rel: 'icon', type: 'image/png', sizes: '512x512', href: '/android-chrome-512x512.png' }],
    ['link', { rel: 'apple-touch-icon', href: '/android-chrome-192x192.png' }],
    ['meta', { name: 'theme-color', content: '#5865F2' }],
    ['meta', { property: 'og:type', content: 'website' }],
    ['meta', { property: 'og:title', content: 'Ari Connect — Cross-Server Discord Bot' }],
    ['meta', { property: 'og:description', content: 'Bridge Discord communities safely. Cross-server chat, events, moderation, and a web portal — all in one.' }],
    ['meta', { property: 'og:image', content: '/android-chrome-512x512.png' }],
  ],
  themeConfig: {
    logo: '/android-chrome-192x192.png',
    nav: [
      { text: 'Home', link: '/' },
      { text: 'Features', link: '/#features' },
      { text: 'Pricing', link: '/#pricing' },
      { text: 'Docs', link: '/docs/tos' },
    ],
    sidebar: {
      '/docs/': [
        {
          text: 'Legal',
          items: [
            { text: 'Terms of Service', link: '/docs/tos' },
          ],
        },
      ],
    },
    socialLinks: [
      { icon: 'github', link: 'https://github.com/Ari-World/ari-connect-bot' },
      { icon: 'discord', link: '#' },
    ],
    footer: {
      message: 'Built to connect communities, safely and responsibly. <a href="/docs/tos">Terms of Service</a>',
      copyright: 'Copyright © 2024 Ari Connect. Discord TOS Compliant.',
    },
  },
})
