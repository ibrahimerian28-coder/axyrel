"use client";
import { ErrorState } from "@/components/ui/states";
export default function ErrorBoundary({ reset }: { reset: () => void }) { return <ErrorState message="The workspace could not be loaded. Please try again." retry={reset} />; }
