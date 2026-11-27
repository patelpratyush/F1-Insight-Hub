"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Button } from "@f1/ui";
import { authClient } from "@/lib/auth-client";

export default function SignUpPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  return (
    <form
      className="mx-auto mt-16 flex max-w-sm flex-col gap-3"
      onSubmit={async (e) => {
        e.preventDefault();
        const data = new FormData(e.currentTarget);
        const { error } = await authClient.signUp.email({
          name: String(data.get("name")), email: String(data.get("email")),
          password: String(data.get("password")),
        });
        if (error) return setError(error.message ?? "Sign up failed");
        router.push("/standings");
      }}
    >
      <h1 className="font-[var(--font-display)] text-3xl font-bold">Create account</h1>
      <input name="name" required aria-label="Name" className="rounded-md bg-carbon-800 p-3" />
      <input name="email" type="email" required aria-label="Email" className="rounded-md bg-carbon-800 p-3" />
      <input name="password" type="password" required minLength={10} aria-label="Password" className="rounded-md bg-carbon-800 p-3" />
      {error ? <p role="alert" className="text-brand">{error}</p> : null}
      <Button type="submit">Sign up</Button>
    </form>
  );
}
