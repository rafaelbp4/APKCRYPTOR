const { Bot, InputFile } = require("grammy");
const http = require("http");
const fs = require("fs");
const path = require("path");
const axios = require("axios");
const FormData = require("form-data");

// ─── Keepalive HTTP server (cron-job.org ping এর জন্য) ───────────────────────
const PORT = process.env.PORT || 3000;
const server = http.createServer((req, res) => {
  if (req.url === "/health" || req.url === "/ping") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ status: "ok", bot: "running", ts: Date.now() }));
  } else {
    res.writeHead(200, { "Content-Type": "text/plain" });
    res.end("🛡️ APK Protector Bot is alive!");
  }
});
server.listen(PORT, () => console.log(`🌐 Keepalive server: http://localhost:${PORT}`));
// ─────────────────────────────────────────────────────────────────────────────

const bot = new Bot(process.env.BOT_TOKEN);
const ENGINE_URL = process.env.ENGINE_URL || "http://localhost:8000";

// /start command
bot.command("start", async (ctx) => {
  await ctx.reply(
    `🛡️ *APK Protector Bot*\n\n` +
    `আমি তোমার APK কে protect করব:\n\n` +
    `✅ String Encryption (Fog)\n` +
    `✅ Anti-Tamper Protection\n` +
    `✅ Package Name Lock\n` +
    `✅ Native Libs (.so) Protection\n` +
    `✅ Resource Obfuscation\n\n` +
    `📤 শুধু .apk file পাঠাও — বাকিটা আমি করব!`,
    { parse_mode: "Markdown" }
  );
});

// /help command
bot.command("help", async (ctx) => {
  await ctx.reply(
    `📖 *কিভাবে ব্যবহার করবে:*\n\n` +
    `1️⃣ .apk file এই chat এ send করো\n` +
    `2️⃣ Protection options select করো\n` +
    `3️⃣ Protected APK download করো\n\n` +
    `⚠️ *Max file size:* 50MB\n` +
    `⏱️ *Processing time:* 1-3 minutes`,
    { parse_mode: "Markdown" }
  );
});

// Handle APK file upload
bot.on("message:document", async (ctx) => {
  const doc = ctx.message.document;

  // Check if it's an APK
  if (!doc.file_name?.endsWith(".apk") && doc.mime_type !== "application/vnd.android.package-archive") {
    return await ctx.reply("❌ শুধু .apk file পাঠাও!");
  }

  // Check file size (50MB limit)
  if (doc.file_size > 50 * 1024 * 1024) {
    return await ctx.reply("❌ File size 50MB এর বেশি! ছোট APK পাঠাও।");
  }

  const statusMsg = await ctx.reply("⏳ APK download করছি...");

  try {
    // Download APK from Telegram
    const fileLink = await ctx.api.getFile(doc.file_id);
    const fileUrl = `https://api.telegram.org/file/bot${process.env.BOT_TOKEN}/${fileLink.file_path}`;

    const response = await axios.get(fileUrl, { responseType: "arraybuffer" });
    const apkBuffer = Buffer.from(response.data);

    await ctx.api.editMessageText(ctx.chat.id, statusMsg.message_id, "🔧 Protection engine এ পাঠাচ্ছি...");

    // Send to Python engine
    const form = new FormData();
    form.append("file", apkBuffer, {
      filename: doc.file_name,
      contentType: "application/vnd.android.package-archive",
    });
    form.append("options", JSON.stringify({
      string_encryption: true,
      anti_tamper: true,
      package_lock: true,
      libs_protection: true,
      resource_obfuscation: true,
    }));

    await ctx.api.editMessageText(ctx.chat.id, statusMsg.message_id,
      "🔐 Protecting APK...\n\n" +
      "⚙️ String encryption...\n" +
      "🛡️ Anti-tamper injection...\n" +
      "📦 Package name lock...\n" +
      "🔩 Libs protection...\n" +
      "🎨 Resource obfuscation..."
    );

    const engineResponse = await axios.post(`${ENGINE_URL}/protect`, form, {
      headers: form.getHeaders(),
      responseType: "arraybuffer",
      timeout: 300000, // 5 min timeout
    });

    // Send protected APK back
    const protectedName = doc.file_name.replace(".apk", "_protected.apk");
    await ctx.api.editMessageText(ctx.chat.id, statusMsg.message_id, "📤 Sending protected APK...");

    await ctx.replyWithDocument(
      new InputFile(Buffer.from(engineResponse.data), protectedName),
      {
        caption:
          `✅ *Protection Complete!*\n\n` +
          `📦 File: \`${protectedName}\`\n` +
          `🔐 String Encryption: ✅\n` +
          `🛡️ Anti-Tamper: ✅\n` +
          `📌 Package Lock: ✅\n` +
          `🔩 Libs Protected: ✅\n` +
          `🎨 Resources Obfuscated: ✅`,
        parse_mode: "Markdown",
      }
    );

    await ctx.api.deleteMessage(ctx.chat.id, statusMsg.message_id);

  } catch (err) {
    console.error("Error:", err.message);
    await ctx.api.editMessageText(
      ctx.chat.id,
      statusMsg.message_id,
      `❌ Error হয়েছে: ${err.response?.data ? "Processing failed" : err.message}\n\nআবার try করো।`
    );
  }
});

// Error handler
bot.catch((err) => {
  console.error("Bot error:", err);
});

bot.start();
console.log("🤖 Bot started!");
