// Serve archived static pages from Cloudflare Workers assets only.
// No upstream ChatGPT requests; asset files are included in the deployment.
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (request.method !== "GET" && request.method !== "HEAD") {
      return new Response("Method Not Allowed", {status:405, headers:{"allow":"GET, HEAD"}});
    }
    let pathname = url.pathname;
    if (pathname === "/") pathname = "/index.html";
    else if (["/privacidade","/termos","/cookies","/acessibilidade"].includes(pathname)) pathname += "/index.html";
    const assetRequest = new Request(new URL(pathname + url.search, url.origin), request);
    const response = await env.ASSETS.fetch(assetRequest);
    const headers = new Headers(response.headers);
    headers.set("x-zac-hosting","cloudflare-independent");
    headers.set("x-content-type-options","nosniff");
    return new Response(request.method === "HEAD" ? null : response.body, {status:response.status,headers});
  }
};
