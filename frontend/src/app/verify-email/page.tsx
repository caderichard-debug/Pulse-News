"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import Footer from '@/components/Footer';

function VerifyEmailContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const token = searchParams.get("token");
  const [status, setStatus] = useState<
    "checking" | "success" | "error" | "invalid"
  >("checking");
  const [message, setMessage] = useState("");

  useEffect(() => {
    const verify = async () => {
      if (!token) {
        setStatus("invalid");
        setMessage("Missing or invalid verification token.");
        return;
      }
      try {
        const data = await api.verifyEmail(token);
        setStatus("success");
        setMessage(data.message || "Email verified successfully!");
        // Redirect after delay
        setTimeout(() => router.push("/feed"), 3000);
      } catch (err) {
        console.error(err);
        setStatus("error");
        setMessage(err instanceof Error ? err.message : "Verification failed.");
      }
    };

    verify();
  }, [token, router]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="rounded-lg bg-card p-8 shadow-md text-center max-w-md">
        {status === "checking" && (
          <p className="text-muted-foreground">Verifying your email...</p>
        )}
        {status === "success" && (
          <p className="text-green-600 font-medium">{message}</p>
        )}
        {status === "error" && (
          <p className="text-red-600 font-medium">{message}</p>
        )}
        {status === "invalid" && (
          <p className="text-yellow-600 font-medium">{message}</p>
        )}
      </div>
      <Footer />
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="rounded-lg bg-card p-8 shadow-md text-center max-w-md">
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    }>
      <VerifyEmailContent />
    </Suspense>
  );
}
