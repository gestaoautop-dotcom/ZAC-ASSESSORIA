// Independent hosting for the approved ZAC static site and its contact forms.
// No runtime requests to the former ChatGPT origin.
function json(value, status = 200) {
  return Response.json(value, { status, headers: { "cache-control": "no-store", "x-content-type-options": "nosniff" } });
}
function clean(value, max) {
  return typeof value === "string" ? value.trim().slice(0, max + 1) : "";
}
async function handleLead(request, env) {
  if (request.method !== "POST") return json({error:"Método não permitido."},405);
  const url = new URL(request.url);
  const origin = request.headers.get("origin");
  if (origin && origin !== url.origin) return json({error:"Origem não autorizada."},403);
  if (request.headers.get("sec-fetch-site") === "cross-site") return json({error:"Origem não autorizada."},403);
  if (!(request.headers.get("content-type")||"").toLowerCase().includes("application/json")) return json({error:"Formato inválido."},415);
  if (!env.LEADS_DB) return json({error:"Serviço de atendimento temporariamente indisponível."},503);
  let body;
  try {
    const raw = await request.text();
    if (raw.length > 8192) return json({error:"Mensagem muito longa."},413);
    body = JSON.parse(raw);
    if (!body || typeof body !== "object" || Array.isArray(body)) throw Error("invalid");
  } catch {
    return json({error:"Dados inválidos."},400);
  }
  // Honeypot: silently discard automated submissions without storing PII.
  if (clean(body.website,120)) return json({ok:true,id:crypto.randomUUID()});
  const name = clean(body.name,100);
  const email = clean(body.email,200).toLowerCase();
  const phone = clean(body.phone,25);
  const subject = clean(body.subject,220);
  const message = clean(body.message,1800);
  const requestType = ["privacidade","acessibilidade"].includes(body.requestType) ? body.requestType : "contato";
  const consent = body.consent === true || body.consent === "on";
  if (name.length < 2 || name.length > 100 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) || email.length > 200) {
    return json({error:"Verifique nome e e-mail."},400);
  }
  if (requestType === "contato" && (!consent || phone.length < 10 || phone.length > 25)) {
    return json({error:"Informe telefone e autorização de contato."},400);
  }
  if (requestType !== "contato" && (message.length < 10 || message.length > 1800)) {
    return json({error:"Descreva sua solicitação."},400);
  }
  const id = crypto.randomUUID();
  try {
    await env.LEADS_DB.prepare(
      "INSERT INTO leads (id, request_type, name, phone, email, subject, message, consent) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
    ).bind(id,requestType,name,phone||null,email,subject||null,message||null,consent?1:0).run();
  } catch {
    return json({error:"Não foi possível registrar a solicitação. Tente novamente."},503);
  }
  return json({ok:true,id},201);
}
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/api/leads") return handleLead(request,env);
    if (request.method !== "GET" && request.method !== "HEAD") {
      return new Response("Method Not Allowed", {status:405,headers:{"allow":"GET, HEAD"}});
    }
    const response = await env.ASSETS.fetch(request);
    const headers = new Headers(response.headers);
    headers.set("x-zac-hosting","cloudflare-independent");
    headers.set("x-content-type-options","nosniff");
    return new Response(request.method === "HEAD" ? null : response.body, {status:response.status,headers});
  }
};
