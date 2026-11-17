"use client";
import { useSearchParams, useRouter } from "next/navigation";
import { Suspense, useState } from "react";
import { Button } from "@f1/ui";
import { authClient } from "@/lib/auth-client";
import { safeNext } from "@/lib/safe-next";

function Form() {
  const params = useSearchParams();
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  return (
    <form
      className="mx-auto mt-16 flex max-w-sm flex-col gap-3"
      onSubmit={async (e) => {
        e.preventDefault();
        const data = new FormData(e.currentTarget);
        const { error } = await authClient.signIn.email({
          email: String(data.get("email")), password: String(data.get("password")),
        });
        if (error) return setError(error.message ?? "Sign in failed");
        router.push(safeNext(params.get("next")));
      }}
    >
      <h1 className="font-[var(--font-display)] text-3xl font-bold">Sign in</h1>
      <input name="email" type="email" required aria-label="Email" className="rounded-md bg-carbon-800 p-3" />
      <input name="password" type="password" required aria-label="Password" className="rounded-md bg-carbon-800 p-3" />
      {error ? <p role="alert" className="text-brand">{error}</p> : null}
      <Button type="submit">Sign in</Button>
      <a href="/sign-up" className="text-sm text-carbon-200 underline">Create an account</a>
    </form>
  );
}

export default function SignInPage() {
  return <Suspense><Form /></Suspense>;
}
