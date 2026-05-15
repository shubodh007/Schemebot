export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background relative overflow-hidden">
      <div className="absolute top-1/3 left-1/3 w-96 h-96 bg-saffron-500/5 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-64 h-64 bg-jade-500/5 rounded-full blur-[100px] pointer-events-none" />
      <div className="relative w-full max-w-md px-4">
        {children}
      </div>
    </div>
  );
}
