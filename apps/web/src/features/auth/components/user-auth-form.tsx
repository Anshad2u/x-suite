'use client';

import { LoadingButton } from '@/components/ui/loading-button';
import { FieldGroup } from '@/components/ui/field';
import { useAppForm } from '@/lib/form';
import { useTransition } from 'react';
import { toast } from 'sonner';
import * as z from 'zod';
import { GithubAuthButton } from './github-auth-button';

const formSchema = z.object({
  email: z.string().email({ message: 'Enter a valid email address' })
});

export default function UserAuthForm() {
  const [isPending, startTransition] = useTransition();

  return (
    <FieldGroup>
      <p className='text-muted-foreground text-sm text-center'>
        Authentication is disabled in this self-hosted deployment.
      </p>
      <GithubAuthButton />
      <LoadingButton loading={isPending} type='submit' className='w-full' disabled>
        Sign In
      </LoadingButton>
    </FieldGroup>
  );
}
