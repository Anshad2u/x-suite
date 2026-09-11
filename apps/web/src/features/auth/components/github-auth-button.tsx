'use client';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

export function GithubAuthButton() {
  return (
    <Button variant="outline" type="submit" className="w-full">
      Continue with GitHub
    </Button>
  );
}

export function InteractiveGrid() {
  return null;
}

export function UserAuthForm() {
  return (
    <div className="grid gap-6">
      <div className="space-y-2">
        <Label htmlFor="email">Email</Label>
        <Input id="email" type="email" placeholder="name@example.com" />
      </div>
      <Button>Sign In</Button>
    </div>
  );
}
