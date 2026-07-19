"use client";

import { useAuth } from "@/components/AuthProvider";
import { CoreShell } from "@/components/CoreShell";

export default function UsersPage() {
  const { user } = useAuth();

  return (
    <CoreShell
      title="Users"
      subtitle="Role-based access for datasets, rights, training, model promotion, and routing."
    >
      {user ? (
        <div className="border border-[var(--line)] px-4 py-4">
          <p className="text-[var(--paper)]">{user.full_name}</p>
          <p className="mt-1 text-sm text-[var(--mist)]">
            {user.email} · {user.role}
          </p>
        </div>
      ) : null}
      <p className="mt-6 text-sm text-[var(--mist)]">
        Admins create users via <code className="text-[var(--paper-dim)]">POST /api/auth/users</code>.
      </p>
    </CoreShell>
  );
}
