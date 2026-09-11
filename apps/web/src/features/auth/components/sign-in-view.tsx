export { GithubAuthButton, InteractiveGrid, UserAuthForm } from './github-auth-button';

export default function SignInView() {
  return (
    <div className='container mx-auto py-10 text-center'>
      <h1 className='text-2xl font-bold'>Sign In</h1>
      <p className='text-muted-foreground mt-2'>
        Authentication is disabled in this self-hosted deployment — all tools are open access.
      </p>
    </div>
  );
}
