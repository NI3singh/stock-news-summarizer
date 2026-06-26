"use client";
import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  type ReactNode,
} from "react";
import {
  onAuthStateChanged,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signInWithPopup,
  GoogleAuthProvider,
  updateProfile,
  sendPasswordResetEmail,
  signOut as fbSignOut,
} from "firebase/auth";
import { firebaseAuth, isFirebaseConfigured } from "./firebase";

export interface AuthUser {
  uid: string;
  email: string | null;
  displayName: string | null;
}

interface AuthContextValue {
  user: AuthUser | null;
  loading: boolean;
  /** true when no Firebase project is configured and the local dev mock is in use */
  usingDevFallback: boolean;
  signInEmail: (email: string, password: string) => Promise<void>;
  signUpEmail: (name: string, email: string, password: string) => Promise<void>;
  signInGoogle: () => Promise<void>;
  resetPassword: (email: string) => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);
const DEV_KEY = "qm_dev_user";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (isFirebaseConfigured && firebaseAuth) {
      const unsub = onAuthStateChanged(firebaseAuth, (fbUser) => {
        setUser(
          fbUser
            ? { uid: fbUser.uid, email: fbUser.email, displayName: fbUser.displayName }
            : null
        );
        setLoading(false);
      });
      return () => unsub();
    }
    // Dev fallback — restore any mock user from localStorage
    try {
      const raw = localStorage.getItem(DEV_KEY);
      setUser(raw ? (JSON.parse(raw) as AuthUser) : null);
    } catch {
      setUser(null);
    }
    setLoading(false);
  }, []);

  const setDevUser = useCallback((u: AuthUser | null) => {
    if (u) localStorage.setItem(DEV_KEY, JSON.stringify(u));
    else localStorage.removeItem(DEV_KEY);
    setUser(u);
  }, []);

  const signInEmail = useCallback(
    async (email: string, password: string) => {
      if (isFirebaseConfigured && firebaseAuth) {
        await signInWithEmailAndPassword(firebaseAuth, email, password);
        return;
      }
      if (!email.includes("@") || password.length < 6) {
        throw new Error("Invalid email or password.");
      }
      setDevUser({ uid: `dev-${email}`, email, displayName: email.split("@")[0] });
    },
    [setDevUser]
  );

  const signUpEmail = useCallback(
    async (name: string, email: string, password: string) => {
      if (isFirebaseConfigured && firebaseAuth) {
        const cred = await createUserWithEmailAndPassword(firebaseAuth, email, password);
        if (name) await updateProfile(cred.user, { displayName: name });
        return;
      }
      if (!email.includes("@") || password.length < 6) {
        throw new Error("Invalid email or password.");
      }
      setDevUser({ uid: `dev-${email}`, email, displayName: name || email.split("@")[0] });
    },
    [setDevUser]
  );

  const signInGoogle = useCallback(async () => {
    if (isFirebaseConfigured && firebaseAuth) {
      await signInWithPopup(firebaseAuth, new GoogleAuthProvider());
      return;
    }
    setDevUser({ uid: "dev-google", email: "dev.user@google.local", displayName: "Dev User" });
  }, [setDevUser]);

  const resetPassword = useCallback(async (email: string) => {
    if (isFirebaseConfigured && firebaseAuth) {
      await sendPasswordResetEmail(firebaseAuth, email);
    }
    // Dev fallback: no-op (the UI shows a generic "check your email" either way)
  }, []);

  const signOut = useCallback(async () => {
    if (isFirebaseConfigured && firebaseAuth) {
      await fbSignOut(firebaseAuth);
      return;
    }
    setDevUser(null);
  }, [setDevUser]);

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        usingDevFallback: !isFirebaseConfigured,
        signInEmail,
        signUpEmail,
        signInGoogle,
        resetPassword,
        signOut,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within <AuthProvider>");
  return ctx;
}
