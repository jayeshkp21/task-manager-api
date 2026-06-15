'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Loader2 } from 'lucide-react';
import { api } from '@/lib/api';

interface SignupFormData {
  username: string;
  email: string;
  firstName: string;
  lastName: string;
  password: string;
}

export function SignupForm() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SignupFormData>({
    defaultValues: {
      username: '',
      email: '',
      firstName: '',
      lastName: '',
      password: '',
    },
  });

  const onSubmit = async (data: SignupFormData) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await api.signup({
        username: data.username,
        email: data.email,
        first_name: data.firstName,
        last_name: data.lastName,
        password: data.password,
      });

      const resData = await response.json();

      if (response.ok) {
        setSuccessMessage(resData.message || 'Account Created! Please check your email to verify your account.');
      } else {
        setError(resData.message || resData.detail || 'Failed to create account');
      }
    } catch (err: any) {
      console.error('Signup error:', err);
      setError('A connection error occurred. Please try again later.');
    } finally {
      setIsLoading(false);
    }
  };

  if (successMessage) {
    return (
      <div className="w-full max-w-md mx-auto">
        <div className="bg-card border border-border rounded-lg shadow-sm p-8 text-center">
          <div className="mb-6">
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100 text-green-600">
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
              </svg>
            </div>
          </div>
          <h1 className="text-2xl font-bold text-foreground mb-4">Registration Successful</h1>
          <p className="text-muted-foreground mb-8">{successMessage}</p>
          <Link href="/login" className="inline-block w-full py-2.5 px-4 bg-primary text-primary-foreground font-medium rounded-md hover:bg-primary/90 text-center transition-colors">
            Go to Login
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full max-w-md mx-auto">
      <div className="bg-card border border-border rounded-lg shadow-sm p-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-foreground mb-2">Create account</h1>
          <p className="text-muted-foreground">Join TaskManager today</p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* Username Field */}
          <div className="space-y-2">
            <label htmlFor="username" className="text-sm font-medium text-foreground">
              Username
            </label>
            <Input
              id="username"
              type="text"
              placeholder="your_username"
              {...register('username', {
                required: 'Username is required',
                minLength: {
                  value: 3,
                  message: 'Username must be at least 3 characters',
                },
              })}
              disabled={isLoading}
              className="w-full"
              aria-invalid={errors.username ? 'true' : 'false'}
            />
            {errors.username && (
              <p className="text-sm text-destructive">{errors.username.message}</p>
            )}
          </div>

          {/* Email Field */}
          <div className="space-y-2">
            <label htmlFor="email" className="text-sm font-medium text-foreground">
              Email address
            </label>
            <Input
              id="email"
              type="email"
              placeholder="you@example.com"
              {...register('email', {
                required: 'Email is required',
                pattern: {
                  value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                  message: 'Invalid email address',
                },
              })}
              disabled={isLoading}
              className="w-full"
              aria-invalid={errors.email ? 'true' : 'false'}
            />
            {errors.email && (
              <p className="text-sm text-destructive">{errors.email.message}</p>
            )}
          </div>

          {/* First Name Field */}
          <div className="space-y-2">
            <label htmlFor="firstName" className="text-sm font-medium text-foreground">
              First name
            </label>
            <Input
              id="firstName"
              type="text"
              placeholder="John"
              {...register('firstName', {
                required: 'First name is required',
              })}
              disabled={isLoading}
              className="w-full"
              aria-invalid={errors.firstName ? 'true' : 'false'}
            />
            {errors.firstName && (
              <p className="text-sm text-destructive">{errors.firstName.message}</p>
            )}
          </div>

          {/* Last Name Field */}
          <div className="space-y-2">
            <label htmlFor="lastName" className="text-sm font-medium text-foreground">
              Last name
            </label>
            <Input
              id="lastName"
              type="text"
              placeholder="Doe"
              {...register('lastName', {
                required: 'Last name is required',
              })}
              disabled={isLoading}
              className="w-full"
              aria-invalid={errors.lastName ? 'true' : 'false'}
            />
            {errors.lastName && (
              <p className="text-sm text-destructive">{errors.lastName.message}</p>
            )}
          </div>

          {/* Password Field */}
          <div className="space-y-2">
            <label htmlFor="password" className="text-sm font-medium text-foreground">
              Password
            </label>
            <Input
              id="password"
              type="password"
              placeholder="Enter a secure password"
              {...register('password', {
                required: 'Password is required',
                minLength: {
                  value: 6,
                  message: 'Password must be at least 6 characters',
                },
              })}
              disabled={isLoading}
              className="w-full"
              aria-invalid={errors.password ? 'true' : 'false'}
            />
            {errors.password && (
              <p className="text-sm text-destructive">{errors.password.message}</p>
            )}
          </div>

          {error && (
            <div className="p-3 text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded-md">
              {error}
            </div>
          )}

          {/* Submit Button */}
          <Button
            type="submit"
            disabled={isLoading}
            className="w-full h-10 mt-6"
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 size-4 animate-spin" />
                <span>Creating account...</span>
              </>
            ) : (
              <span>Sign up</span>
            )}
          </Button>
        </form>

        {/* Sign in link */}
        <div className="mt-6 text-center">
          <p className="text-sm text-muted-foreground">
            Already have an account?{' '}
            <Link
              href="/login"
              className="font-medium text-primary hover:underline"
            >
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
