require('dotenv').config();
const express = require('express');
const cors = require('cors');
const { Telegraf, Markup } = require('telegraf');
const { Rcon } = require('rcon-client');

// ======== КОНФИГ ========
const {
  BOT_TOKEN,
  CHANNEL_ID,
  RCON_HOST,
  RCON_PORT,
  RCON_PASSWORD,
  PORT = 3001,
} = process.env;

if (!BOT_TOKEN || !CHANNEL_ID) {
  console.error('❌ BOT_TOKEN и CHANNEL_ID обязательны!');
  process.exit(1);
}

// ======== ИНИЦИАЛИЗАЦИЯ ========
const bot = new Telegraf(BOT_TOKEN);
const app = express();
const pendingReasons = new Map(); // messageId -> данные заявки

app.use(cors());
app.use(express.json());

// ======== RCON ========
async function addToWhitelist(nickname) {
  if (!RCON_HOST || !RCON_PASSWORD) {
    console.warn('⚠️ RCON не настроен');
    return '✅ симуляция';
  }
  const rcon = await Rcon.connect({
    host: RCON_HOST,
    port: parseInt(RCON_PORT || '25575'),
    password: RCON_PASSWORD,
  });
  const response = await rcon.send(`whitelist add ${nickname}`);
  await rcon.end();
  return response;
}

function escapeHtml(text) {
  if (!text) return '';
  return text.replace(/[&<>"]/g, c => ({
    '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'
  })[c]);
}

function formatApplication(data) {
  const source = data.source === 'Другое'
    ? `Другое: ${data.sourceOther || 'не указано'}`
    : data.source;
  return `
📋 <b>НОВАЯ ЗАЯВКА</b>
━━━━━━━━━━━━━━━━

🎮 <b>Никнейм:</b> <code>${escapeHtml(data.nickname)}</code>
🎂 <b>Возраст:</b> ${data.age} лет
🔍 <b>Откуда узнал:</b> ${escapeHtml(source)}
📝 <b>О себе:</b> ${escapeHtml(data.about)}

👤 <b>Telegram:</b> ${data.firstName || ''} ${data.lastName || ''}${data.username ? ` (@${data.username})` : ''}
🆔 <b>ID:</b> <code>${data.telegramId}</code>
━━━━━━━━━━━━━━━━
⏳ <i>Ожидает решения...</i>
  `.trim();
}

// ======== API: ПРИНЯТЬ ЗАЯВКУ ========
app.post('/api/application', async (req, res) => {
  try {
    const { nickname, age, source, sourceOther, about, telegramId, username, firstName, lastName } = req.body;

    if (!nickname || !/^[a-zA-Z0-9_]{2,16}$/.test(nickname))
      return res.status(400).json({ error: 'Некорректный никнейм' });
    if (!age || isNaN(age) || age < 5 || age > 120)
      return res.status(400).json({ error: 'Некорректный возраст' });
    if (!source) return res.status(400).json({ error: 'Укажите откуда узнали' });
    if (!about || about.length < 10)
      return res.status(400).json({ error: 'Минимум 10 символов о себе' });

    const appData = { nickname, age, source, sourceOther, about, telegramId, username, firstName, lastName };
    const messageText = formatApplication(appData);

    const sentMessage = await bot.telegram.sendMessage(
      CHANNEL_ID,
      messageText,
      {
        parse_mode: 'HTML',
        ...Markup.inlineKeyboard([
          [Markup.button.callback('✅ Принять', 'approve'),
           Markup.button.callback('❌ Отклонить', 'reject')],
        ]),
      }
    );

    pendingReasons.set(sentMessage.message_id.toString(), {
      userId: telegramId,
      nickname,
      username,
      firstName,
      lastName,
      channelMessageId: sentMessage.message_id,
    });

    console.log(`📨 Заявка от ${nickname} (ID: ${telegramId})`);
    res.json({ success: true, message: 'Заявка отправлена администрации!' });
  } catch (err) {
    console.error('❌ Ошибка:', err);
    res.status(500).json({ error: 'Ошибка сервера' });
  }
});

// ======== КНОПКИ В КАНАЛЕ ========
bot.on('callback_query', async (ctx) => {
  const { data, message } = ctx.callbackQuery;
  if (data === 'noop') return ctx.answerCbQuery();

  const messageId = message.message_id.toString();
  const appData = pendingReasons.get(messageId);
  if (!appData) {
    return ctx.answerCbQuery('❌ Заявка уже обработана.', { show_alert: true });
  }

  const { userId, nickname } = appData;

  if (data === 'approve') {
    try {
      await ctx.answerCbQuery('✅ Добавляю в вайтлист...');
      await addToWhitelist(nickname);

      await ctx.editMessageText(
        message.text.replace('⏳ Ожидает решения...', '✅ ОДОБРЕНО'),
        { parse_mode: 'HTML' }
      );
      await ctx.editMessageReplyMarkup({
        inline_keyboard: [[Markup.button.callback('✅ Принято ✓', 'noop')]]
      });

      await ctx.telegram.sendMessage(
        userId,
        `✅ <b>Заявка одобрена!</b>\n\n` +
        `🎮 Ваш ник <code>${escapeHtml(nickname)}</code> добавлен в вайтлист!\n\n` +
        `🌐 IP: <code>play.myserver.ru</code>\n` +
        `📦 Версия: 1.21.x Java\n\n` +
        `Добро пожаловать! 🎉`,
        { parse_mode: 'HTML' }
      );

      pendingReasons.delete(messageId);
      console.log(`✅ Заявка ${nickname} — ОДОБРЕНА`);
    } catch (err) {
      await ctx.answerCbQuery(`❌ Ошибка: ${err.message}`, { show_alert: true });
    }
  } else if (data === 'reject') {
    await ctx.answerCbQuery('📝 Введите причину отклонения...');

    await ctx.telegram.sendMessage(
      CHANNEL_ID,
      `📝 <b>Введите причину отклонения</b> для <code>${escapeHtml(nickname)}</code>\n` +
      `(или отправьте /cancel для отмены)`,
      {
        parse_mode: 'HTML',
        reply_to_message_id: message.message_id,
      }
    );

    pendingReasons.set(messageId, { ...appData, awaitingReason: true });
  }
});

// ======== ПРИЧИНА ОТКЛОНЕНИЯ ========
bot.on('text', async (ctx) => {
  if (!ctx.message.reply_to_message) return;
  const repliedMessageId = ctx.message.reply_to_message.message_id;

  for (const [msgId, data] of pendingReasons.entries()) {
    if (data.awaitingReason && data.channelMessageId === repliedMessageId) {
      const reason = ctx.message.text;
      const { userId, nickname } = data;

      try {
        await ctx.telegram.sendMessage(
          userId,
          `❌ <b>Заявка отклонена</b>\n\n` +
          `🎮 Ник: <code>${escapeHtml(nickname)}</code>\n` +
          `📋 Причина: <i>${escapeHtml(reason)}</i>\n\n` +
          `Вы можете подать заявку ещё раз, исправив ошибки.`,
          { parse_mode: 'HTML' }
        );

        await ctx.telegram.sendMessage(
          CHANNEL_ID,
          `❌ <b>Заявка отклонена</b>\n🎮 ${escapeHtml(nickname)}\n📋 Причина: ${escapeHtml(reason)}`,
          { parse_mode: 'HTML' }
        );

        try {
          await ctx.telegram.editMessageText(
            CHANNEL_ID, data.channelMessageId, null,
            `❌ <b>ЗАЯВКА ОТКЛОНЕНА</b>\n🎮 <code>${escapeHtml(nickname)}</code>\n📋 Причина: ${escapeHtml(reason)}`,
            { parse_mode: 'HTML' }
          );
          await ctx.telegram.editMessageReplyMarkup(
            CHANNEL_ID, data.channelMessageId, null,
            { inline_keyboard: [[Markup.button.callback('❌ Отклонено', 'noop')]] }
          );
        } catch (e) {}

        pendingReasons.delete(msgId);
        console.log(`❌ Заявка ${nickname} — ОТКЛОНЕНА. Причина: ${reason}`);
      } catch (err) {
        await ctx.reply(`❌ Не удалось отправить уведомление пользователю (ID: ${userId})`);
      }
      break;
    }
  }
});

bot.command('cancel', async (ctx) => {
  if (!ctx.message.reply_to_message) return;
  const repliedId = ctx.message.reply_to_message.message_id;
  for (const [msgId, data] of pendingReasons.entries()) {
    if (data.awaitingReason && data.channelMessageId === repliedId) {
      pendingReasons.delete(msgId);
      await ctx.reply('❌ Отмена.');
      break;
    }
  }
});

// ======== ЗАПУСК ========
async function start() {
  const botInfo = await bot.telegram.getMe();
  console.log(`🤖 Бот @${botInfo.username} запущен!`);

  try {
    const chat = await bot.telegram.getChat(CHANNEL_ID);
    console.log(`📢 Канал: ${chat.title} (${chat.id})`);
  } catch (e) {
    console.warn('⚠️ Проверьте CHANNEL_ID и права бота');
  }

  app.listen(PORT, () => {
    console.log(`🌐 Сервер на порту ${PORT}`);
    console.log(`📝 POST http://localhost:${PORT}/api/application`);
  });

  bot.launch();
}

start();

process.once('SIGINT', () => { bot.stop('SIGINT'); process.exit(0); });
process.once('SIGTERM', () => { bot.stop('SIGTERM'); process.exit(0); });
