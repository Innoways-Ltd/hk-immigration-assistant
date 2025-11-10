"use client";

import dynamic from "next/dynamic";
import { TooltipProvider } from "@/components/ui/tooltip";
import { SettlementProvider } from "@/lib/hooks/use-settlement";
import { CopilotKit } from "@copilotkit/react-core";
import { CopilotSidebar, useChatContext } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";
import { useEffect } from "react";
import { useMediaQuery } from "@/lib/hooks/use-media-query";

// Disable server-side rendering for the MapCanvas component, this
// is because Leaflet is not compatible with server-side rendering
//
// https://github.com/PaulLeCam/react-leaflet/issues/45
let MapCanvas: any;
MapCanvas = dynamic(
  () =>
    import("@/components/MapCanvas").then((module: any) => module.MapCanvas),
  {
    ssr: false,
  }
);

function MainContent() {
  const { setOpen } = useChatContext();
  const isDesktop = useMediaQuery("(min-width: 900px)");
  
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const copilotOpenParam = urlParams.get('copilotOpen');
    if (copilotOpenParam !== null) {
      setOpen(copilotOpenParam === 'true');
    } else {
      setOpen(isDesktop);
    }
  }, [setOpen, isDesktop]);

  return (
    <TooltipProvider>
      <SettlementProvider>
        <main className="h-screen w-screen">
          <MapCanvas />
        </main>
      </SettlementProvider>
    </TooltipProvider>
  );
}

export default function Home() {
  const lgcDeploymentUrl =
    globalThis.window === undefined
      ? null
      : new URL(window.location.href).searchParams.get("lgcDeploymentUrl");

  return (
    <CopilotKit
      agent="immigration"
      runtimeUrl={
        process.env.NEXT_PUBLIC_CPK_PUBLIC_API_KEY == undefined
          ? `/api/copilotkit?lgcDeploymentUrl=${lgcDeploymentUrl ?? ""}`
          : "https://api.cloud.copilotkit.ai/copilotkit/v1"
      }
      publicApiKey={process.env.NEXT_PUBLIC_CPK_PUBLIC_API_KEY}
      // 增加流式响应的超时时间
      runtimeOptions={{
        timeout: 300000, // 5 minutes
        headers: {
          'X-Accel-Buffering': 'no', // 禁用缓冲
        }
      }}
    >
      <CopilotSidebar
        defaultOpen={false}
        clickOutsideToClose={false}
        // 增加聊天组件的超时设置
        timeout={300000} // 5 minutes
        labels={{
          title: "Immigration Settlement Assistant",
          initial:
            "Hello! 👋 I'm your immigration settlement assistant. I'm here to help make your move smooth and stress-free.\n\nTo get started, could you please share your order number? This will allow me to pull up your booking details and create a personalized settlement plan for you.\n\nIf you don't have an order number yet, that's okay! We can collect your information step by step.",
        }}
      >
        <MainContent />
      </CopilotSidebar>
    </CopilotKit>
  );
}
