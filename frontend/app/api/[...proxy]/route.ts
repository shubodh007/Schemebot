import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ proxy: string[] }> }
) {
  const { proxy } = await params;
  return proxyRequest(request, "GET", proxy);
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ proxy: string[] }> }
) {
  const { proxy } = await params;
  return proxyRequest(request, "POST", proxy);
}

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ proxy: string[] }> }
) {
  const { proxy } = await params;
  return proxyRequest(request, "PATCH", proxy);
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ proxy: string[] }> }
) {
  const { proxy } = await params;
  return proxyRequest(request, "DELETE", proxy);
}

async function proxyRequest(
  request: NextRequest,
  method: string,
  proxy: string[]
): Promise<NextResponse> {
  const path = proxy.join("/");
  const url = `${API_URL}/${path}`;
  const searchParams = request.nextUrl.searchParams.toString();
  const fullUrl = searchParams ? `${url}?${searchParams}` : url;

  const headers: Record<string, string> = {
    "Content-Type": request.headers.get("Content-Type") || "application/json",
  };

  const authHeader = request.headers.get("Authorization");
  if (authHeader) {
    headers["Authorization"] = authHeader;
  }

  const cookieHeader = request.headers.get("Cookie");
  if (cookieHeader) {
    headers["Cookie"] = cookieHeader;
  }

  let body: BodyInit | undefined;
  if (method !== "GET" && method !== "DELETE") {
    try {
      const cloned = request.clone();
      body = await cloned.text();
    } catch {
      body = undefined;
    }
  }

  try {
    const response = await fetch(fullUrl, {
      method,
      headers,
      body,
      cache: "no-store",
    });

    const responseHeaders = new Headers(response.headers);
    responseHeaders.delete("content-encoding");
    responseHeaders.delete("transfer-encoding");

    const setCookie = responseHeaders.get("set-cookie");
    const responseInit: ResponseInit & { headers: Headers } = {
      status: response.status,
      statusText: response.statusText,
      headers: responseHeaders,
    };

    const data = await response.text();

    const nextResponse = new NextResponse(data, responseInit);

    if (setCookie) {
      nextResponse.headers.set("set-cookie", setCookie);
    }

    return nextResponse;
  } catch (error) {
    return NextResponse.json(
      { code: "PROXY_ERROR", detail: "Failed to connect to backend" },
      { status: 502 }
    );
  }
}
