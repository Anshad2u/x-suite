'use server';

import { revalidatePath } from 'next/cache';
import { assignFollower, removeFollower } from '@/lib/server/queries';

export async function assignFollowerAction(formData: FormData) {
  const username = String(formData.get('username') ?? '').trim();
  const group = String(formData.get('group') ?? '').trim();
  if (!username || !group) return;
  await assignFollower(username, group);
  revalidatePath('/followers');
}

export async function removeFollowerAction(formData: FormData) {
  const username = String(formData.get('username') ?? '').trim();
  const group = String(formData.get('group') ?? '').trim();
  if (!username || !group) return;
  await removeFollower(username, group);
  revalidatePath('/followers');
}
