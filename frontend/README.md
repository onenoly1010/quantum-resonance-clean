# Quantum Resonance Frontend

Frontend application for Quantum Resonance - Pi Forge Quantum Genesis project.

## Overview

This is a Next.js application with Vercel Speed Insights integrated for performance monitoring.

## Tech Stack

- **Next.js 15**: React framework for production
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first CSS framework
- **Vercel Speed Insights**: Real-time performance monitoring

## Setup

### Installation

```bash
npm install
```

### Development

Run the development server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

### Build

Build the application for production:

```bash
npm run build
```

### Production

Start the production server:

```bash
npm start
```

### Linting

Run ESLint to check code quality:

```bash
npm run lint
```

## Vercel Speed Insights

This application is configured with **Vercel Speed Insights** for real-time performance monitoring. The integration is done in `src/app/layout.tsx`:

```typescript
import { SpeedInsights } from "@vercel/speed-insights/next";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        {children}
        <SpeedInsights />
      </body>
    </html>
  );
}
```

### How It Works

- Speed Insights is injected as a client-side component in the root layout
- It automatically collects Web Vitals metrics from your users
- Data is sent to Vercel's analytics dashboard
- No additional configuration needed for Vercel deployments

## Deployment

This project is optimized for deployment on Vercel:

1. Push your code to GitHub/GitLab/Bitbucket
2. Import the project in Vercel dashboard
3. Vercel will auto-detect Next.js and configure settings
4. Deploy with a single click
5. Speed Insights data will appear in your Vercel dashboard

## Project Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx       # Root layout with Speed Insights
│   │   ├── page.tsx         # Home page
│   │   └── globals.css      # Global styles
│   └── components/          # React components (add here)
├── public/                  # Static assets
├── next.config.ts          # Next.js configuration
├── tailwind.config.ts       # Tailwind CSS configuration
├── tsconfig.json           # TypeScript configuration
└── package.json            # Dependencies
```

## Learn More

- [Next.js Documentation](https://nextjs.org/docs)
- [Vercel Speed Insights](https://vercel.com/docs/speed-insights)
- [Tailwind CSS](https://tailwindcss.com)

## License

This project is part of the Pi Forge Quantum Genesis initiative.
