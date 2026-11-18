const ORIGIN = "https://zac-assessoria.carolschimitez491.chatgpt.site";
const EVENT_PATH = "/images/galeria/eventos/";
const REPO_EVENT_URL = "https://raw.githubusercontent.com/gestaoautop-dotcom/ZAC-ASSESSORIA/main/galeria/eventos/";
const eventName = i => "zac-evento-" + String(i).padStart(2, "0") + ".jpg";
const galleryFrames = Array.from({length:11}, (_,i) => {
  const n=i+1;
  return '<figure class="carousel-frame"><img loading="lazy" decoding="async" src="' + EVENT_PATH + eventName(n) + '" alt="Registro de encontro e relacionamento da ZAC — fotografia ' + n + '"></figure>';
}).join("");

export default {
  async fetch(request) {
    const target = new URL(request.url);
    if (target.pathname.startsWith(EVENT_PATH)) {
      const filename = target.pathname.slice(EVENT_PATH.length);
      if (!/^zac-evento-(0[1-9]|1[01])\.jpg$/.test(filename)) {
        return new Response("Not found", {status:404});
      }
      const imageResponse = await fetch(REPO_EVENT_URL + filename);
      if (!imageResponse.ok) return new Response("Not found", {status:404});
      return new Response(imageResponse.body, {
        status:200,
        headers:{"content-type":"image/jpeg","cache-control":"public, max-age=3600","x-content-type-options":"nosniff"}
      });
    }
    const upstream = new URL(target.pathname + target.search, ORIGIN);
    const headers = new Headers(request.headers);
    headers.delete("host");
    headers.delete("cf-connecting-ip");
    headers.delete("x-forwarded-host");
    headers.delete("x-forwarded-proto");
    const upstreamResponse = await fetch(new Request(upstream.toString(), {
      method: request.method,
      headers,
      body:["GET","HEAD"].includes(request.method) ? undefined : request.body,
      redirect:"manual"
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
      const first = await fetch(REPO_EVENT_URL + eventName(1), {method:"HEAD"});
      if (first.ok) {
        const rewrite = new HTMLRewriter().on("#zac-photo-track", {
          element(element) {
            element.append(galleryFrames, {html:true});
          }
        });
        return rewrite.transform(new Response(html, {status:upstreamResponse.status, headers:responseHeaders}));
      }
      return new Response(html, {status:upstreamResponse.status, headers:responseHeaders});
    }
    return new Response(upstreamResponse.body, {status:upstreamResponse.status, headers:responseHeaders});
  }
};
