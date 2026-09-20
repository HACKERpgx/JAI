import type { Metadata } from 'next'
import { Analytics } from '@vercel/analytics/next'

const title = 'JAI Assistant — Advanced AI Assistant Platform'
const description =
  'JAI is an advanced AI assistant platform with voice and chat control, vision analysis, email and calendar automation, reminders, media control and autonomous task execution — all from one interface.'

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
