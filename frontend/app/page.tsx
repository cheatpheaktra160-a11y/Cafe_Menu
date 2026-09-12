import Link from 'next/link';

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-coffee-50 via-white to-coffee-100 text-coffee-900">
      <div className="mx-auto flex min-h-screen max-w-6xl flex-col items-center justify-center px-6 py-16">
        <div className="rounded-[2rem] border border-coffee-200 bg-white/90 p-10 shadow-[0_20px_80px_rgba(101,67,44,0.12)] backdrop-blur-xl">
          <h1 className="text-4xl font-semibold tracking-tight text-coffee-900 sm:text-5xl">
            Cafe Menu Frontend
          </h1>
          <p className="mt-4 max-w-2xl text-base text-coffee-700 sm:text-lg">
            A React + TypeScript + Tailwind frontend scaffold, ready for your shadcn-style UI components.
          </p>
          <div className="mt-10 flex flex-col gap-4 sm:flex-row">
            <Link href="/demo" className="inline-flex items-center justify-center rounded-2xl bg-coffee-700 px-6 py-3 text-white transition hover:bg-coffee-800">
              Open Demo
            </Link>
            <Link href="/components/ui/modern-login-signup" className="inline-flex items-center justify-center rounded-2xl border border-coffee-300 bg-white px-6 py-3 text-coffee-900 transition hover:bg-coffee-50">
              View Component Path
            </Link>
          </div>
        </div>
      </div>
    </main>
  );
}
