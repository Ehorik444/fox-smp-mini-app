/**
 * Minecraft Whitelist Telegram Mini App
 * Один JS файл — вся логика + генерация HTML + стили
 * 
 * Использование:
 * 1. Создать index.html с <script src="whitelist-app.js"></script>
 * 2. Или вставить в любую страницу как <script>
 * 3. Поменять API_URL на свой бэкенд
 */

(function() {
    'use strict';

    // =============================================
    // КОНФИГУРАЦИЯ
    // =============================================
    const CONFIG = {
        API_URL: 'https://your-backend.com',      // <-- ЗАМЕНИТЬ
        SERVER_IP: 'play.myserver.ru',
        SERVER_VERSION: '1.21.x',
        SERVER_TYPE: 'Ванильный',
    };

    const STEPS = [
        { title: 'Никнейм', icon: '🎮', desc: 'Ваш никнейм в Minecraft (латиница, до 16 символов)' },
        { title: 'Возраст', icon: '🎂', desc: 'Укажите ваш возраст для допуска к игре' },
        { title: 'Откуда узнал', icon: '🔍', desc: 'Расскажите, как вы нашли наш сервер' },
        { title: 'О себе', icon: '📝', desc: 'Напишите пару слов о себе для администрации' },
    ];

    const SOURCES = [
        '', '👥 Друзья', '▶️ YouTube', '🎵 TikTok',
        '💬 VK / Discord', '🌐 Поисковик', '📢 Реклама', '📌 Другое'
    ];

    // =============================================
    // СОСТОЯНИЕ
    // =============================================
    const state = {
        step: 1,
        status: 'idle', // idle | loading | success | error
        error: null,
        form: { nickname: '', age: '', source: '', sourceOther: '', about: '' },
        tg: null,
        tgUser: null,
    };

    // =============================================
    // TELEGRAM SDK
    // =============================================
    function initTelegram() {
        try {
            if (window.Telegram?.WebApp) {
                state.tg = window.Telegram.WebApp;
                state.tg.ready();
                state.tg.expand();
                state.tgUser = state.tg.initDataUnsafe?.user || null;

                const t = state.tg.themeParams || {};
                const r = document.documentElement;
                if (t.bg_color) r.style.setProperty('--bg', t.bg_color);
                if (t.text_color) r.style.setProperty('--text', t.text_color);
                if (t.button_color) r.style.setProperty('--btn', t.button_color);
                if (t.button_text_color) r.style.setProperty('--btn-text', t.button_text_color);
                if (t.secondary_bg_color) r.style.setProperty('--secondary', t.secondary_bg_color);
            }
        } catch (e) {
            console.warn('Telegram WebApp not available, running standalone');
        }
    }

    function haptic(type) {
        try {
            if (state.tg?.HapticFeedback) {
                if (type === 'light') state.tg.HapticFeedback.impactOccurred('light');
                if (type === 'success') state.tg.HapticFeedback.notificationOccurred('success');
                if (type === 'error') state.tg.HapticFeedback.notificationOccurred('error');
            }
        } catch (e) {}
    }

    // =============================================
    // ВАЛИДАЦИЯ
    // =============================================
    function isValid(step) {
        const f = state.form;
        switch (step) {
            case 1: return /^[a-zA-Z0-9_]{2,16}$/.test(f.nickname.trim());
            case 2: {
                const a = Number(f.age);
                return f.age.trim() !== '' && !isNaN(a) && a >= 5 && a <= 120;
            }
            case 3: return f.source.trim().length >= 2;
            case 4: return f.about.trim().length >= 10;
            default: return false;
        }
    }

    // =============================================
    // ЧТЕНИЕ ПОЛЕЙ
    // =============================================
    function readFields() {
        const byId = (id) => document.getElementById('mc-' + id);
        if (state.step === 1) state.form.nickname = (byId('nick')?.value || '').trim();
        if (state.step === 2) state.form.age = (byId('age')?.value || '').trim();
        if (state.step === 3) {
            state.form.source = byId('source')?.value || '';
            state.form.sourceOther = (byId('source-other')?.value || '').trim();
        }
        if (state.step === 4) state.form.about = (byId('about')?.value || '').trim();
    }

    // =============================================
    // ГЕНЕРАЦИЯ СТИЛЕЙ
    // =============================================
    function injectStyles() {
        if (document.getElementById('mc-styles')) return;

        const css = document.createElement('style');
        css.id = 'mc-styles';
        css.textContent = `
            :root {
                --bg: #ffffff; --text: #000000; --hint: #999999;
                --btn: #3390ec; --btn-text: #ffffff; --secondary: #efeff3;
                --green: #4ade80; --dark: #22c55e; --red: #ef4444;
            }
            #mc-app { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: var(--bg); color: var(--text);
                min-height: 100vh; margin: 0; padding: 0; user-select: none;
                -webkit-tap-highlight-color: transparent;
                max-width: 480px; margin: 0 auto;
            }
            #mc-app * { box-sizing: border-box; margin: 0; padding: 0; }
            .mc-hdr {
                background: linear-gradient(135deg,#1a1a2e,#16213e,#0f3460);
                padding: 28px 20px 44px; border-radius: 0 0 28px 28px; position: relative; overflow: hidden;
            }
            .mc-hdr::before {
                content: ''; position: absolute; inset: 0; pointer-events: none;
                background: repeating-linear-gradient(45deg,transparent,transparent 28px,rgba(255,255,255,0.03) 28px,rgba(255,255,255,0.03) 56px);
            }
            .mc-hdr-inner { position: relative; z-index: 1; display: flex; align-items: center; gap: 12px; }
            .mc-hdr-icon {
                width: 46px; height: 46px; background: var(--green); border-radius: 14px;
                display: flex; align-items: center; justify-content: center; font-size: 22px;
                box-shadow: 0 6px 16px rgba(74,222,128,0.3); flex-shrink: 0;
            }
            .mc-hdr h1 { color: #fff; font-size: 19px; font-weight: 800; letter-spacing: -0.3px; }
            .mc-hdr-status { display: flex; align-items: center; gap: 5px; margin-top: 2px; }
            .mc-dot {
                width: 6px; height: 6px; background: var(--green); border-radius: 50%;
                animation: mcpulse 2s infinite;
            }
            @keyframes mcpulse { 0%,100%{opacity:1} 50%{opacity:.4} }
            .mc-hdr-status span { color: rgba(255,255,255,0.55); font-size: 11px; }
            
            .mc-main { padding: 0 14px; margin-top: -22px; position: relative; z-index: 2; }
            
            .mc-progress {
                background: var(--secondary); border-radius: 14px; padding: 14px;
                margin-bottom: 14px; border: 1px solid rgba(0,0,0,0.04);
            }
            .mc-prog-steps { display: flex; justify-content: space-between; margin-bottom: 10px; }
            .mc-prog-step { display: flex; flex-direction: column; align-items: center; flex: 1; }
            .mc-prog-c {
                width: 32px; height: 32px; border-radius: 10px; display: flex;
                align-items: center; justify-content: center; font-size: 12px; font-weight: 700;
                transition: all .3s; border: 1px solid rgba(0,0,0,0.07);
                background: var(--bg); color: var(--hint);
            }
            .mc-prog-c.active { background: var(--btn); color: var(--btn-text); border: none; transform: scale(1.1); box-shadow: 0 3px 10px rgba(51,144,236,0.3); }
            .mc-prog-c.done { background: var(--dark); color: #fff; border: none; }
            .mc-prog-lbl { font-size: 8px; margin-top: 3px; font-weight: 500; transition: color .2s; color: var(--hint); }
            .mc-prog-lbl.active { color: var(--btn); }
            .mc-prog-lbl.done { color: var(--dark); }
            .mc-prog-bar { height: 3px; background: var(--bg); border-radius: 3px; overflow: hidden; }
            .mc-prog-fill {
                height: 100%; background: linear-gradient(90deg,var(--btn),var(--green));
                border-radius: 3px; transition: width .4s cubic-bezier(.4,0,.2,1); width: 0%;
            }

            .mc-card {
                background: var(--bg); border-radius: 14px; padding: 18px;
                border: 1px solid rgba(0,0,0,0.04); margin-bottom: 14px;
                animation: mcslide .3s ease-out;
            }
            @keyframes mcslide { from{opacity:0;transform:translateX(20px)} to{opacity:1;transform:translateX(0)} }
            .mc-card h2 { font-size: 18px; font-weight: 700; margin-bottom: 2px; }
            .mc-card .mc-desc { font-size: 12px; color: var(--hint); margin-bottom: 14px; }
            
            .mc-field { position: relative; margin-bottom: 14px; }
            .mc-field-icon { position: absolute; left: 12px; top: 50%; transform: translateY(-50%); font-size: 16px; pointer-events: none; z-index: 1; }
            
            .mc-input, .mc-select, .mc-textarea {
                width: 100%; background: var(--secondary); border: none;
                border-radius: 10px; padding: 14px 14px 14px 40px; font-size: 14px;
                color: var(--text); outline: none; transition: box-shadow .15s;
                font-family: inherit;
            }
            .mc-input:focus, .mc-select:focus, .mc-textarea:focus { box-shadow: 0 0 0 2px var(--btn); }
            .mc-input:disabled, .mc-select:disabled, .mc-textarea:disabled { opacity: .5; }
            .mc-input::placeholder, .mc-textarea::placeholder { color: var(--hint); }
            .mc-textarea { padding: 14px; min-height: 110px; resize: none; line-height: 1.5; }
            .mc-select {
                appearance: none; padding-right: 36px;
                background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='10' viewBox='0 0 10 10'%3E%3Cpath fill='%23999' d='M5 7L1 3h8z'/%3E%3C/svg%3E");
                background-repeat: no-repeat; background-position: right 12px center;
            }
            .mc-extra { margin-top: 6px; }
            .mc-extra .mc-input { padding: 10px 14px; font-size: 13px; }
            
            .mc-valid { font-size: 11px; margin-top: 3px; display: flex; align-items: center; gap: 3px; }
            .mc-valid.err { color: var(--red); }
            .mc-valid.ok { color: var(--dark); }
            .mc-count { display: flex; justify-content: space-between; font-size: 10px; color: var(--hint); margin-top: 3px; }

            .mc-btns { display: flex; gap: 10px; margin-top: 18px; }
            .mc-btn {
                flex: 1; border: none; border-radius: 10px; padding: 14px; font-size: 13px;
                font-weight: 700; cursor: pointer; transition: all .15s; font-family: inherit;
                background: var(--secondary); color: var(--text);
            }
            .mc-btn:active:not(:disabled) { transform: scale(.97); }
            .mc-btn:disabled { opacity: .4; cursor: not-allowed; }
            .mc-btn-primary { background: var(--btn); color: var(--btn-text); box-shadow: 0 3px 10px rgba(51,144,236,.2); }
            .mc-btn-green { background: var(--dark); color: #fff; box-shadow: 0 3px 10px rgba(34,197,94,.2); }
            .mc-spinner {
                width: 18px; height: 18px; border: 2px solid rgba(255,255,255,.3);
                border-top-color: #fff; border-radius: 50%; animation: mcspin .7s linear infinite;
            }
            @keyframes mcspin { to { transform: rotate(360deg); } }
            
            .mc-err {
                margin-top: 10px; background: #fef2f2; border: 1px solid #fecaca;
                padding: 10px 12px; border-radius: 10px; font-size: 12px; color: #991b1b;
                display: flex; align-items: flex-start; gap: 6px;
            }

            .mc-success {
                background: #f0fdf4; border: 2px solid #bbf7d0; border-radius: 20px;
                padding: 28px 20px; text-align: center; margin-bottom: 14px;
                animation: mcfade .35s ease-out;
            }
            @keyframes mcfade { from{opacity:0;transform:scale(.95)} to{opacity:1;transform:scale(1)} }
            .mc-succ-icon {
                width: 80px; height: 80px; background: var(--dark); border-radius: 50%;
                display: flex; align-items: center; justify-content: center;
                font-size: 36px; margin: 0 auto 14px;
                box-shadow: 0 6px 20px rgba(34,197,94,.25);
            }
            .mc-success h2 { font-size: 20px; color: #166534; margin-bottom: 4px; }
            .mc-success p { font-size: 13px; color: #15803d; line-height: 1.5; }
            .mc-summary {
                background: #dcfce7; border-radius: 10px; padding: 14px; text-align: left;
                font-size: 12px; color: #166534; line-height: 1.8; margin: 14px 0;
            }
            .mc-summary b { font-weight: 600; }
            .mc-link {
                background: none; border: none; color: var(--dark); font-size: 12px;
                font-weight: 600; cursor: pointer; text-decoration: underline; padding: 6px;
            }

            .mc-info {
                background: var(--secondary); border-radius: 14px; padding: 14px;
                border: 1px solid rgba(0,0,0,0.04);
            }
            .mc-info-row { display: flex; justify-content: space-between; align-items: center; }
            .mc-info-l { display: flex; align-items: center; gap: 6px; font-size: 13px; font-weight: 700; }
            .mc-info-r { display: flex; align-items: center; gap: 3px; font-size: 11px; color: var(--dark); font-weight: 500; }
            .mc-tags { display: flex; gap: 10px; margin-top: 6px; font-size: 10px; color: var(--hint); }
        `;
        document.head.appendChild(css);
    }

    // =============================================
    // ГЕНЕРАЦИЯ HTML
    // =============================================
    function escape(s) {
        if (!s) return '';
        return String(s).replace(/[&<>'"]/g, c => ({
            '&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#039;','"':'&quot;'
        })[c]);
    }

    function render() {
        const app = document.getElementById('mc-app');
        if (!app) return;

        const isSuccess = state.status === 'success';
        const isLoading = state.status === 'loading';

        // Header
        let html = `
            <div class="mc-hdr">
                <div class="mc-hdr-inner">
                    <div class="mc-hdr-icon">⛏️</div>
                    <div>
                        <h1>Minecraft Server</h1>
                        <div class="mc-hdr-status">
                            <div class="mc-dot"></div>
                            <span>Сервер онлайн · ${CONFIG.SERVER_IP}</span>
                        </div>
                    </div>
                </div>
            </div>
            <div class="mc-main">
        `;

        // Progress
        html += `<div class="mc-progress"><div class="mc-prog-steps">`;
        STEPS.forEach((s, i) => {
            const idx = i + 1;
            const active = state.step === idx;
            const done = state.step > idx;
            const cls = active ? 'active' : done ? 'done' : '';
            html += `
                <div class="mc-prog-step">
                    <div class="mc-prog-c ${cls}">${done ? '✓' : s.icon}</div>
                    <span class="mc-prog-lbl ${cls}">${s.title}</span>
                </div>
            `;
        });
        html += `</div><div class="mc-prog-bar"><div class="mc-prog-fill" style="width:${((state.step-1)/3)*100}%"></div></div></div>`;

        // Content
        if (isSuccess) {
            const src = state.form.source === 'Другое' ? (state.form.sourceOther || 'Другое') : state.form.source;
            html += `
                <div class="mc-success">
                    <div class="mc-succ-icon">✅</div>
                    <h2>Заявка отправлена!</h2>
                    <p>Ваша заявка отправлена администрации сервера.<br>Ожидайте решения — вам придёт уведомление в Telegram.</p>
                    <div class="mc-summary">
                        <b>🎮 Ник:</b> ${escape(state.form.nickname)}<br>
                        <b>🎂 Возраст:</b> ${escape(state.form.age)} лет<br>
                        <b>🔍 Откуда:</b> ${escape(src)}
                    </div>
                    <button class="mc-link" onclick="window.__mcReset()">Подать новую заявку</button>
                </div>
            `;
        } else {
            const s = STEPS[state.step - 1];
            let content = '';

            // Step 1 - Nickname
            if (state.step === 1) {
                let v = '';
                if (state.form.nickname) {
                    v = /^[a-zA-Z0-9_]{2,16}$/.test(state.form.nickname)
                        ? '<div class="mc-valid ok">✅ Никнейм валидный</div>'
                        : '<div class="mc-valid err">⚠️ Только латиница, цифры и _, от 2 до 16 символов</div>';
                }
                content = `
                    <div class="mc-field">
                        <div class="mc-field-icon">🎮</div>
                        <input class="mc-input" id="mc-nick" type="text" 
                               value="${escape(state.form.nickname)}" placeholder="Введите никнейм..."
                               maxlength="16" ${isLoading?'disabled':''} autofocus>
                    </div>
                    ${v}
                `;
            }

            // Step 2 - Age
            if (state.step === 2) {
                let v = '';
                if (state.form.age && (Number(state.form.age) < 5 || Number(state.form.age) > 120)) {
                    v = '<div class="mc-valid err">⚠️ Укажите корректный возраст (5-120)</div>';
                }
                content = `
                    <div class="mc-field">
                        <div class="mc-field-icon">🎂</div>
                        <input class="mc-input" id="mc-age" type="number"
                               value="${escape(state.form.age)}" placeholder="Ваш возраст..."
                               min="5" max="120" ${isLoading?'disabled':''} autofocus>
                    </div>
                    ${v}
                `;
            }

            // Step 3 - Source
            if (state.step === 3) {
                let opts = '';
                SOURCES.forEach(v => {
                    const val = v.replace(/^[^\s]+\s/, '');
                    const label = v || 'Выберите вариант...';
                    const sel = state.form.source === val ? 'selected' : '';
                    opts += `<option value="${escape(val)}" ${sel}>${label}</option>`;
                });
                let extra = '';
                if (state.form.source === 'Другое') {
                    extra = `
                        <div class="mc-extra">
                            <input class="mc-input" id="mc-source-other" type="text"
                                   value="${escape(state.form.sourceOther)}"
                                   placeholder="Уточните..." ${isLoading?'disabled':''}>
                        </div>
                    `;
                }
                content = `
                    <div class="mc-field">
                        <div class="mc-field-icon">🔍</div>
                        <select class="mc-select" id="mc-source" ${isLoading?'disabled':''} autofocus>${opts}</select>
                    </div>
                    ${extra}
                `;
            }

            // Step 4 - About
            if (state.step === 4) {
                const len = state.form.about.length;
                content = `
                    <div class="mc-field">
                        <textarea class="mc-textarea" id="mc-about" rows="5" maxlength="500"
                                  ${isLoading?'disabled':''} autofocus
                            placeholder="Расскажите о себе: опыт в Minecraft, почему хотите играть у нас...">${escape(state.form.about)}</textarea>
                    </div>
                    <div class="mc-count">
                        <span>${len>=10?'✅':'⚠️'} Минимум 10 символов</span>
                        <span>${len}/500</span>
                    </div>
                `;
            }

            // Buttons
            let btns = '';
            if (state.step > 1) {
                btns += `<button class="mc-btn" onclick="window.__mcPrev()" ${isLoading?'disabled':''}>← Назад</button>`;
            }
            if (state.step < 4) {
                btns += `<button class="mc-btn mc-btn-primary" onclick="window.__mcNext()" ${!isValid(state.step)||isLoading?'disabled':''}>Далее →</button>`;
            } else {
                btns += `<button class="mc-btn mc-btn-green" onclick="window.__mcSubmit()" ${!isValid(4)||isLoading?'disabled':''}>
                    ${isLoading ? '<span class="mc-spinner"></span> Отправка...' : 'Отправить заявку'}
                </button>`;
            }

            let errHtml = '';
            if (state.error) {
                errHtml = `<div class="mc-err"><span>⚠️</span><span>${escape(state.error)}</span></div>`;
            }

            html += `
                <div class="mc-card">
                    <h2>${s.icon} ${s.title}</h2>
                    <div class="mc-desc">${s.desc}</div>
                    ${content}
                    <div class="mc-btns">${btns}</div>
                    ${errHtml}
                </div>
            `;
        }

        // Server Info
        html += `
            <div class="mc-info">
                <div class="mc-info-row">
                    <div class="mc-info-l"><span>🎮</span><span>${CONFIG.SERVER_IP}</span></div>
                    <div class="mc-info-r"><div class="mc-dot"></div> Online</div>
                </div>
                <div class="mc-tags">
                    <span>📦 ${CONFIG.SERVER_VERSION}</span>
                    <span>🏆 ${CONFIG.SERVER_TYPE}</span>
                    <span>👥 Whitelist</span>
                </div>
            </div>
        `;

        html += '</div>';
        app.innerHTML = html;

        if (!isSuccess) {
            setTimeout(() => {
                const ids = ['mc-nick', 'mc-age', 'mc-source', 'mc-about'];
                document.getElementById(ids[state.step - 1])?.focus();
            }, 50);
        }
    }

    // =============================================
    // ДЕЙСТВИЯ
    // =============================================
    window.__mcNext = function() {
        readFields();
        if (!isValid(state.step) || state.step >= 4) return;
        state.step++;
        haptic('light');
        render();
    };

    window.__mcPrev = function() {
        readFields();
        if (state.step <= 1) return;
        state.step--;
        haptic('light');
        render();
    };

    window.__mcSubmit = async function() {
        readFields();
        if (!isValid(4) || state.status === 'loading') return;

        state.status = 'loading';
        state.error = null;
        render();

        try {
            const res = await fetch(CONFIG.API_URL + '/api/application', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ...state.form,
                    telegramId: state.tgUser?.id || 0,
                    username: state.tgUser?.username || '',
                    firstName: state.tgUser?.first_name || '',
                    lastName: state.tgUser?.last_name || '',
                }),
            });

            if (!res.ok) {
                const data = await res.json().catch(() => ({}));
                throw new Error(data.error || 'Ошибка сервера');
            }

            state.status = 'success';
            haptic('success');
            render();
        } catch (err) {
            state.status = 'idle';
            state.error = err.message || 'Ошибка соединения. Попробуйте позже.';
            haptic('error');
            render();
        }
    };

    window.__mcReset = function() {
        state.step = 1;
        state.status = 'idle';
        state.error = null;
        state.form = { nickname: '', age: '', source: '', sourceOther: '', about: '' };
        render();
    };

    // Enter key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && state.status !== 'success') {
            e.preventDefault();
            if (state.step < 4) window.__mcNext();
            else window.__mcSubmit();
        }
    });

    // =============================================
    // ЗАПУСК
    // =============================================
    function init() {
        let app = document.getElementById('mc-app');
        if (!app) {
            app = document.createElement('div');
            app.id = 'mc-app';
            document.body.appendChild(app);
        }
        injectStyles();
        initTelegram();
        render();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
