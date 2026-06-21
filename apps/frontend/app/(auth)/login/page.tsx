"use client"

import { Suspense, useState } from "react"
import Link from "next/link"
import { useRouter, useSearchParams } from "next/navigation"
import { zodResolver } from "@hookform/resolvers/zod"
import axios from "axios"
import { useForm } from "react-hook-form"
import { z } from "zod"

import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useAuth } from "@/hooks/useAuth"

const loginSchema = z.object({
  email: z.string().email("Enter a valid email address."),
  password: z.string().min(1, "Password is required."),
})

type LoginFormValues = z.infer<typeof loginSchema>

function getErrorDetail(error: unknown, fallback: string): string {
  if (axios.isAxiosError(error) && typeof error.response?.data?.detail === "string") {
    return error.response.data.detail
  }
  return fallback
}

function LoginForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const next = searchParams.get("next") ?? "/dashboard"
  const { login, isLoggingIn } = useAuth()
  const [formError, setFormError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
  })

  async function onSubmit(values: LoginFormValues) {
    setFormError(null)
    try {
      await login(values)
      router.push(next)
    } catch (error) {
      setFormError(
        getErrorDetail(error, "Unable to sign in. Please check your credentials and try again.")
      )
    }
  }

  const registerHref =
    next && next !== "/dashboard" ? `/register?next=${encodeURIComponent(next)}` : "/register"

  return (
    <Card>
      <CardHeader>
        <CardTitle>Sign in</CardTitle>
        <CardDescription>Enter your email and password to continue.</CardDescription>
      </CardHeader>
      <CardContent>
        <form className="flex flex-col gap-4" onSubmit={handleSubmit(onSubmit)} noValidate>
          {formError ? (
            <Alert variant="destructive">
              <AlertDescription>{formError}</AlertDescription>
            </Alert>
          ) : null}
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              autoComplete="email"
              aria-invalid={Boolean(errors.email)}
              {...register("email")}
            />
            {errors.email ? (
              <p className="text-sm text-destructive">{errors.email.message}</p>
            ) : null}
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              autoComplete="current-password"
              aria-invalid={Boolean(errors.password)}
              {...register("password")}
            />
            {errors.password ? (
              <p className="text-sm text-destructive">{errors.password.message}</p>
            ) : null}
          </div>
          <Button type="submit" disabled={isLoggingIn}>
            {isLoggingIn ? "Signing in..." : "Sign in"}
          </Button>
        </form>
      </CardContent>
      <CardFooter className="justify-center gap-1 text-sm text-muted-foreground">
        Don&apos;t have an account?
        <Link href={registerHref} className="font-medium text-primary hover:underline">
          Create one
        </Link>
      </CardFooter>
    </Card>
  )
}

export default function LoginPage() {
  return (
    <Suspense fallback={null}>
      <LoginForm />
    </Suspense>
  )
}
