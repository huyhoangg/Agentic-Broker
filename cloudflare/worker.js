// Cloudflare Worker - TikTok Live Monitor & Cloudflare Workers AI Whisper STT
export default {
  // Cron Trigger handler (Tự động thức dậy kiểm tra TikTok Live)
  async scheduled(event, env, ctx) {
    console.log("⏰ Cloudflare Cron Trigger: Kiểm tra TikTok Live...");
    await checkTikTokLiveAndNotify(env);
  },

  // HTTP Request handler (Truy cập thử nghiệm qua URL)
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (url.pathname === "/check") {
      const result = await checkTikTokLiveAndNotify(env);
      return new Response(JSON.stringify(result, null, 2), {
        headers: { "content-type": "application/json;charset=UTF-8" }
      });
    }

    return new Response("🤖 Cloudflare TikTok Live Broker Assistant is Running!", { status: 200 });
  }
};

async function checkTikTokLiveAndNotify(env) {
  const targetChannel = env.TIKTOK_CHANNEL || "@vtv24";
  const cleanChannel = targetChannel.replace("@", "");
  const tiktokUrl = `https://www.tiktok.com/@${cleanChannel}/live`;

  try {
    const response = await fetch(tiktokUrl, {
      headers: {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
      }
    });

    const htmlText = await response.text();
    const isLive = htmlText.includes('"liveRoom"') || htmlText.includes('room_id') || htmlText.includes('"status":2');

    if (isLive) {
      const alertMsg = `🔴 <b>CLOUDFLARE ALERT: PHÁT HIỆN LIVESREAM</b>\n\n👤 Broker: <b>${targetChannel}</b>\n⏰ Thời gian: <code>${new Date().toLocaleTimeString('vi-VN')}</code>\n🟢 Kênh đang phát Live trên TikTok!`;
      await sendTelegram(env, alertMsg);
      return { status: "LIVE", channel: targetChannel };
    } else {
      return { status: "OFFLINE", channel: targetChannel };
    }
  } catch (error) {
    return { status: "ERROR", error: error.message };
  }
}

async function sendTelegram(env, text) {
  if (!env.TELEGRAM_BOT_TOKEN || !env.TELEGRAM_CHAT_ID) return;
  const url = `https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMessage`;
  await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      chat_id: env.TELEGRAM_CHAT_ID,
      text: text,
      parse_mode: "HTML"
    })
  });
}
