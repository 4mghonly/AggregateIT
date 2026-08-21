const ALLOWED_HOSTS = [
  "arctic-shift.philo.berkeley.edu",
  "api.pullpush.io",
  "rsshub.app",
  "rsshub.rssforever.com",
  "hub.slarker.me",
  "rsshub.pseudoyu.com",
  "api.stocktwits.com"
];

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const target = url.searchParams.get("target");
    if (!target) return new Response("missing target", { status: 400 });
    let t;
    try { t = new URL(target); } catch { return new Response("bad target", { status: 400 }); }
    if (!ALLOWED_HOSTS.includes(t.hostname)) return new Response("host not allowed", { status: 403 });
    try {
      const res = await fetch(t, {
        headers: { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" },
        redirect: "follow"
      });
      const body = await res.arrayBuffer();
      return new Response(body, {
        status: res.status,
        headers: {
          "Content-Type": res.headers.get("Content-Type") || "application/octet-stream",
          "Cache-Control": "public, max-age=120"
        }
      });
    } catch (e) {
      return new Response("upstream error", { status: 502 });
    }
  }
};
