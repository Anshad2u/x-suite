'use server';

import { revalidatePath } from 'next/cache';
import { approveDraft, rejectDraft } from '@/lib/server/queries';

export async function approveDraftAction(formData: FormData) {
  const id = Number(formData.get('id'));
  if (!Number.isFinite(id)) return;
  await approveDraft(id);
  revalidatePath('/activity');
}

export async function rejectDraftAction(formData: FormData) {
  const id = Number(formData.get('id'));
  if (!Number.isFinite(id)) return;
  await rejectDraft(id);
  revalidatePath('/activity');
}
