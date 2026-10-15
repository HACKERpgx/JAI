/* Attach the existing Supabase session to API calls that require authentication. */
(function () {
  "use strict";

  const protectedPrefixes = [
    "/api/autonomous",
    "/api/email",
    "/api/auto-reply",
    "/api/integrations",
    "/api/security",
  ];
  const originalFetch = window.fetch.bind(window);
  let clientPromise;

  function isProtectedRequest(input) {
    try {
      const url = new URL(typeof input === "string" ? input : input.url, window.location.href);
      const sameSiteHost = url.hostname === window.location.hostname ||
        url.hostname === "j-ai.top" || url.hostname === "www.j-ai.top";
      return sameSiteHost && protectedPrefixes.some((prefix) =>
        url.pathname === prefix || url.pathname.startsWith(prefix + "/")
      );
    } catch (_) {
      return false;
    }
  }

  async function getSupabaseClient() {
    if (!clientPromise) {
      clientPromise = (async function () {
        const response = await originalFetch("/api/auth/config", { cache: "no-store" });
        if (!response.ok) throw new Error("Authentication configuration unavailable");
        const config = await response.json();
        if (!config.enabled || !config.supabase_url || !config.supabase_anon_key) {
          throw new Error("Authentication is not configured");
        }
        if (!window.supabase || !window.supabase.createClient) {
          await new Promise((resolve, reject) => {
            const script = document.createElement("script");
            script.src = "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.47.10/dist/umd/supabase.min.js";
            script.onload = resolve;
            script.onerror = () => reject(new Error("Authentication client unavailable"));
            document.head.appendChild(script);
          });
        }
        return window.supabase.createClient(config.supabase_url, config.supabase_anon_key, {
          auth: { autoRefreshToken: true, persistSession: true, detectSessionInUrl: true },
        });
      })();
    }
    return clientPromise;
  }

  window.fetch = async function (input, init) {
    if (!isProtectedRequest(input)) return originalFetch(input, init);
    try {
      const client = await getSupabaseClient();
      const { data, error } = await client.auth.getSession();
      const accessToken = data && data.session && data.session.access_token;
      if (error || !accessToken) throw new Error("Sign in is required");
      const headers = new Headers((init && init.headers) || (input instanceof Request ? input.headers : undefined));
      headers.set("Authorization", "Bearer " + accessToken);
      return originalFetch(input, Object.assign({}, init || {}, { headers }));
    } catch (_) {
      return new Response(JSON.stringify({ detail: "Sign in on the JAI home page to use this feature." }), {
        status: 401,
        headers: { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" },
      });
    }
  };
})();
