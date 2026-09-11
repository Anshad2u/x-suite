import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export default function ExclusivePage() {
  return (
    <div className="container mx-auto py-10">
      <Card>
        <CardHeader>
          <CardTitle>Exclusive Content</CardTitle>
          <CardDescription>Premium features and exclusive tools</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground mb-4">
            These exclusive features require authentication and proper permissions.
          </p>
          <ul className="space-y-2 text-sm">
            <li className="flex items-center gap-2">
              <span className="text-green-500">✓</span>
              Advanced X scraping strategies
            </li>
            <li className="flex items-center gap-2">
              <span className="text-green-500">✓</span>
              Competitive content calendar generation
            </li>
            <li className="flex items-center gap-2">
              <span className="text-green-500">✓</span>
              Account health audit (automated)
            </li>
            <li className="flex items-center gap-2">
              <span className="text-green-500">✓</span>
              Historical trend analysis
            </li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
