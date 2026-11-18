// Self-hosted archived ZAC website, served from Cloudflare Workers static assets.
// Do not route requests to ChatGPT or to other application servers.
export default {
  async fetch(request, env) {
    if (request.method !== "GET" && request.method !== "HEAD") {
      return new Response("Method Not Allowed", {status:405, headers:{"allow":"GET, HEAD"}});
    }
    // Cloudflare static assets handles / and trailing-slash/index.html canonicals.
    // Rewriting / to /index.html created a redirect loop and must not be done.
    const result = await env.ASSETS.fetch(request);
    const headers = new Headers(result.headers);
    headers.set("x-zac-hosting", "cloudflare-independent");
    headers.set("x-content-type-options", "nosniff");
    return new Response(request.method === "HEAD" ? null : result.body, {
      status:result.status, headers
    });
  }
};
