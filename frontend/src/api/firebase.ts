import { initializeApp, getApps } from "firebase/app";
import { createUserWithEmailAndPassword, getAuth, GoogleAuthProvider, signInWithEmailAndPassword, signInWithPopup } from "firebase/auth";

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
};

export const firebaseConfigured = Object.values(firebaseConfig).every(Boolean);

const app = firebaseConfigured
  ? (getApps()[0] ?? initializeApp(firebaseConfig))
  : null;
const auth = app ? getAuth(app) : null;

export async function signInWithGoogle(): Promise<string> {
  if (!auth) throw new Error("Google sign-in is not configured for this environment.");
  try {
    const result = await signInWithPopup(auth, new GoogleAuthProvider());
    return result.user.getIdToken();
  } catch (error) {
    const code = (error as { code?: string }).code;
    if (code === "auth/popup-closed-by-user") throw new Error("Google sign-in was cancelled.");
    if (code === "auth/unauthorized-domain") throw new Error("This website domain is not authorized in Firebase.");
    if (code === "auth/popup-blocked") throw new Error("Your browser blocked the Google sign-in popup.");
    throw new Error("Google sign-in could not be completed. Check Firebase Authentication settings.");
  }
}

export async function signInWithEmail(email: string, password: string): Promise<string> {
  if (!auth) throw new Error("Firebase authentication is not configured for this environment.");
  const result = await signInWithEmailAndPassword(auth, email, password);
  return result.user.getIdToken();
}

export async function registerWithEmail(email: string, password: string): Promise<string> {
  if (!auth) throw new Error("Firebase authentication is not configured for this environment.");
  const result = await createUserWithEmailAndPassword(auth, email, password);
  return result.user.getIdToken();
}