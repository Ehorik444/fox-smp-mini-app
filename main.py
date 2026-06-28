import { useEffect, useState } from 'react';
import WebApp from '@twa-dev/sdk';
import { motion, AnimatePresence } from 'framer-motion';

// Иконка Minecraft
const IconMinecraft = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-6 h-6">
    <path d="M12 2L2 7v10l10 5 10-5V7l-10-5z" />
    <path d="M12 12l-6-3v6l6 3 6-3v-6l-6 3z" />
    <path d="M4 7l8 4 8-4" />
  </svg>
);

type Step = 1 | 2 | 3 | 4;
type SubmitStatus = 'idle' | 'loading' | 'success' | 'error';

interface FormData {
  nickname: string;
  age: string;
  source: string;
  sourceOther: string;
  about: string;
}

const defaultForm: FormData = {
  nickname: '',
  age: '',
  source: '',
  sourceOther: '',
  about: '',
};

const MC_SERVER_IP = 'play.myserver.ru';
const API_URL = import.meta.env.VITE_API_URL || 'https://your-backend-url.com';

export default function App() {
  const [step, setStep] = useState<Step>(1);
  const [form, setForm] = useState<FormData>(defaultForm);
  const [status, setStatus] = useState<SubmitStatus>('idle');
  const [error, setError] = useState<string | null>(null);
  const [user, setUser] = useState<any>(null);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    WebApp.ready();
    WebApp.expand();
    setUser(WebApp.initDataUnsafe.user);

    const theme = WebApp.themeParams;
    if (theme.bg_color) document.documentElement.style.setProperty('--tg-theme-bg-color', theme.bg_color);
    if (theme.text_color) document.documentElement.style.setProperty('--tg-theme-text-color', theme.text_color);
    if (theme.button_color) document.documentElement.style.setProperty('--tg-theme-button-color', theme.button_color);
    if (theme.button_text_color) document.documentElement.style.setProperty('--tg-theme-button-text-color', theme.button_text_color);
    if (theme.secondary_bg_color) document.documentElement.style.setProperty('--tg-theme-secondary-bg-color', theme.secondary_bg_color);
  }, []);

  const updateField = (field: keyof FormData, value: string) => {
    setForm(prev => ({ ...prev, [field]: value }));
  };

  const nextStep = () => {
    if (step < 4) {
      setStep((step + 1) as Step);
      setProgress(step * 25);
      WebApp.HapticFeedback.impactOccurred('light');
    }
  };

  const prevStep = () => {
    if (step > 1) {
      setStep((step - 1) as Step);
      setProgress((step - 2) * 25);
      WebApp.HapticFeedback.impactOccurred('light');
    }
  };

  const handleSubmit = async () => {
    setStatus('loading');
    setError(null);

    try {
      const response = await fetch(`${API_URL}/api/application`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...form,
          telegramId: user?.id || 0,
          username: user?.username || '',
          firstName: user?.first_name || '',
          lastName: user?.last_name || '',
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Ошибка сервера');
      }

      setStatus('success');
      WebApp.HapticFeedback.notificationOccurred('success');
    } catch (err: any) {
      setStatus('error');
      setError(err.message || 'Ошибка соединения. Попробуйте позже.');
      WebApp.HapticFeedback.notificationOccurred('error');
    }
  };

  const stepTitles = ['Никнейм', 'Возраст', 'Откуда узнал', 'О себе'];
  const stepIcons = ['🎮', '🎂', '🔍', '📝'];

  const isStepValid = (s: Step): boolean => {
    switch (s) {
      case 1: return form.nickname.trim().length >= 2 && /^[a-zA-Z0-9_]{2,16}$/.test(form.nickname.trim());
      case 2: return form.age.trim().length > 0 && !isNaN(Number(form.age)) && Number(form.age) >= 5 && Number(form.age) <= 120;
      case 3: return form.source.trim().length >= 2;
      case 4: return form.about.trim().length >= 10;
      default: return false;
    }
  };

  return (
    <div className="min-h-screen bg-[var(--tg-theme-bg-color,#fff)] text-[var(--tg-theme-text-color,#000)] font-sans">
      
      {/* Header */}
      <div className="relative bg-gradient-to-br from-[#1a1a2e] via-[#16213e] to-[#0f3460] px-5 pt-8 pb-12 rounded-b-[2rem]">
        <div className="absolute top-0 left-0 right-0 h-full opacity-10">
          <div className="absolute inset-0" style={{ backgroundImage: 'url("data:image/svg+xml,%3Csvg width=\'60\' height=\'60\' viewBox=\'0 0 60 60\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cg fill=\'none\' fill-rule=\'evenodd\'%3E%3Cg fill=\'%23ffffff\' fill-opacity=\'0.08\'%3E%3Cpath d=\'M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z\'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")' }}></div>
        </div>
        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-12 h-12 bg-green-500 rounded-2xl flex items-center justify-center shadow-lg shadow-green-500/30">
              <IconMinecraft />
            </div>
            <div>
              <h1 className="text-white text-xl font-extrabold tracking-tight">Minecraft Server</h1>
              <div className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
                <span className="text-green-300 text-xs">Сервер онлайн • </span>
                <span className="text-white/50 text-xs">{MC_SERVER_IP}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <main className="px-4 -mt-6 relative z-20 space-y-4 pb-8">
        {/* Progress Steps */}
        <div className="bg-[var(--tg-theme-secondary-bg-color,#f0f0f5)] rounded-2xl p-4 shadow-sm border border-black/5">
          <div className="flex justify-between mb-3">
            {stepTitles.map((title, i) => {
              const s = (i + 1) as Step;
              const isActive = step === s;
              const isDone = step > s;
              return (
                <div key={i} className="flex flex-col items-center flex-1">
                  <div 
                    className={`
                      w-9 h-9 rounded-xl flex items-center justify-center text-sm font-bold transition-all duration-300
                      ${isActive ? 'bg-[var(--tg-theme-button-color,#3390ec)] text-white shadow-lg scale-110' : ''}
                      ${isDone ? 'bg-green-500 text-white' : ''}
                      ${!isActive && !isDone ? 'bg-[var(--tg-theme-bg-color,#fff)] text-[var(--tg-theme-hint-color,#999)] border border-black/10' : ''}
                    `}
                  >
                    {isDone ? '✓' : stepIcons[i]}
                  </div>
                  <span className={`
                    text-[10px] mt-1 font-medium transition-colors
                    ${isActive ? 'text-[var(--tg-theme-button-color,#3390ec)]' : ''}
                    ${isDone ? 'text-green-500' : ''}
                    ${!isActive && !isDone ? 'text-[var(--tg-theme-hint-color,#999)]' : ''}
                  `}>
                    {title}
                  </span>
                </div>
              );
            })}
          </div>
          {/* Progress bar */}
          <div className="h-1 bg-[var(--tg-theme-bg-color,#fff)] rounded-full overflow-hidden">
            <motion.div 
              className="h-full bg-gradient-to-r from-[var(--tg-theme-button-color,#3390ec)] to-green-500 rounded-full"
              animate={{ width: `${progress}%` }}
              transition={{ type: 'spring', stiffness: 300, damping: 30 }}
            />
          </div>
        </div>

        {/* Step Content */}
        <AnimatePresence mode="wait">
          {status !== 'success' ? (
            <motion.div
              key={`step-${step}`}
              initial={{ opacity: 0, x: 30 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -30 }}
              transition={{ type: 'spring', stiffness: 300, damping: 30 }}
              className="bg-[var(--tg-theme-bg-color,#fff)] rounded-2xl p-5 shadow-sm border border-black/5"
            >
              <div className="mb-5">
                <h2 className="text-xl font-bold mb-1">
                  {stepIcons[step - 1]} {stepTitles[step - 1]}
                </h2>
                <p className="text-[var(--tg-theme-hint-color,#999)] text-sm">
                  {step === 1 && 'Ваш никнейм в Minecraft (латиница, до 16 символов)'}
                  {step === 2 && 'Укажите ваш возраст для допуска к игре'}
                  {step === 3 && 'Расскажите, как вы нашли наш сервер'}
                  {step === 4 && 'Напишите пару слов о себе для администрации'}
                </p>
              </div>

              {/* Step 1 - Nickname */}
              {step === 1 && (
                <div className="space-y-3">
                  <div className="relative">
                    <div className="absolute left-4 top-1/2 -translate-y-1/2 text-lg">🎮</div>
                    <input
                      type="text"
                      value={form.nickname}
                      onChange={(e) => updateField('nickname', e.target.value)}
                      placeholder="Введите никнейм..."
                      maxLength={16}
                      disabled={status === 'loading'}
                      className="w-full bg-[var(--tg-theme-secondary-bg-color,#f0f0f5)] rounded-xl py-4 pl-12 pr-4 text-base outline-none focus:ring-2 focus:ring-[var(--tg-theme-button-color,#3390ec)] transition-all disabled:opacity-50 font-mono tracking-wide"
                      autoFocus
                    />
                  </div>
                  {form.nickname && !/^[a-zA-Z0-9_]{2,16}$/.test(form.nickname) && (
                    <p className="text-red-500 text-xs flex items-center gap-1">
                      <span>⚠️</span> Только латиница, цифры и _, от 2 до 16 символов
                    </p>
                  )}
                  {form.nickname && /^[a-zA-Z0-9_]{2,16}$/.test(form.nickname) && (
                    <p className="text-green-500 text-xs flex items-center gap-1">
                      <span>✅</span> Никнейм валидный
                    </p>
                  )}
                </div>
              )}

              {/* Step 2 - Age */}
              {step === 2 && (
                <div className="space-y-3">
                  <div className="relative">
                    <div className="absolute left-4 top-1/2 -translate-y-1/2 text-lg">🎂</div>
                    <input
                      type="number"
                      value={form.age}
                      onChange={(e) => updateField('age', e.target.value)}
                      placeholder="Ваш возраст..."
                      min={5}
                      max={120}
                      disabled={status === 'loading'}
                      className="w-full bg-[var(--tg-theme-secondary-bg-color,#f0f0f5)] rounded-xl py-4 pl-12 pr-4 text-base outline-none focus:ring-2 focus:ring-[var(--tg-theme-button-color,#3390ec)] transition-all disabled:opacity-50"
                      autoFocus
                    />
                  </div>
                  {form.age && (Number(form.age) < 5 || Number(form.age) > 120) && (
                    <p className="text-red-500 text-xs flex items-center gap-1">
                      <span>⚠️</span> Укажите корректный возраст (5-120)
                    </p>
                  )}
                </div>
              )}

              {/* Step 3 - Source */}
              {step === 3 && (
                <div className="space-y-3">
                  <div className="relative">
                    <div className="absolute left-4 top-1/2 -translate-y-1/2 text-lg">🔍</div>
                    <select
                      value={form.source}
                      onChange={(e) => updateField('source', e.target.value)}
                      disabled={status === 'loading'}
                      className="w-full bg-[var(--tg-theme-secondary-bg-color,#f0f0f5)] rounded-xl py-4 pl-12 pr-4 text-base outline-none focus:ring-2 focus:ring-[var(--tg-theme-button-color,#3390ec)] transition-all disabled:opacity-50 appearance-none"
                      style={{
                        backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23999' d='M6 8L1 3h10z'/%3E%3C/svg%3E")`,
                        backgroundRepeat: 'no-repeat',
                        backgroundPosition: 'right 16px center',
                      }}
                      autoFocus
                    >
                      <option value="">Выберите вариант...</option>
                      <option value="Друзья">👥 Друзья</option>
                      <option value="YouTube">▶️ YouTube</option>
                      <option value="TikTok">🎵 TikTok</option>
                      <option value="VK / Discord">💬 VK / Discord</option>
                      <option value="Поисковик">🌐 Поисковик</option>
                      <option value="Реклама">📢 Реклама</option>
                      <option value="Другое">📌 Другое</option>
                    </select>
                  </div>
                  {form.source === 'Другое' && (
                    <input
                      type="text"
                      value={form.sourceOther}
                      onChange={(e) => updateField('sourceOther', e.target.value)}
                      placeholder="Уточните, откуда узнали..."
                      className="w-full bg-[var(--tg-theme-secondary-bg-color,#f0f0f5)] rounded-xl py-3 px-4 text-sm outline-none focus:ring-2 focus:ring-[var(--tg-theme-button-color,#3390ec)] transition-all"
                    />
                  )}
                </div>
              )}

              {/* Step 4 - About */}
              {step === 4 && (
                <div className="space-y-3">
                  <div className="relative">
                    <textarea
                      value={form.about}
                      onChange={(e) => updateField('about', e.target.value)}
                      placeholder="Расскажите немного о себе: чем занимаетесь, какой опыт в Minecraft, почему хотите играть именно у нас..."
                      rows={5}
                      maxLength={500}
                      disabled={status === 'loading'}
                      className="w-full bg-[var(--tg-theme-secondary-bg-color,#f0f0f5)] rounded-xl py-4 px-4 text-base outline-none focus:ring-2 focus:ring-[var(--tg-theme-button-color,#3390ec)] transition-all disabled:opacity-50 resize-none"
                      autoFocus
                    />
                  </div>
                  <div className="flex justify-between text-xs text-[var(--tg-theme-hint-color,#999)]">
                    <span>{form.about.length >= 10 ? '✅' : '⚠️'} Минимум 10 символов</span>
                    <span>{form.about.length}/500</span>
                  </div>
                </div>
              )}

              {/* Navigation Buttons */}
              <div className="flex gap-3 mt-6">
                {step > 1 && (
                  <button
                    onClick={prevStep}
                    disabled={status === 'loading'}
                    className="flex-1 bg-[var(--tg-theme-secondary-bg-color,#f0f0f5)] py-4 rounded-xl font-bold text-sm active:scale-[0.98] transition-all disabled:opacity-50"
                  >
                    ← Назад
                  </button>
                )}
                {step < 4 ? (
                  <button
                    onClick={nextStep}
                    disabled={!isStepValid(step) || status === 'loading'}
                    className="flex-1 bg-[var(--tg-theme-button-color,#3390ec)] text-[var(--tg-theme-button-text-color,#fff)] py-4 rounded-xl font-bold text-sm active:scale-[0.98] transition-all disabled:opacity-50 shadow-lg shadow-[var(--tg-theme-button-color,#3390ec)]/20"
                  >
                    Далее →
                  </button>
                ) : (
                  <button
                    onClick={handleSubmit}
                    disabled={!isStepValid(4) || status === 'loading'}
                    className="flex-1 bg-green-500 text-white py-4 rounded-xl font-bold text-sm active:scale-[0.98] transition-all disabled:opacity-50 shadow-lg shadow-green-500/20 flex items-center justify-center gap-2"
                  >
                    {status === 'loading' ? (
                      <>
                        <svg className="animate-spin w-5 h-5" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                        </svg>
                        Отправка...
                      </>
                    ) : (
                      'Отправить заявку'
                    )}
                  </button>
                )}
              </div>

              {error && (
                <div className="mt-4 bg-red-50 border border-red-200 p-3 rounded-xl flex items-start gap-2 text-red-700 text-sm">
                  <span className="text-lg">⚠️</span>
                  <span>{error}</span>
                </div>
              )}
            </motion.div>
          ) : (
            /* Success Screen */
            <motion.div
              key="success"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="bg-green-50 border-2 border-green-200 p-8 rounded-3xl text-center space-y-4"
            >
              <div className="w-24 h-24 bg-green-500 rounded-full flex items-center justify-center mx-auto shadow-lg shadow-green-200">
                <span className="text-4xl">✅</span>
              </div>
              <div>
                <h2 className="text-2xl font-bold text-green-800">Заявка отправлена!</h2>
                <p className="text-green-700 mt-2">
                  Ваша заявка отправлена администрации сервера. 
                  Ожидайте решения — вам придёт уведомление в Telegram.
                </p>
              </div>
              <div className="bg-green-100 p-4 rounded-xl text-left text-sm text-green-800 space-y-1">
                <p><b>🎮 Ник:</b> {form.nickname}</p>
                <p><b>🎂 Возраст:</b> {form.age} лет</p>
                <p><b>🔍 Откуда:</b> {form.source === 'Другое' ? form.sourceOther || 'Другое' : form.source}</p>
              </div>
              <button
                onClick={() => {
                  setStatus('idle');
                  setForm(defaultForm);
                  setStep(1);
                  setProgress(0);
                }}
                className="text-green-600 font-semibold hover:underline text-sm"
              >
                Подать новую заявку
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Server Info */}
        <div className="bg-[var(--tg-theme-secondary-bg-color,#f0f0f5)] rounded-2xl p-4 border border-black/5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm">
              <span>🎮</span>
              <span className="font-bold">{MC_SERVER_IP}</span>
            </div>
            <div className="flex items-center gap-1 text-xs">
              <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
              <span className="text-green-600 font-medium">Online</span>
            </div>
          </div>
          <div className="flex gap-3 mt-2 text-xs text-[var(--tg-theme-hint-color,#999)]">
            <span>📦 1.21.x</span>
            <span>🏆 Ванильный</span>
            <span>👥 Whitelist</span>
          </div>
        </div>
      </main>
    </div>
  );
}
