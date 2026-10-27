"use client";

import { AdminProvider, useAdmin } from "@/lib/admin-context";
import AdminLogin from "@/components/admin/AdminLogin";
import AdminShell from "@/components/admin/AdminShell";

function Gate({ children }: { children: React.ReactNode }) {
  const { authed, ready } = useAdmin();

  if (!ready) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background text-muted">
        Загрузка…
      </div>
    );
  }
  if (!authed) return <AdminLogin />;
  return <AdminShell>{children}</AdminShell>;
}

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <AdminProvider>
      <Gate>{children}</Gate>
    </AdminProvider>
  );
}
