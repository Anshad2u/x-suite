'use server';

import { revalidatePath } from 'next/cache';
import { createGroup, deleteGroup } from '@/lib/server/queries';

export async function createGroupAction(formData: FormData) {
  const name = String(formData.get('name') ?? '').trim();
  const description = String(formData.get('description') ?? '').trim();
  const color = String(formData.get('color') ?? '#6366f1').trim() || '#6366f1';
  if (!name) return;
  await createGroup(name, description, color);
  revalidatePath('/groups');
  revalidatePath('/');
}

export async function deleteGroupAction(formData: FormData) {
  const name = String(formData.get('name') ?? '').trim();
  if (!name) return;
  await deleteGroup(name);
  revalidatePath('/groups');
  revalidatePath('/');
}
