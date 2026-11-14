/**
 * Cloudflare Pages Function: same-origin reverse proxy to the MyCTF API.
 *
 * public/_routes.json limits it to /api/*, /admin/api/* and /labs/*; everything
 * else is static files served by Pages. Because the browser only ever talks to
 * your own domain, the session cookie is first-party: no CORS, no SameSite
 * workarounds.
 *
 * Environment variables (Pages -> Settings -> Variables and Secrets):
 *   ORIGIN_URL      https://api.example.com   (your Cloudflare Tunnel hostname)
 *   ORIGIN_SECRET   must equal MYCTF_ORIGIN_SECRET on the server
 */
interface Env {
  ORIGIN_URL?: string;
  ORIGIN_SECRET?: string;
}

interface Context {
  request: Request;
  env: Env;
}

const json = (body: unknown, status: number): Response =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });

export const onRequest = async ({ request, env }: Context): Promise<Response> => {
  if (!env.ORIGIN_URL) return json({ error: "ORIGIN_URL is not configured" }, 500);

  const incoming = new URL(request.url);
  const target = new URL(incoming.pathname + incoming.search, env.ORIGIN_URL);

  const headers = new Headers(request.headers);
  headers.delete("host");
  // Never trust these from the browser; set them ourselves.
  headers.delete("X-Origin-Secret");
  headers.set("X-Client-IP", request.headers.get("CF-Connecting-IP") ?? "");
  if (env.ORIGIN_SECRET) headers.set("X-Origin-Secret", env.ORIGIN_SECRET);

  const hasBody = request.method !== "GET" && request.method !== "HEAD";
  try {
    return await fetch(target.toString(), {
      method: request.method,
      headers,
      body: hasBody ? request.body : undefined,
      // Pass Flask redirects straight to the browser instead of following them.
      redirect: "manual",
    });
  } catch {
    return json({ error: "The API is unreachable right now. Try again in a moment." }, 502);
  }
};
