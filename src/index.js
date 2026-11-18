const ORIGIN = "https://zac-assessoria.carolschimitez491.chatgpt.site";
const EVENT_PATH = "/images/galeria/eventos/";
const RAW_PATH = "https://raw.githubusercontent.com/gestaoautop-dotcom/ZAC-ASSESSORIA/main/galeria/eventos/";
const NAMES = Array.from({length:11}, (_,i) => "zac-evento-" + String(i+1).padStart(2,"0") + ".jpg");
const FRAMES = NAMES.map((filename,i) => '<figure class="carousel-frame"><img src="' + EVENT_PATH + filename + '" loading="lazy" decoding="async" alt="Registro de encontro e evento da ZAC — foto ' + (i+1) + '"></figure>').join("");
export default {
  async fetch(request) {
    const url = new URL(request.url);
    if (url.pathname.startsWith(EVENT_PATH)) {
      const filename = url.pathname.slice(EVENT_PATH.length);
      if (!NAMES.includes(filename)) return new Response("Not found", {status:404});
      const res = await fetch(RAW_PATH+filename);
      if (!res.ok) return new Response("Not found", {status:404});
      return new Response(request.method === "HEAD" ? null : res.body, {
        status:200,headers:{"content-type":"image/jpeg","cache-control":"public,max-age=3600","x-content-type-options":"nosniff"}
      });
    }
    const originURL = new URL(url.pathname + url.search,ORIGIN);
    const headers = new Headers(request.headers);
    for (const h of ["host","cf-connecting-ip","x-forwarded-host","x-forwarded-proto"]) headers.delete(h);
    const res = await fetch(new Request(originURL.toString(),{
      method:request.method,headers,body:["GET","HEAD"].includes(request.method) ? undefined : request.body,redirect:"manual"
    }));
    const outHeaders = new Headers(res.headers);
    for (const h of ["content-security-policy","content-security-policy-report-only","content-length","content-encoding","set-cookie"]) outHeaders.delete(h);
    outHeaders.set("x-zac-upstream","original-chatgpt-site");
    const redirect = outHeaders.get("location");
    if (redirect) {
      const to = new URL(redirect,ORIGIN);
      if (to.origin === ORIGIN) outHeaders.set("location",url.origin+to.pathname+to.search+to.hash);
    }
    if (!(outHeaders.get("content-type") || "").includes("text/html") || request.method === "HEAD") {
      return new Response(request.method === "HEAD" ? null : res.body,{status:res.status,headers:outHeaders});
    }
    const html = (await res.text()).split(ORIGIN).join(url.origin);
    const response = new Response(html,{status:res.status,headers:outHeaders});
    // Preserve all existing photos until ALL eleven replacements are actually uploaded.
    if (res.ok) {
      return new HTMLRewriter().on("#zac-photo-track",{
        element(element){ element.setInnerContent(FRAMES,{html:true}); }
      }).transform(response);
    }
    return response;
  }
};
