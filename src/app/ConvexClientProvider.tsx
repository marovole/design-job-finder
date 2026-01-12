"use client";

import { ReactNode } from "react";
import { ConvexAuthProvider } from "@convex-dev/auth/react";
import { convex } from "@/lib/convex-client";

export function ConvexClientProvider({ children }: { children: ReactNode }) {
  return (
    <ConvexAuthProvider client={convex}>
      {children}
    </ConvexAuthProvider>
  );
}
