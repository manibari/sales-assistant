"use client";

import { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";

export default function IntelDetailRedirect() {
  const params = useParams();
  const router = useRouter();

  useEffect(() => {
    // Redirect to the main intel chat page — the conversation
    // will be loaded from the sidebar list
    router.replace(`/intel?id=${params.id}`);
  }, [params.id, router]);

  return (
    <div className="flex items-center justify-center h-full text-slate-400 text-sm">
      載入中...
    </div>
  );
}
