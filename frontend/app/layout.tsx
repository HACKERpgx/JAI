import type { Metadata } from 'next'
import { Analytics } from '@vercel/analytics/next'

export const metadata: Metadata = {
  title: 'JAI Website',
  description: 'Personal AI Assistant Website',
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
