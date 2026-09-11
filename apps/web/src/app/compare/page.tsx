'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { IconLoader, IconUsers } from '@tabler/icons-react';
import { analyzeProfile, AnalysisResult } from '@/lib/api';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  LineChart,
  Line,
  CartesianGrid
} from 'recharts';

export default function ComparePage() {
  const [usernames, setUsernames] = useState<string[]>(['wilczyn', '']);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<{[key: string]: AnalysisResult}>({});

  const handleCompare = async () => {
    const validNames = usernames.filter(u => u.trim()).map(u => u.replace('@', '').trim());
    if (validNames.length < 1) return;

    setLoading(true);
    const newResults: {[key: string]: AnalysisResult} = {};
    for (const name of validNames) {
      try {
        const data = await analyzeProfile(name, 100);
        newResults[name] = data;
      } catch (err: any) {
        console.error(`Failed to fetch ${name}:`, err);
      }
    }
    setResults(newResults);
    setLoading(false);
  };

  const handleUsernameChange = (index: number, value: string) => {
    const newNames = [...usernames];
    newNames[index] = value;
    setUsernames(newNames);
  };

  const addUsername = () => {
    if (usernames.length < 4) {
      setUsernames([...usernames, '']);
    }
  };

  // Build comparison data
  const comparisonData = Object.entries(results).map(([username, result]) => ({
    username: `@${username}`,
    tweets: result.total_tweets,
    avgScore: Math.round(result.tweets.reduce((sum, t) => sum + t.score.engagement_score, 0) / result.tweets.length),
    totalLikes: result.tweets.reduce((sum, t) => sum + t.raw_metrics.likes, 0),
    totalReplies: result.tweets.reduce((sum, t) => sum + t.raw_metrics.replies, 0),
    totalViews: result.tweets.reduce((sum, t) => sum + t.raw_metrics.views, 0),
    engagementRate: result.tweets.length > 0
      ? (result.tweets.reduce((sum, t) => sum + t.score.engagement_score, 0) /
         result.tweets.reduce((sum, t) => sum + t.raw_metrics.views, 0) * 100).toFixed(1)
      : '0'
  }));

  return (
    <div className="container mx-auto py-8 max-w-7xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Compare X Accounts</h1>
        <p className="text-muted-foreground">
          Compare tweet performance, engagement scores, and growth patterns across multiple accounts.
        </p>
      </div>

      {/* Input */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Accounts to compare</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {usernames.map((name, i) => (
              <div key={i} className="flex gap-2">
                <Input
                  placeholder={`Username ${i + 1}`}
                  value={name}
                  onChange={(e) => handleUsernameChange(i, e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleCompare()}
                />
              </div>
            ))}
          </div>
          <div className="flex gap-2 mt-4">
            <Button variant="outline" onClick={addUsername} disabled={usernames.length >= 4}>
              + Add Account
            </Button>
            <Button onClick={handleCompare} disabled={loading}>
              {loading ? (
                <>
                  <IconLoader className="w-4 h-4 mr-2 animate-spin" />
                  Analyzing...
                </>
              ) : 'Compare'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Comparison Results */}
      {comparisonData.length > 0 && (
        <>
          {/* Summary cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <Card>
              <CardHeader>
                <CardTitle className="text-3xl">{comparisonData.length}</CardTitle>
                <p className="text-sm text-muted-foreground">Accounts Analyzed</p>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-3xl font-bold text-primary">
                  {comparisonData.reduce((sum, a) => sum + a.tweets, 0)}
                </CardTitle>
                <p className="text-sm text-muted-foreground">Total Tweets</p>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-3xl font-bold text-green-500">
                  {comparisonData.reduce((sum, a) => sum + a.totalViews, 0).toLocaleString()}
                </CardTitle>
                <p className="text-sm text-muted-foreground">Total Views</p>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-3xl font-bold text-blue-500">
                  {comparisonData.reduce((sum, a) => sum + a.totalLikes, 0).toLocaleString()}
                </CardTitle>
                <p className="text-sm text-muted-foreground">Total Likes</p>
              </CardHeader>
            </Card>
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            <Card>
              <CardHeader>
                <CardTitle>Avg Score per Account</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={comparisonData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="username" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="avgScore" fill="#3b82f6" name="Avg Score" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Engagement Rate Comparison</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={comparisonData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="username" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="engagementRate" stroke="#10b981" name="Rate %" />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Detailed table */}
          <Card>
            <CardHeader>
              <CardTitle>Detailed Comparison</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Account</TableHead>
                    <TableHead className="text-right">Tweets</TableHead>
                    <TableHead className="text-right">Avg Score</TableHead>
                    <TableHead className="text-right">Total Views</TableHead>
                    <TableHead className="text-right">Total Likes</TableHead>
                    <TableHead className="text-right">Total Replies</TableHead>
                    <TableHead>Rate</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {comparisonData.map((d) => (
                    <TableRow key={d.username}>
                      <TableCell className="font-medium">{d.username}</TableCell>
                      <TableCell className="text-right">{d.tweets}</TableCell>
                      <TableCell className="text-right">{d.avgScore}</TableCell>
                      <TableCell className="text-right">{d.totalViews.toLocaleString()}</TableCell>
                      <TableCell className="text-right">{d.totalLikes.toLocaleString()}</TableCell>
                      <TableCell className="text-right">{d.totalReplies.toLocaleString()}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{d.engagementRate}%</Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
