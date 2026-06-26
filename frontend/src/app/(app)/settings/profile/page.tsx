"use client";
import { useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { useDashboardStore } from "@/stores/dashboard-store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

function PasswordModal({ onClose, onSave }: { onClose: () => void; onSave: () => void }) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-sm rounded-xl border border-qm-border bg-qm-card p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="mb-4 text-lg font-bold text-qm-text">Change Password</h3>
        <div className="space-y-3">
          <Input label="Current password" type="password" />
          <Input label="New password" type="password" />
          <Input label="Confirm new password" type="password" />
        </div>
        <div className="mt-5 flex justify-end gap-2">
          <Button variant="secondary" size="sm" onClick={onClose}>
            Cancel
          </Button>
          <Button size="sm" onClick={onSave}>
            Update
          </Button>
        </div>
      </div>
    </div>
  );
}

export default function ProfilePage() {
  const { user } = useAuth();
  const addNotification = useDashboardStore((s) => s.addNotification);
  const [name, setName] = useState(user?.displayName ?? "");
  const [showPwModal, setShowPwModal] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

  const initial = (name || user?.email || "U").charAt(0).toUpperCase();

  return (
    <div className="space-y-8">
      <section className="space-y-4">
        <div className="flex items-center gap-4">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-qm-green text-2xl font-bold text-white">
            {initial}
          </div>
          <span className="text-sm text-qm-text3">Profile avatar</span>
        </div>
        <Input label="Display Name" value={name} onChange={(e) => setName(e.target.value)} />
        <Input label="Email" value={user?.email ?? ""} readOnly disabled />
        <div className="flex items-center gap-3">
          <Button onClick={() => addNotification("Profile saved (mocked)", "success")}>
            Save Changes
          </Button>
          <button
            onClick={() => setShowPwModal(true)}
            className="text-sm text-qm-green hover:underline"
          >
            Change password
          </button>
        </div>
      </section>

      <section className="rounded-xl border border-red-500/30 bg-red-500/5 p-4">
        <h3 className="text-sm font-semibold text-red-400">Danger Zone</h3>
        <p className="mt-1 text-xs text-qm-text3">Permanently delete your account and all data.</p>
        {!confirmDelete ? (
          <Button variant="danger" size="sm" className="mt-3" onClick={() => setConfirmDelete(true)}>
            Delete account
          </Button>
        ) : (
          <div className="mt-3 flex items-center gap-2">
            <span className="text-sm text-qm-text2">Are you sure?</span>
            <Button
              variant="danger"
              size="sm"
              onClick={() => {
                setConfirmDelete(false);
                addNotification("Account deletion is mocked", "warning");
              }}
            >
              Yes, delete
            </Button>
            <Button variant="secondary" size="sm" onClick={() => setConfirmDelete(false)}>
              Cancel
            </Button>
          </div>
        )}
      </section>

      {showPwModal && (
        <PasswordModal
          onClose={() => setShowPwModal(false)}
          onSave={() => {
            setShowPwModal(false);
            addNotification("Password changed (mocked)", "success");
          }}
        />
      )}
    </div>
  );
}
