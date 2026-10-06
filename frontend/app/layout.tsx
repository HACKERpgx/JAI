import type { Metadata } from 'next'
import { Analytics } from '@vercel/analytics/next'

const title = 'JAI — Personal AI Assistant for Chat, Voice & Image Analysis'
const description =
  'Chat with JAI, use voice input, and analyze images. Explore optional third-party tools for file conversion, image generation, satellite tracking, and interactive demos.'

export const metadata: Metadata = {
  metadataBase: new URL('https://j-ai.top'),
  title,
  description,
  keywords: ['JAI', 'AI assistant', 'voice assistant', 'AI chat', 'automation', 'productivity'],
  alternates: { canonical: '/' },
  openGraph: {
    type: 'website',
    siteName: 'JAI',
    url: '/',
    title,
    description,
    locale: 'en_US',
    images: [{ url: '/static/icon-512.png', width: 512, height: 512, alt: 'JAI Assistant logo' }],
  },
  twitter: {
    card: 'summary_large_image',
    title,
    description,
    images: ['/static/icon-512.png'],
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        {children}
        <Analytics />
      </body>
    </html>
  )
}
