import ModernLoginSignup from '@/components/ui/modern-login-signup';

export default function DemoPage() {
  return (
    <main className="min-h-screen bg-coffee-50 text-coffee-900">
      <div className="mx-auto flex min-h-screen max-w-6xl items-center justify-center px-6 py-16">
        <div className="w-full rounded-[2rem] border border-coffee-200 bg-white/95 p-6 shadow-[0_20px_80px_rgba(101,67,44,0.12)]">
          <ModernLoginSignup />
        </div>
      </div>
    </main>
  );
}
