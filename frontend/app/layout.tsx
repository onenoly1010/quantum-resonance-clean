import type { Metadata } from 'next'
import { inject } from '@vercel/analytics'

export const metadata: Metadata = {
  title: 'Quantum Resonance',
  description: 'Pi Forge Quantum Genesis - Quantum Resonance Application',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  inject()
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body>
        {children}
      </body>
    </html>
  )
}
