'use client';

import * as React from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import {
  Card, CardContent, CardDescription, CardHeader, CardTitle
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { IconCopy, IconWand } from '@tabler/icons-react';
import { classifyTweet } from '@/lib/analytics';

interface Angle {
  name: string;
  template: (topic: string) => string;
  why: string;
  scoreMultiplier: string;
}

const ANGLES: Angle[] = [
  {
    name: 'Question Hook',
    template: (t) => `${t.replace(/[.?!]+$/, '')} — agree or disagree?`,
    why: 'Questions drive replies, the highest-weighted metric (20x in the score).',
    scoreMultiplier: 'High reply potential'
  },
  {
    name: 'Hot Take',
    template: (t) => `Unpopular opinion: ${t.replace(/[.?!]+$/, '').toLowerCase()}. Most people get this wrong.`,
    why: 'Contrarian framing triggers quote tweets and debate.',
    scoreMultiplier: 'High repost potential'
  },
  {
    name: 'List Format',
    template: (t) => `5 lessons from ${t.replace(/[.?!]+$/, '').toLowerCase()}:\n\n1. \n2. \n3. \n4. \n5. `,
    why: 'Lists are highly bookmarkable — bookmarks are weighted 80x.',
    scoreMultiplier: 'High bookmark potential'
  },
  {
    name: 'Build in Public',
    template: (t) => `Building in public, day 1: ${t.replace(/[.?!]+$/, '').toLowerCase()}\n\nSharing every number as I go.`,
    why: 'Transparency framing drives follows and repeat engagement.',
    scoreMultiplier: 'High follow potential'
  },
  {
    name: 'Curiosity Gap',
    template: (t) => `I tested ${t.replace(/[.?!]+$/, '').toLowerCase()} for 30 days. The results surprised me 🧵`,
    why: 'Thread openers pull readers into replies and bookmarks.',
    scoreMultiplier: 'High thread potential'
  }
];

export default function ClonePage() {
  const [sourceUrl, setSourceUrl] = React.useState('');
  const [tweetText, setTweetText] = React.useState('');
  const [copied, setCopied] = React.useState<number | null>(null);

  const detected = tweetText.trim() ? classifyTweet(tweetText) : null;

  const copy = async (text: string, i: number) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(i);
      setTimeout(() => setCopied(null), 1500);
    } catch {
      /* clipboard unavailable */
    }
  };

  return (
    <div className='container mx-auto max-w-5xl py-8'>
      <div className='mb-8'>
        <h1 className='text-3xl font-bold mb-2'>Tweet Cloner</h1>
        <p className='text-muted-foreground'>
          Paste a winning tweet (yours or a competitor&apos;s) and generate scored rewrite
          angles you can post as your own.
        </p>
      </div>

      <Card className='mb-6'>
        <CardHeader>
          <CardTitle>Source tweet</CardTitle>
          <CardDescription>Optional: paste the X URL for reference</CardDescription>
        </CardHeader>
        <CardContent className='space-y-4'>
          <Input
            placeholder='https://x.com/user/status/...'
            value={sourceUrl}
            onChange={(e) => setSourceUrl(e.target.value)}
          />
          <Textarea
            placeholder='Paste the full tweet text here…'
            value={tweetText}
            onChange={(e) => setTweetText(e.target.value)}
            rows={4}
          />
          {detected && (
            <p className='text-xs text-muted-foreground'>
              Detected format: <Badge variant='outline'>{detected}</Badge>
            </p>
          )}
        </CardContent>
      </Card>

      {tweetText.trim() && (
        <div className='space-y-4'>
          <h2 className='text-xl font-semibold flex items-center gap-2'>
            <IconWand className='w-5 h-5 text-primary' />
            Rewrite angles
          </h2>
          {ANGLES.map((angle, i) => {
            const text = angle.template(tweetText.trim());
            return (
              <Card key={angle.name}>
                <CardHeader className='pb-2'>
                  <div className='flex items-center justify-between'>
                    <CardTitle className='text-base'>{angle.name}</CardTitle>
                    <Badge variant='secondary'>{angle.scoreMultiplier}</Badge>
                  </div>
                  <CardDescription>{angle.why}</CardDescription>
                </CardHeader>
                <CardContent>
                  <pre className='whitespace-pre-wrap text-sm bg-muted rounded p-3 mb-3'>
                    {text}
                  </pre>
                  <Button variant='outline' size='sm' onClick={() => copy(text, i)}>
                    <IconCopy className='w-4 h-4 mr-2' />
                    {copied === i ? 'Copied!' : 'Copy'}
                  </Button>
                </CardContent>
              </Card>
            );
          })}
          <p className='text-xs text-muted-foreground'>
            Source: {sourceUrl || 'no URL provided'}
          </p>
        </div>
      )}
    </div>
  );
}
