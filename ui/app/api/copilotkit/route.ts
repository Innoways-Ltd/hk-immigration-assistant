import { NextRequest } from "next/server";
import {
  CopilotRuntime,
  OpenAIAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
  langGraphPlatformEndpoint,
  copilotKitEndpoint,
} from "@copilotkit/runtime";
import OpenAI from "openai";

const openai = new OpenAI({
  apiKey: process.env.AZURE_OPENAI_API_KEY,
  baseURL: `${process.env.AZURE_OPENAI_ENDPOINT}/openai/deployments/${process.env.AZURE_OPENAI_DEPLOYMENT}`,
  defaultQuery: { "api-version": process.env.AZURE_OPENAI_API_VERSION },
  defaultHeaders: { "api-key": process.env.AZURE_OPENAI_API_KEY },
});
const llmAdapter = new OpenAIAdapter({ openai, model: process.env.AZURE_OPENAI_DEPLOYMENT || "gpt-4o" } as any);
const langsmithApiKey = process.env.LANGSMITH_API_KEY as string;

export const POST = async (req: NextRequest) => {
  try {
    const searchParams = req.nextUrl.searchParams;
    const deploymentUrl = searchParams.get("lgcDeploymentUrl");

    const remoteEndpoint = deploymentUrl
      ? langGraphPlatformEndpoint({
          deploymentUrl,
          langsmithApiKey,
          agents: [
            {
              name: "travel",
              description:
                "This agent helps the user plan and manage their trips",
            },
          ],
        })
      : copilotKitEndpoint({
          url:
            process.env.REMOTE_ACTION_URL || "http://localhost:8000/copilotkit",
        });

    const runtime = new CopilotRuntime({
      remoteEndpoints: [remoteEndpoint],
    });

    const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
      runtime,
      serviceAdapter: llmAdapter,
      endpoint: "/api/copilotkit",
    });

    // 设置响应超时为 5 分钟，避免 ResponseAborted 错误
    const response = await handleRequest(req);

    // 为响应添加超时头
    const newHeaders = new Headers(response.headers);
    newHeaders.set('X-Accel-Buffering', 'no'); // 禁用 Nginx 缓冲
    newHeaders.set('Cache-Control', 'no-cache');
    newHeaders.set('Connection', 'keep-alive');

    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: newHeaders,
    });

  } catch (error: any) {
    console.error("CopilotKit API error:", error);

    // 处理 ResponseAborted 错误
    if (error?.name === "ResponseAborted" || error?.message?.includes("Aborted")) {
      console.warn("Request was aborted by client, this is usually normal");
      return new Response(null, { status: 499 }); // Client Closed Request
    }

    // 处理其他错误
    return new Response(
      JSON.stringify({
        error: "Internal server error",
        message: error?.message || "An unexpected error occurred",
      }),
      {
        status: 500,
        headers: { "Content-Type": "application/json" },
      }
    );
  }
};

// 配置 API 路由的最大执行时间（以秒为单位）
export const maxDuration = 300; // 5 minutes
