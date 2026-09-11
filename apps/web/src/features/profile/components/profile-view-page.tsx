'use client';

export default function ProfileViewPage() {
  return (
    <div className="p-6">
      <div className="flex flex-col space-y-4">
        <div>
          <h1 className="text-2xl font-bold">Profile Settings</h1>
          <p className="text-muted-foreground mt-2">
            Profile management is not available in this self-hosted deployment.
          </p>
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          <div className="border rounded-lg p-4">
            <h3 className="font-semibold mb-2">Account</h3>
            <p className="text-sm text-muted-foreground">Email, password, and basic info</p>
          </div>
          <div className="border rounded-lg p-4">
            <h3 className="font-semibold mb-2">Appearance</h3>
            <p className="text-sm text-muted-foreground">Theme and display settings</p>
          </div>
          <div className="border rounded-lg p-4">
            <h3 className="font-semibold mb-2">Notifications</h3>
            <p className="text-sm text-muted-foreground">Email and push preferences</p>
          </div>
        </div>
      </div>
    </div>
  );
}
