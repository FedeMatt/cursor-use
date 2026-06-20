import PostalMime from "postal-mime";

/** @param {string} from @param {string} allowedCsv */
function senderAllowed(from, allowedCsv) {
  const list = allowedCsv
    .split(",")
    .map((s) => s.trim().toLowerCase())
    .filter(Boolean);
  if (!list.length) return true;
  const addr = from.toLowerCase();
  return list.some((a) => addr.includes(a));
}

/** @param {string} name */
function safeFilename(name) {
  return (name || "statement.pdf").replace(/[^\w.-]+/g, "_");
}

export default {
  /**
   * @param {import("cloudflare:workers").ForwardableEmailMessage} message
   * @param {Env} env
   */
  async email(message, env) {
    if (!senderAllowed(message.from, env.ALLOWED_FROM || "")) {
      message.setReject("Sender not allowed");
      return;
    }

    const raw = await new Response(message.raw).arrayBuffer();
    const parsed = await PostalMime.parse(raw);
    const prefix = (env.R2_PREFIX || "credit-card-bills/").replace(/\/?$/, "/");
    const date = new Date().toISOString().slice(0, 10);
    let saved = 0;

    for (const att of parsed.attachments || []) {
      const name = att.filename || "";
      if (!name.toLowerCase().endsWith(".pdf")) continue;
      const key = `${prefix}${date}_${safeFilename(name)}`;
      await env.BILLS.put(key, att.content, {
        httpMetadata: { contentType: att.mimeType || "application/pdf" },
      });
      saved++;
    }

    if (saved === 0) {
      message.setReject("No PDF attachment found");
    }
  },
};

/** @typedef {{ BILLS: R2Bucket; R2_PREFIX?: string; ALLOWED_FROM?: string }} Env */
