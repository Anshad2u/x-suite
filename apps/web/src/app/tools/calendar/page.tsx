'use client';

import * as React from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Card, CardContent, CardDescription, CardHeader, CardTitle
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { IconCalendar, IconSearch } from '@tabler/icons-react';
import { analyzeProfile, type AnalysisResult } from '@/lib/api';
import { generateContentCalendar } from '@/lib/analytics';

export default function CalendarPage() {
  const [username, setUsername] = React.useState('');
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [result, setResult] = React.useState<AnalysisResult | null>(null);

  const run = async () => {
    if (!username.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await analyzeProfile(username.trim());
      setResult(data);
    } catch (e: any) {
      setError(e?.message || 'Failed to analyze profile');
    } finally {
      setLoading(false);
    }
  };

  const calendar = result ? generateContentCalendar(result.tweets) : [];

  return (
    <div className='container mx-auto max-w-7xl py-8'>
      <div className='mb-8'>
        <h1 className='text-3xl font-bold mb-2'>Content Calendar Generator</h1>
        <p className='text-muted-foreground'>
          Analyze any account and auto-generate a weekly posting calendar from its winning
          patterns — best days, best hours, best content types.
        </p>
      </div>

      <div className='flex gap-2 mb-6'>
        <Input
          placeholder='Enter username (e.g., wilczyn)'
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && run()}
          className='max-w-md'
        />
        <Button onClick={run} disabled={loading || !username.trim()}>
          <IconSearch className='w-4 h-4 mr-2' />
          {loading ? 'Analyzing…' : 'Generate Calendar'}
        </Button>
      </div>

      {loading && (
        <div className='space-y-3'>
          <Skeleton className='h-10 w-2/3' />
          <Skeleton className='h-64 w-full' />
        </div>
      )}

      {error && (
        <Card className='mb-6 border-destructive'>
          <CardContent className='pt-6 text-sm text-destructive'>{error}</CardContent>
        </Card>
      )}

      {!loading && calendar.length > 0 && (
        <div className='space-y-6'>
          <Card>
            <CardHeader>
              <CardTitle className='flex items-center gap-2'>
                <IconCalendar className='w-5 h-5 text-primary' />
                Weekly Calendar for @{result?.username}
              </CardTitle>
              <CardDescription>
                Built from {result?.total_tweets} analyzed tweets. Slots are ranked by average
                engagement score.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className='grid gap-3 md:grid-cols-2 lg:grid-cols-4'>
                {calendar.map((entry, i) => (
                  <div key={i} className='rounded-lg border p-4 space-y-2'>
                    <div className='flex items-center justify-between'>
                      <span className='font-semibold text-sm'>{entry.day}</span>
                      <Badge variant='secondary'>{entry.slot}</Badge>
                    </div>
                    <Badge variant='outline'>{entry.contentType}</Badge>
                    <p className='text-xs text-muted-foreground line-clamp-3'>
                      {entry.example}
                    </p>
                    <p className='text-xs'>
                      Expected score:{' '}
                      <span className='font-semibold text-primary'>
                        {entry.expectedScore.toLocaleString()}
                      </span>
                    </p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {!loading && !error && calendar.length === 0 && (
        <Card>
          <CardContent className='py-10 text-center text-sm text-muted-foreground'>
            Enter a username above to generate a data-driven weekly content calendar.
          </CardContent>
        </Card>
      )}
    </div>
  );
}
