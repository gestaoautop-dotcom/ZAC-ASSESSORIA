const ORIGIN = "https://zac-assessoria.carolschimitez491.chatgpt.site";
export default {
  async fetch(request) {
    const target = new URL(request.url);
    const upstream = new URL(target.pathname + target.search, ORIGIN);
    const headers = new Headers(request.headers);
    headers.delete("host");
    headers.delete("cf-connecting-ip");
    headers.delete("x-forwarded-host");
    headers.delete("x-forwarded-proto");
    const upstreamResponse = await fetch(new Request(upstream.toString(), {
      method: request.method,
      headers,
      body: ["GET", "HEAD"].includes(request.method) ? undefined : request.body,
      redirect: "manual"
    }));
    const responseHeaders = new Headers(upstreamResponse.headers);
    responseHeaders.delete("content-security-policy");
    responseHeaders.delete("content-security-policy-report-only");
    responseHeaders.delete("content-length");
    responseHeaders.delete("content-encoding");
    responseHeaders.delete("set-cookie");
    responseHeaders.set("x-zac-upstream", "original-chatgpt-site");
    const location = responseHeaders.get("location");
    if (location) {
      const absolute = new URL(location, ORIGIN);
      if (absolute.origin === ORIGIN) {
        responseHeaders.set("location", target.origin + absolute.pathname + absolute.search + absolute.hash);
      }
    }
    if ((responseHeaders.get("content-type") || "").includes("text/html")) {
      let html = await upstreamResponse.text();
      html = html.split(ORIGIN).join(target.origin);
      return new Response(html, {status: upstreamResponse.status, headers: responseHeaders});
    }
    return new Response(upstreamResponse.body, {status: upstreamResponse.status, headers: responseHeaders});
  }
};
