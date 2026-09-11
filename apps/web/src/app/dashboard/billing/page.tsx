import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export default function BillingPage() {
  return (
    <div className="container mx-auto py-10">
      <Card>
        <CardHeader>
          <CardTitle>Billing & Plans</CardTitle>
          <CardDescription>Subscription management is not configured in this environment.</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Billing features are powered by Clerk Billing and are not available in this self-hosted deployment.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
