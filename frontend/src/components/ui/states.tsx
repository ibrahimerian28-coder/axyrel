export function LoadingState() { return <div className="state" role="status">Loading your workspace…</div>; }
export function EmptyState({ title, description }: { title: string; description: string }) { return <section className="state"><h2>{title}</h2><p>{description}</p></section>; }
export function ErrorState({ message, retry }: { message: string; retry?: () => void }) { return <section className="state" role="alert"><h2>Unable to load</h2><p>{message}</p>{retry && <button onClick={retry}>Try again</button>}</section>; }
export function PermissionState() { return <section className="state" role="alert"><h2>Access unavailable</h2><p>Your account does not have permission to view this area.</p></section>; }
