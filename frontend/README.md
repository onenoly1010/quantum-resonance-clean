# Quantum Resonance Frontend

Modern frontend application for Quantum Resonance - Pi Forge Quantum Genesis.

## Overview

This is a Next.js application that provides the user interface for the Quantum Resonance system. It includes integrated Vercel Web Analytics for monitoring application performance and user behavior.

## Technologies

- **Next.js 14**: React framework for production
- **TypeScript**: Type-safe development
- **Vercel Web Analytics**: Performance monitoring and analytics
- **TailwindCSS**: Utility-first CSS (optional, can be added)

## Setup

### Prerequisites

- Node.js 18+ or pnpm/yarn/bun
- npm, yarn, pnpm, or bun package manager

### Installation

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install
# or
pnpm install
# or
yarn install
# or
bun install
```

### Development

```bash
npm run dev
# or
pnpm dev
# or
yarn dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) to view the application.

### Build

```bash
npm run build
# or
pnpm build
```

### Production

```bash
npm run start
# or
pnpm start
```

## Vercel Web Analytics

This application includes Vercel Web Analytics integration via the `@vercel/analytics` package. 

### How it Works

- Analytics are automatically injected in the root layout (`app/layout.tsx`)
- The `inject()` function from `@vercel/analytics` runs on the client side
- No additional configuration required - analytics data is automatically sent to Vercel

### Integration Details

The analytics are integrated in the root layout component:

```tsx
import { inject } from '@vercel/analytics'

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  inject()
  return (
    <html lang="en">
      {/* ... */}
    </html>
  )
}
```

### Viewing Analytics

Analytics data is available in your Vercel dashboard at:
- https://vercel.com/dashboard (for your project)

### Documentation

For more information on Vercel Web Analytics, see:
- [Vercel Web Analytics Documentation](https://vercel.com/docs/analytics)

## Development

### Linting

```bash
npm run lint
# or
pnpm lint
```

### Linting with Auto-fix

```bash
npm run lint:fix
# or
pnpm lint:fix
```

## Project Structure

```
frontend/
├── app/
│   ├── layout.tsx        # Root layout with analytics injection
│   └── page.tsx          # Home page
├── package.json          # Project dependencies
├── next.config.js        # Next.js configuration
├── tsconfig.json         # TypeScript configuration
└── .eslintrc.json        # ESLint configuration
```

## Environment Variables

Create a `.env.local` file in the frontend directory if needed:

```env
# Add any environment variables here
# They will be available in the application at runtime
```

## Deployment

This application is ready to be deployed to Vercel:

1. Push your changes to GitHub
2. Connect your repository to Vercel
3. Deploy automatically on push

For other deployment options, see the [Next.js deployment documentation](https://nextjs.org/docs/deployment).

## License

See the main repository LICENSE file.
