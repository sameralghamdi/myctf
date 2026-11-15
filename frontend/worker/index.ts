/**
 * Cloudflare Worker: serves the React app and proxies the API.
 *
 * wrangler.jsonc sends only /api/*, /admin/api/* and /labs/* to this code; every
 * other request is answered straight from the built files in dist/ (with
 * index.html as the fallback for client-side routes). Because the browser only
 * ever talks to your own domain, the session cookie is first-party: no CORS.
 *
 * Runtime variables (Workers & Pages -> your project -> Settings ->
 * Variables and secrets), NOT "Build variables":
 *   ORIGIN_URL      https://api.example.com   (your Cloudflare Tunnel hostname)
 *   ORIGIN_SECRET   must equal MYCTF_ORIGIN_SECRET on the server (type: Secret)
 */
interface Env {
  ORIGIN_URL?: string;
  ORIGIN_SECRET?: string;
}

const json = (body: unknown, status: number): Response =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
  });

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const originUrl = (env.ORIGIN_URL ?? "").trim();
    // Pasted secrets often carry a stray space or newline; strip it.
    const originSecret = (env.ORIGIN_SECRET ?? "").trim();
    if (!originUrl) return json({ error: "ORIGIN_URL is not configured" }, 500);

    const incoming = new URL(request.url);
    // TEMPORARY diagnostic (remove after setup): reports presence and length only.
    if (incoming.pathname === "/api/_worker-check") {
      return json({ origin_url_set: true, secret_set: originSecret.length > 0, secret_length: originSecret.length }, 200);
    }
    const target = new URL(incoming.pathname + incoming.search, originUrl);

    const headers = new Headers(request.headers);
    headers.delete("host");
    // Never trust these from the browser; set them ourselves.
    headers.delete("X-Origin-Secret");
    headers.set("X-Client-IP", request.headers.get("CF-Connecting-IP") ?? "");
    if (originSecret) headers.set("X-Origin-Secret", originSecret);

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
  },
};
