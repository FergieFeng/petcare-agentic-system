/**
 * PetCare Triage Assistant -- Frontend Logic
 *
 * Authors: Syed Ali Turab, Fergie Feng & Diana Liu | Team: Broadview
 * Date:   March 1, 2026
 * Code updated: Syed Ali Turab, March 4, 2026 — Emergency banner, clinic summary panel, fetch on complete/emergency.
 *
 * Handles the chat interface, session management, voice interaction,
 * and multilingual support for the PetCare Triage & Smart Booking Agent.
 *
 * Voice Support (3 Tiers):
 *   Tier 1: Browser-native Web Speech API (free, no API key)
 *   Tier 2: OpenAI Whisper (STT) + OpenAI TTS (speech synthesis)
 *   Tier 3: OpenAI Realtime API (future — interactive voice)
 *
 * Language Support:
 *   English (en), French (fr), Chinese Mandarin (zh), Arabic (ar),
 *   Spanish (es), Hindi (hi), Urdu (ur)
 *   Arabic and Urdu trigger RTL layout automatically.
 */

// ---------------------------------------------------------------------------
// Supported Languages
// ---------------------------------------------------------------------------

const LANGUAGES = {
    en: {
        code: 'en',
        bcp47: 'en-US',
        name: 'English',
        nativeName: 'English',
        dir: 'ltr',
        ui: {
            title: '🐾 PetCare Triage Assistant',
            subtitle: 'AI-powered veterinary symptom intake & smart booking',
            placeholder: 'Describe your pet\'s symptoms...',
            sendBtn: 'Send',
            disclaimer: 'This tool provides triage support only — not medical diagnoses. Always consult a veterinarian for your pet\'s health concerns.',
            voiceStart: 'Start voice input',
            voiceStop: 'Stop recording',
            speakerOn: 'Speaker on (click to mute)',
            speakerOff: 'Speaker off (click to unmute)',
            connectError: 'Unable to connect to the server. Please try again later.',
            sendError: 'Something went wrong. Please try again.',
            micDenied: 'Microphone access is required for voice input. Please allow microphone access and try again.',
            voiceFail: 'Voice transcription failed. Please type your message instead.',
            audioFail: 'Could not understand the audio. Please try again.'
        }
    },
    fr: {
        code: 'fr',
        bcp47: 'fr-FR',
        name: 'French',
        nativeName: 'Français',
        dir: 'ltr',
        ui: {
            title: '🐾 Assistant Triage Vétérinaire',
            subtitle: 'Prise en charge vétérinaire et prise de rendez-vous par IA',
            placeholder: 'Décrivez les symptômes de votre animal...',
            sendBtn: 'Envoyer',
            disclaimer: 'Cet outil fournit un soutien au triage uniquement — pas de diagnostics médicaux. Consultez toujours un vétérinaire pour les problèmes de santé de votre animal.',
            voiceStart: 'Démarrer la saisie vocale',
            voiceStop: 'Arrêter l\'enregistrement',
            speakerOn: 'Haut-parleur activé (cliquer pour couper)',
            speakerOff: 'Haut-parleur désactivé (cliquer pour activer)',
            connectError: 'Impossible de se connecter au serveur. Veuillez réessayer plus tard.',
            sendError: 'Une erreur s\'est produite. Veuillez réessayer.',
            micDenied: 'L\'accès au microphone est requis pour la saisie vocale. Veuillez autoriser l\'accès au microphone et réessayer.',
            voiceFail: 'La transcription vocale a échoué. Veuillez taper votre message.',
            audioFail: 'Impossible de comprendre l\'audio. Veuillez réessayer.'
        }
    },
    zh: {
        code: 'zh',
        bcp47: 'zh-CN',
        name: 'Chinese',
        nativeName: '中文',
        dir: 'ltr',
        ui: {
            title: '🐾 宠物护理分诊助手',
            subtitle: 'AI驱动的兽医症状采集与智能预约',
            placeholder: '请描述您宠物的症状...',
            sendBtn: '发送',
            disclaimer: '此工具仅提供分诊支持，不提供医学诊断。请始终咨询兽医以了解您宠物的健康问题。',
            voiceStart: '开始语音输入',
            voiceStop: '停止录音',
            speakerOn: '扬声器已开启（点击静音）',
            speakerOff: '扬声器已关闭（点击开启）',
            connectError: '无法连接到服务器。请稍后再试。',
            sendError: '出了点问题。请重试。',
            micDenied: '语音输入需要麦克风权限。请允许麦克风访问后重试。',
            voiceFail: '语音转录失败。请改为输入您的消息。',
            audioFail: '无法理解音频。请重试。'
        }
    },
    ar: {
        code: 'ar',
        bcp47: 'ar-SA',
        name: 'Arabic',
        nativeName: 'العربية',
        dir: 'rtl',
        ui: {
            title: '🐾 مساعد فرز رعاية الحيوانات الأليفة',
            subtitle: 'استقبال الأعراض البيطرية والحجز الذكي بالذكاء الاصطناعي',
            placeholder: 'صف أعراض حيوانك الأليف...',
            sendBtn: 'إرسال',
            disclaimer: 'هذه الأداة توفر دعم الفرز فقط — وليس التشخيص الطبي. استشر دائمًا طبيبًا بيطريًا بشأن صحة حيوانك الأليف.',
            voiceStart: 'بدء الإدخال الصوتي',
            voiceStop: 'إيقاف التسجيل',
            speakerOn: 'مكبر الصوت مفعّل (انقر للكتم)',
            speakerOff: 'مكبر الصوت مكتوم (انقر للتفعيل)',
            connectError: 'تعذر الاتصال بالخادم. يرجى المحاولة لاحقًا.',
            sendError: 'حدث خطأ ما. يرجى المحاولة مرة أخرى.',
            micDenied: 'مطلوب الوصول إلى الميكروفون للإدخال الصوتي. يرجى السماح بالوصول والمحاولة مرة أخرى.',
            voiceFail: 'فشل النسخ الصوتي. يرجى كتابة رسالتك بدلاً من ذلك.',
            audioFail: 'تعذر فهم الصوت. يرجى المحاولة مرة أخرى.'
        }
    },
    es: {
        code: 'es',
        bcp47: 'es-ES',
        name: 'Spanish',
        nativeName: 'Español',
        dir: 'ltr',
        ui: {
            title: '🐾 Asistente de Triaje Veterinario',
            subtitle: 'Evaluación de síntomas veterinarios y reserva inteligente con IA',
            placeholder: 'Describa los síntomas de su mascota...',
            sendBtn: 'Enviar',
            disclaimer: 'Esta herramienta proporciona solo soporte de triaje, no diagnósticos médicos. Siempre consulte a un veterinario para las preocupaciones de salud de su mascota.',
            voiceStart: 'Iniciar entrada de voz',
            voiceStop: 'Detener grabación',
            speakerOn: 'Altavoz activado (clic para silenciar)',
            speakerOff: 'Altavoz desactivado (clic para activar)',
            connectError: 'No se pudo conectar al servidor. Inténtelo de nuevo más tarde.',
            sendError: 'Algo salió mal. Inténtelo de nuevo.',
            micDenied: 'Se requiere acceso al micrófono para la entrada de voz. Permita el acceso al micrófono e inténtelo de nuevo.',
            voiceFail: 'La transcripción de voz falló. Escriba su mensaje en su lugar.',
            audioFail: 'No se pudo entender el audio. Inténtelo de nuevo.'
        }
    },
    hi: {
        code: 'hi',
        bcp47: 'hi-IN',
        name: 'Hindi',
        nativeName: 'हिन्दी',
        dir: 'ltr',
        ui: {
            title: '🐾 पेटकेयर ट्राइएज सहायक',
            subtitle: 'AI-संचालित पशु चिकित्सा लक्षण सेवन और स्मार्ट बुकिंग',
            placeholder: 'अपने पालतू जानवर के लक्षण बताएं...',
            sendBtn: 'भेजें',
            disclaimer: 'यह उपकरण केवल ट्राइएज सहायता प्रदान करता है — चिकित्सा निदान नहीं। अपने पालतू जानवर की स्वास्थ्य चिंताओं के लिए हमेशा पशु चिकित्सक से परामर्श करें।',
            voiceStart: 'आवाज़ इनपुट शुरू करें',
            voiceStop: 'रिकॉर्डिंग बंद करें',
            speakerOn: 'स्पीकर चालू (म्यूट करने के लिए क्लिक करें)',
            speakerOff: 'स्पीकर बंद (चालू करने के लिए क्लिक करें)',
            connectError: 'सर्वर से कनेक्ट नहीं हो सका। कृपया बाद में पुनः प्रयास करें।',
            sendError: 'कुछ गलत हो गया। कृपया पुनः प्रयास करें।',
            micDenied: 'आवाज़ इनपुट के लिए माइक्रोफ़ोन एक्सेस आवश्यक है। कृपया माइक्रोफ़ोन एक्सेस दें और पुनः प्रयास करें।',
            voiceFail: 'आवाज़ ट्रांसक्रिप्शन विफल हुआ। कृपया अपना संदेश टाइप करें।',
            audioFail: 'ऑडियो समझ नहीं आया। कृपया पुनः प्रयास करें।'
        }
    },
    ur: {
        code: 'ur',
        bcp47: 'ur-PK',
        name: 'Urdu',
        nativeName: 'اردو',
        dir: 'rtl',
        ui: {
            title: '🐾 پیٹ کیئر ٹرائیج اسسٹنٹ',
            subtitle: 'AI سے چلنے والا ویٹرنری علامات کا جائزہ اور سمارٹ بکنگ',
            placeholder: 'اپنے پالتو جانور کی علامات بیان کریں...',
            sendBtn: 'بھیجیں',
            disclaimer: 'یہ ٹول صرف ٹرائیج سپورٹ فراہم کرتا ہے — طبی تشخیص نہیں۔ اپنے پالتو جانور کی صحت کے خدشات کے لیے ہمیشہ ویٹرنری ڈاکٹر سے مشورہ کریں۔',
            voiceStart: 'آواز ان پٹ شروع کریں',
            voiceStop: 'ریکارڈنگ بند کریں',
            speakerOn: 'اسپیکر آن (خاموش کرنے کے لیے کلک کریں)',
            speakerOff: 'اسپیکر آف (آن کرنے کے لیے کلک کریں)',
            connectError: 'سرور سے رابطہ نہیں ہو سکا۔ بعد میں دوبارہ کوشش کریں۔',
            sendError: 'کچھ غلط ہو گیا۔ براہ کرم دوبارہ کوشش کریں۔',
            micDenied: 'آواز ان پٹ کے لیے مائیکروفون تک رسائی ضروری ہے۔ براہ کرم مائیکروفون کی اجازت دیں اور دوبارہ کوشش کریں۔',
            voiceFail: 'آواز کی ٹرانسکرپشن ناکام ہوئی۔ براہ کرم اپنا پیغام ٹائپ کریں۔',
            audioFail: 'آڈیو سمجھ نہیں آئی۔ براہ کرم دوبارہ کوشش کریں۔'
        }
    }
};

// ---------------------------------------------------------------------------
// Global State
// ---------------------------------------------------------------------------

let sessionId = null;
let isRecording = false;
let mediaRecorder = null;
let audioChunks = [];
let voiceTier = 1;
let speechRecognition = null;
let ttsEnabled = true;
let currentLang = 'en';
let lastTriageState = null;  // tracks post-triage state for action buttons
const _shownBreeds = new Set();

const BREED_RISKS = {
    'golden retriever': { risks: ['Hip dysplasia', 'Cancer (lymphoma, hemangiosarcoma)', 'Heart disease'], tip: 'Regular hip and cancer screenings recommended after age 5' },
    'german shepherd': { risks: ['Hip & elbow dysplasia', 'Degenerative myelopathy', 'Bloat (GDV)'], tip: 'Feed smaller meals to reduce bloat risk' },
    'labrador': { risks: ['Obesity', 'Hip dysplasia', 'Exercise-induced collapse'], tip: 'Monitor weight carefully and avoid overfeeding' },
    'bulldog': { risks: ['Brachycephalic syndrome', 'Skin fold infections', 'Joint problems'], tip: 'Keep airways clear and monitor breathing in heat' },
    'poodle': { risks: ['Hip dysplasia', 'Progressive retinal atrophy', 'Bloat'], tip: 'Regular eye exams recommended' },
    'beagle': { risks: ['Epilepsy', 'Hypothyroidism', 'Intervertebral disc disease'], tip: 'Watch for seizure activity and weight gain' },
    'husky': { risks: ['Autoimmune disorders', 'Hip dysplasia', 'Eye conditions'], tip: 'Regular eye check-ups are important' },
    'chihuahua': { risks: ['Patellar luxation', 'Heart disease', 'Hydrocephalus'], tip: 'Handle gently and protect from cold temperatures' },
    'persian': { risks: ['Polycystic kidney disease', 'Breathing difficulties', 'Eye discharge'], tip: 'Regular kidney screening recommended' },
    'siamese': { risks: ['Amyloidosis', 'Respiratory issues', 'Crossed eyes'], tip: 'Monitor appetite and energy levels closely' },
    'maine coon': { risks: ['Hypertrophic cardiomyopathy', 'Hip dysplasia', 'Spinal muscular atrophy'], tip: 'Regular heart screening recommended' }
};

// ---------------------------------------------------------------------------
// Initialization
// ---------------------------------------------------------------------------

document.addEventListener('DOMContentLoaded', initApp);

/**
 * Initialize the application on page load.
 *
 * Sets up event listeners for text input (Enter key to send),
 * detects language from URL params or browser settings,
 * checks voice support, and starts a new intake session.
 */
async function initApp() {
    const input = document.getElementById('user-input');
    checkOnboarding();
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    loadDarkModePreference();
    checkConsent();

    const urlParams = new URLSearchParams(window.location.search);
    const urlLang = urlParams.get('lang');
    if (urlLang && LANGUAGES[urlLang]) {
        currentLang = urlLang;
    } else {
        const browserLang = navigator.language.split('-')[0];
        if (LANGUAGES[browserLang]) {
            currentLang = browserLang;
        }
    }

    document.getElementById('lang-select').value = currentLang;
    applyLanguage(currentLang);

    await detectVoiceSupport();
    await startSession();
    _loadPetProfile();
    _showSymptomHistory();

    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/sw.js').catch(() => {});
    }
}

// ---------------------------------------------------------------------------
// Language Management
// ---------------------------------------------------------------------------

/**
 * Called when the user selects a new language from the dropdown.
 * Applies the language to the UI and restarts the session so
 * the agent responds in the new language from the start.
 */
function changeLanguage(langCode) {
    if (!LANGUAGES[langCode]) return;
    currentLang = langCode;
    applyLanguage(langCode);

    // Update Web Speech API language if available
    if (speechRecognition) {
        speechRecognition.lang = LANGUAGES[langCode].bcp47;
    }

    // Restart the session so the welcome message is in the new language
    startSession();
}

/**
 * Apply the selected language to all UI elements.
 * Handles RTL/LTR direction switching for Arabic and Urdu.
 */
function applyLanguage(langCode) {
    const lang = LANGUAGES[langCode];
    if (!lang) return;

    const htmlEl = document.documentElement;
    htmlEl.lang = langCode;
    htmlEl.dir = lang.dir;

    document.getElementById('app-title').textContent = lang.ui.title;
    document.getElementById('app-subtitle').textContent = lang.ui.subtitle;
    document.getElementById('user-input').placeholder = lang.ui.placeholder;
    document.getElementById('send-btn').title = lang.ui.sendBtn;
    document.getElementById('disclaimer').textContent = lang.ui.disclaimer;

    const voiceBtn = document.getElementById('voice-btn');
    if (voiceBtn && !isRecording) {
        voiceBtn.title = lang.ui.voiceStart;
    }

    const ttsBtn = document.getElementById('tts-btn');
    if (ttsBtn) {
        ttsBtn.title = ttsEnabled ? lang.ui.speakerOn : lang.ui.speakerOff;
    }
}

/**
 * Get a translated UI string for the current language.
 * Falls back to English if the key is missing.
 */
function t(key) {
    const lang = LANGUAGES[currentLang] || LANGUAGES['en'];
    return lang.ui[key] || LANGUAGES['en'].ui[key] || key;
}

// ---------------------------------------------------------------------------
// Dark Mode
// ---------------------------------------------------------------------------

function toggleDarkMode() {
    const html = document.documentElement;
    const isDark = html.getAttribute('data-theme') === 'dark';
    const newTheme = isDark ? 'light' : 'dark';
    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('petcare_theme', newTheme);

    const btn = document.getElementById('dark-mode-toggle');
    if (btn) btn.textContent = newTheme === 'dark' ? '☀️' : '🌙';
}

function loadDarkModePreference() {
    const saved = localStorage.getItem('petcare_theme');
    if (saved === 'dark') {
        document.documentElement.setAttribute('data-theme', 'dark');
        const btn = document.getElementById('dark-mode-toggle');
        if (btn) btn.textContent = '☀️';
    }
}

// ---------------------------------------------------------------------------
// Consent Banner
// ---------------------------------------------------------------------------

function checkConsent() {
    if (!localStorage.getItem('petcare_consent_accepted')) {
        const banner = document.getElementById('consent-banner');
        if (banner) banner.classList.remove('hidden');
    }
}

function acceptConsent() {
    localStorage.setItem('petcare_consent_accepted', 'true');
    const banner = document.getElementById('consent-banner');
    if (banner) banner.classList.add('hidden');
}

// ---------------------------------------------------------------------------
// Voice Support Detection
// ---------------------------------------------------------------------------

/**
 * Detect which voice tier is available.
 *
 * Tier 1: Browser Web Speech API (SpeechRecognition).
 * Tier 2: OpenAI Whisper + TTS via backend endpoints.
 *
 * Sets the global voiceTier variable and updates the UI.
 */
async function detectVoiceSupport() {
    const SpeechRecognition = window.SpeechRecognition ||
                               window.webkitSpeechRecognition;

    if (SpeechRecognition) {
        speechRecognition = new SpeechRecognition();
        speechRecognition.continuous = false;
        speechRecognition.interimResults = false;
        speechRecognition.lang = LANGUAGES[currentLang].bcp47;

        speechRecognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            document.getElementById('user-input').value = transcript;
            sendMessage('voice');
        };

        speechRecognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            stopRecording();
        };

        speechRecognition.onend = () => {
            stopRecording();
        };
    }

    try {
        const res = await fetch('/api/health');
        const data = await res.json();
        if (data.voice_enabled) {
            voiceTier = 2;
        }
    } catch (err) {
        console.warn('Could not check voice support:', err);
    }

    if (speechRecognition || voiceTier >= 2) {
        const voiceBtn = document.getElementById('voice-btn');
        if (voiceBtn) voiceBtn.classList.remove('hidden');
    }

    console.log(`Voice tier: ${voiceTier} | Language: ${currentLang}`);
}

// ---------------------------------------------------------------------------
// Session Management
// ---------------------------------------------------------------------------

/**
 * Start a new intake session by calling the backend.
 * Passes the current language so the welcome message comes
 * back in the right language.
 */
async function startSession() {
    // Clear existing messages
    document.getElementById('chat-messages').innerHTML = '';

    try {
        const res = await fetch('/api/session/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ language: currentLang })
        });
        const data = await res.json();
        sessionId = data.session_id;
        addMessage(data.message, 'assistant');
        speakText(data.message);
    } catch (err) {
        addMessage(t('connectError'), 'assistant');
        console.error('Failed to start session:', err);
    }
}

// ---------------------------------------------------------------------------
// Message Handling
// ---------------------------------------------------------------------------

/**
 * Send the current text input as a message to the backend.
 * The language is passed with every message so the backend
 * knows which language to respond in.
 */
async function sendMessage(source = 'text') {
    const input = document.getElementById('user-input');
    const message = input.value.trim();
    if (!message || !sessionId) return;

    input.value = '';
    addMessage(message, 'user');
    _checkBreedRisks(message);

    const sendBtn = document.getElementById('send-btn');
    sendBtn.disabled = true;
    showTypingIndicator();

    try {
        const res = await fetch(`/api/session/${sessionId}/message`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, source, language: currentLang })
        });

        if (!res.ok) {
            removeTypingIndicator();
            if (res.status === 404) {
                addMessage('Session expired. Starting a fresh session...', 'assistant');
                await startSession();
                return;
            }
            addMessage(t('sendError'), 'assistant');
            return;
        }

        const data = await res.json();
        removeTypingIndicator();

        // Restart flow: if state returned to intake from a completed flow,
        // clear the chat and start fresh so old messages don't linger.
        if (data.state === 'intake' && lastTriageState && lastTriageState !== 'intake') {
            document.getElementById('chat-messages').innerHTML = '';
            lastTriageState = 'intake';
            addMessage(data.message, 'assistant');
            speakText(data.message);
            return;
        }

        const isEmergency = data.emergency ||
            data.state === 'emergency' ||
            (data.message && data.message.includes('EMERGENCY'));

        addMessage(data.message, 'assistant', isEmergency);
        speakText(data.message);
        lastTriageState = data.state;

        if (isEmergency) {
            if (!document.getElementById('emergency-banner')) {
                const banner = document.createElement('div');
                banner.id = 'emergency-banner';
                banner.style.cssText = 'background:#c0392b;color:white;padding:12px 16px;font-weight:bold;text-align:center;border-radius:8px;margin:8px 0;font-size:15px;';
                banner.textContent = '🚨 EMERGENCY — Please take your pet to an emergency veterinary clinic immediately. Do not wait.';
                document.getElementById('chat-messages').prepend(banner);
            }
        }

        if (data.state === 'complete' || data.state === 'emergency') {
            try {
                const sumRes = await fetch(`/api/session/${sessionId}/summary`);
                const sumData = await sumRes.json();
                _showClinicPanel(sumData);
                _savePetProfile(sumData.pet_profile);
                _saveSymptomHistory(sumData);
            } catch (err) {
                console.error('Could not fetch clinic summary:', err);
            }
            _showActionButtons();
            const urgencyTier = _detectUrgencyTier(data.message);
            _showCostEstimate(urgencyTier);
            _showFeedbackPrompt();
        }

        if (data.state === 'booked') {
            _showActionButtons();
            _showReminderPrompt();
        }

    } catch (err) {
        removeTypingIndicator();
        addMessage(t('sendError'), 'assistant');
        console.error('Failed to send message:', err);
    } finally {
        sendBtn.disabled = false;
        input.focus();
    }
}

// ---------------------------------------------------------------------------
// Voice Recording
// ---------------------------------------------------------------------------

/**
 * Toggle voice recording on/off.
 */
function toggleVoice() {
    if (isRecording) {
        stopRecording();
    } else {
        startRecording();
    }
}

/**
 * Start voice recording.
 *
 * Prefers browser SpeechRecognition (Tier 1) when available because it
 * auto-detects end-of-speech — the user clicks once to start, and the
 * result fires automatically when they stop talking.
 *
 * Falls back to MediaRecorder → Whisper (Tier 2) only when the browser
 * does not support SpeechRecognition (e.g. Firefox, Safari).
 */
async function startRecording() {
    isRecording = true;
    updateVoiceButton(true);

    if (speechRecognition) {
        speechRecognition.lang = LANGUAGES[currentLang].bcp47;
        speechRecognition.start();

    } else if (voiceTier >= 2) {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: true
            });

            mediaRecorder = new MediaRecorder(stream, {
                mimeType: 'audio/webm'
            });
            audioChunks = [];

            mediaRecorder.ondataavailable = (e) => {
                if (e.data.size > 0) audioChunks.push(e.data);
            };

            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(audioChunks, {
                    type: 'audio/webm'
                });
                await transcribeAudio(audioBlob);
                stream.getTracks().forEach(t => t.stop());
            };

            mediaRecorder.start();
        } catch (err) {
            console.error('Microphone access denied:', err);
            addMessage(t('micDenied'), 'assistant');
            stopRecording();
        }
    }
}

/**
 * Stop voice recording.
 */
function stopRecording() {
    isRecording = false;
    updateVoiceButton(false);

    if (speechRecognition) {
        try { speechRecognition.stop(); } catch (_) { /* already stopped */ }
    } else if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
    }
}

/**
 * Send recorded audio to the backend for Whisper transcription.
 * Passes the current language so Whisper can optimize recognition.
 *
 * @param {Blob} audioBlob - The recorded audio data (WebM format)
 */
async function transcribeAudio(audioBlob) {
    showTypingIndicator();

    try {
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.webm');
        formData.append('language', currentLang);

        const res = await fetch('/api/voice/transcribe', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        removeTypingIndicator();

        if (data.text) {
            document.getElementById('user-input').value = data.text;
            await sendMessage('voice');
        } else {
            addMessage(t('audioFail'), 'assistant');
        }
    } catch (err) {
        removeTypingIndicator();
        console.error('Transcription failed:', err);
        addMessage(t('voiceFail'), 'assistant');
    }
}

// ---------------------------------------------------------------------------
// Text-to-Speech (Response Playback)
// ---------------------------------------------------------------------------

/**
 * Speak text aloud using the best available TTS method.
 * Passes the current language to both the browser TTS and OpenAI TTS.
 *
 * @param {string} text - The text to speak aloud
 */
async function speakText(text) {
    if (!ttsEnabled || !text) return;

    if (voiceTier >= 2) {
        try {
            const res = await fetch('/api/voice/synthesize', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text,
                    voice: 'nova',
                    language: currentLang
                })
            });

            if (res.ok) {
                const audioBlob = await res.blob();
                const audioUrl = URL.createObjectURL(audioBlob);
                const audio = new Audio(audioUrl);
                audio.play();
                return;
            }
        } catch (err) {
            console.warn('OpenAI TTS failed, falling back to browser:', err);
        }
    }

    // Tier 1 fallback: Browser-native TTS
    if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();

        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = LANGUAGES[currentLang].bcp47;
        utterance.rate = 0.95;
        utterance.pitch = 1.0;
        utterance.volume = 1.0;
        window.speechSynthesis.speak(utterance);
    }
}

/**
 * Toggle text-to-speech on/off.
 */
function toggleTTS() {
    ttsEnabled = !ttsEnabled;
    const ttsBtn = document.getElementById('tts-btn');
    if (ttsBtn) {
        ttsBtn.textContent = ttsEnabled ? '🔊' : '🔇';
        ttsBtn.title = ttsEnabled ? t('speakerOn') : t('speakerOff');
    }
}

// ---------------------------------------------------------------------------
// UI Helpers
// ---------------------------------------------------------------------------

/**
 * Add a message bubble to the chat container.
 *
 * @param {string} text - The message text
 * @param {string} role - 'user' or 'assistant'
 * @param {boolean} isEmergency - If true, styles as emergency alert
 */
function addMessage(text, role, isEmergency = false) {
    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = `message ${role}`;
    if (isEmergency) div.classList.add('emergency');

    if (role === 'assistant') {
        const html = _formatMessage(text);
        div.innerHTML = '';
        container.appendChild(div);
        _typeMessage(div, html);
    } else {
        div.textContent = text;
        container.appendChild(div);
        container.scrollTop = container.scrollHeight;
    }
}

function _typeMessage(element, html, speed = 15) {
    let i = 0;
    const chunkSize = 3;

    function revealNext() {
        if (i >= html.length) {
            element.innerHTML = html;
            const container = document.getElementById('chat-messages');
            container.scrollTop = container.scrollHeight;
            return;
        }

        let end = Math.min(i + chunkSize, html.length);

        const lastOpen = html.lastIndexOf('<', end - 1);
        const lastClose = html.lastIndexOf('>', end - 1);
        if (lastOpen > lastClose) {
            const nextClose = html.indexOf('>', end);
            if (nextClose !== -1) end = nextClose + 1;
        }

        const lastAmp = html.lastIndexOf('&', end - 1);
        if (lastAmp >= i) {
            const semi = html.indexOf(';', lastAmp);
            if (semi !== -1 && semi >= end) end = semi + 1;
        }

        i = end;
        element.innerHTML = html.substring(0, i) + '<span class="typing-cursor"></span>';

        const container = document.getElementById('chat-messages');
        container.scrollTop = container.scrollHeight;

        setTimeout(revealNext, speed);
    }

    revealNext();
}

function _formatMessage(text) {
    if (!text) return '';
    let html = String(text)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');

    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

    const urgencyPattern = /recommend a <strong>(Emergency|Same-day|Soon|Routine)<\/strong> visit/;
    const match = html.match(urgencyPattern);
    if (match) {
        const tier = match[1];
        const colors = {
            Emergency: '#dc2626', 'Same-day': '#f59e0b',
            Soon: '#d4ac0d', Routine: '#16a34a'
        };
        const color = colors[tier] || '#64748b';
        html = html.replace(
            urgencyPattern,
            `recommend a <span class="urgency-badge" style="background:${color}">${tier}</span> visit`
        );
    }

    html = html.replace(
        /^(  - (.+?)(with .+)?)$/gm,
        (_, full, datetime, provider) => {
            const cleanDt = datetime.replace(provider || '', '').trim();
            const cleanProv = (provider || '').replace('with ', '').trim();
            return `<button class="slot-btn" onclick="_bookSlot(this, '${cleanProv}')" data-provider="${cleanProv}" data-datetime="${cleanDt}">
                <span class="slot-datetime">📅 ${cleanDt}</span>
                <span class="slot-provider">${cleanProv ? 'with ' + cleanProv : ''}</span>
            </button>`;
        }
    );

    html = html.replace(/^  ✓ (.+)$/gm, '<div class="tip-item tip-do">✓ $1</div>');
    html = html.replace(/^  ⚠ (.+)$/gm, '<div class="tip-item tip-warn">⚠ $1</div>');

    html = html.replace(/\n(Available appointments:)/g, '<div class="section-label">$1</div>');
    html = html.replace(/\n(While you wait:)/g, '<div class="section-label section-do">$1</div>');
    html = html.replace(/\n(Seek emergency care if you notice:)/g, '<div class="section-label section-warn">$1</div>');

    html = html.replace(/\n\n/g, '<br><br>').replace(/\n/g, '<br>');

    return html;
}

function _bookSlot(btn, provider) {
    const msg = provider ? `book with ${provider}` : 'book the first one';
    document.getElementById('user-input').value = msg;
    sendMessage();
}

/**
 * Show a typing indicator in the chat.
 */
function showTypingIndicator() {
    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = 'message assistant';
    div.id = 'typing-indicator';
    div.innerHTML =
        '<div class="typing-indicator">' +
        '<span></span><span></span><span></span>' +
        '</div>';
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

/**
 * Remove the typing indicator from the chat.
 */
function removeTypingIndicator() {
    const el = document.getElementById('typing-indicator');
    if (el) el.remove();
}

/**
 * Update the voice button appearance based on recording state.
 *
 * @param {boolean} recording - Whether voice recording is active
 */
function updateVoiceButton(recording) {
    const voiceBtn = document.getElementById('voice-btn');
    if (!voiceBtn) return;

    if (recording) {
        voiceBtn.classList.add('recording');
        voiceBtn.textContent = '⏹';
        voiceBtn.title = t('voiceStop');
    } else {
        voiceBtn.classList.remove('recording');
        voiceBtn.textContent = '🎤';
        voiceBtn.title = t('voiceStart');
    }
}

/**
 * Renders the clinic-facing summary panel (staff view only).
 * Shows pet, urgency tier, rationale, factors, routing, slots, fields captured; includes "Copy full JSON" button.
 * Added March 4, 2026 — Syed Ali Turab.
 * @param {Object} sumData - Response from GET /api/session/<id>/summary
 */
// ---------------------------------------------------------------------------
// Action Buttons (post-triage)
// ---------------------------------------------------------------------------

function _showActionButtons() {
    if (document.getElementById('action-buttons')) return;

    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.id = 'action-buttons';
    div.className = 'action-buttons';
    div.innerHTML = `
        <button onclick="findNearbyVets()" class="action-btn vet-finder-btn">
            📍 Find Nearby Vets
        </button>
        <button onclick="downloadSummary()" class="action-btn export-btn">
            📄 Download Summary
        </button>
        <button onclick="downloadTranscript()" class="action-btn export-btn">
            💬 Download Transcript
        </button>
    `;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;

    _autoOfferVetFinder();
}

function _autoOfferVetFinder() {
    if (document.getElementById('vet-offer-prompt')) return;

    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.id = 'vet-offer-prompt';
    div.className = 'message assistant vet-offer';
    div.innerHTML = `
        <div class="vet-offer-content">
            <span class="vet-offer-icon">📍</span>
            <div class="vet-offer-text">
                <strong>Need a vet nearby?</strong>
                <span>I can find veterinary clinics near you with phone numbers and directions.</span>
            </div>
        </div>
        <div class="vet-offer-actions">
            <button onclick="_acceptVetOffer()" class="action-btn-sm">Yes, find vets near me</button>
            <button onclick="this.closest('.vet-offer').remove()" class="action-btn-sm secondary">No thanks</button>
        </div>
    `;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function _acceptVetOffer() {
    const offer = document.getElementById('vet-offer-prompt');
    if (offer) offer.remove();
    findNearbyVets();
}

// ---------------------------------------------------------------------------
// Feature 1: Nearby Vet Finder
// ---------------------------------------------------------------------------

async function findNearbyVets() {
    if (!navigator.geolocation) {
        addMessage('Location services are not available in your browser.', 'assistant');
        return;
    }

    const existing = document.querySelector('.vet-results');
    if (existing) existing.remove();

    addMessage('📍 Searching for nearby veterinary clinics...', 'assistant');
    showTypingIndicator();

    try {
        const pos = await Promise.race([
            new Promise((resolve, reject) => {
                navigator.geolocation.getCurrentPosition(resolve, reject, {
                    enableHighAccuracy: false,
                    timeout: 8000,
                    maximumAge: 300000
                });
            }),
            new Promise((_, reject) =>
                setTimeout(() => reject({ code: 3, message: 'Location request timed out' }), 12000)
            )
        ]);

        const { latitude: lat, longitude: lng } = pos.coords;

        const res = await fetch('/api/nearby-vets', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ lat, lng, radius_km: 10 })
        });
        const data = await res.json();
        removeTypingIndicator();

        if (data.error) {
            const isApiDisabled = data.error.includes('not been used') || data.error.includes('disabled');
            if (isApiDisabled) {
                addMessage(
                    '⚠️ The Google Places API needs to be enabled for your project. ' +
                    'Visit your Google Cloud Console → APIs & Services → Enable "Places API (New)".',
                    'assistant'
                );
            } else {
                addMessage(`Could not find nearby vets: ${data.error}`, 'assistant');
            }
            return;
        }

        if (!data.vets || data.vets.length === 0) {
            addMessage('No veterinary clinics found within 10 km. Try expanding your search area.', 'assistant');
            return;
        }

        _renderVetResults(data.vets);

    } catch (err) {
        removeTypingIndicator();
        if (err.code === 1) {
            addMessage('📍 Location access was denied. Please allow location access in your browser settings and try again.', 'assistant');
        } else if (err.code === 3 || (err.message && err.message.includes('timed out'))) {
            addMessage('📍 Location request timed out. Please check that location services are enabled in your system settings and try again.', 'assistant');
        } else {
            addMessage('📍 Could not determine your location. Please check your browser and system location settings.', 'assistant');
        }
        console.error('Geolocation error:', err);
    }
}

function _renderVetResults(vets) {
    const container = document.getElementById('chat-messages');
    const wrapper = document.createElement('div');
    wrapper.className = 'message assistant vet-results';

    let html = '<div class="vet-results-header">🏥 Nearby Veterinary Clinics</div>';
    html += '<div class="vet-cards">';

    for (const vet of vets.slice(0, 5)) {
        const stars = vet.rating ? '⭐'.repeat(Math.round(vet.rating)) : '';
        const ratingText = vet.rating ? `${vet.rating}/5 (${vet.total_ratings} reviews)` : 'No ratings';
        const statusClass = vet.open_now ? 'open' : 'closed';
        const statusText = vet.open_now === true ? '🟢 Open now' : vet.open_now === false ? '🔴 Closed' : '';
        const mapsLink = vet.maps_url
            ? `<a href="${vet.maps_url}" target="_blank" rel="noopener" class="vet-directions-btn">🗺️ Get Directions</a>`
            : '';

        const callBtn = vet.phone
            ? `<a href="tel:${vet.phone}" class="vet-call-btn">📞 Call ${vet.phone}</a>`
            : '<span class="vet-no-phone">No phone listed</span>';

        const websiteLink = vet.website
            ? `<a href="${vet.website}" target="_blank" rel="noopener" class="vet-website-btn">🌐 Website</a>`
            : '';

        const hoursInfo = vet.hours_today
            ? `<div class="vet-hours">🕐 ${vet.hours_today}</div>`
            : '';

        html += `
            <div class="vet-card">
                <div class="vet-card-header">
                    <div>
                        <div class="vet-name">${vet.name}</div>
                        <div class="vet-address">${vet.address}</div>
                    </div>
                    ${statusText ? `<span class="vet-status-badge ${statusClass}">${statusText}</span>` : ''}
                </div>
                <div class="vet-meta">
                    <span class="vet-distance">${vet.distance_km} km away</span>
                    <span class="vet-rating">${stars} ${ratingText}</span>
                </div>
                ${hoursInfo}
                <div class="vet-actions">
                    ${callBtn}
                    ${mapsLink}
                    ${websiteLink}
                </div>
            </div>`;
    }

    html += '</div>';
    html += `<div class="vet-results-footer">
        <button onclick="findNearbyVets()" class="action-btn-sm secondary">🔄 Refresh results</button>
    </div>`;
    wrapper.innerHTML = html;
    container.appendChild(wrapper);
    container.scrollTop = container.scrollHeight;
}

// ---------------------------------------------------------------------------
// Feature 2a: Chat Transcript Export
// ---------------------------------------------------------------------------

function downloadTranscript() {
    const messages = document.querySelectorAll('#chat-messages .message');
    const lines = [];
    const now = new Date();
    const dateStr = now.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });

    lines.push('PetCare Triage - Chat Transcript');
    lines.push(`Date: ${dateStr}`);
    lines.push(`Session: ${sessionId || 'N/A'}`);
    lines.push('================================');
    lines.push('');

    messages.forEach(msg => {
        const isUser = msg.classList.contains('user');
        const label = isUser ? '[You]' : '[PetCare]';
        const text = msg.textContent.trim();
        if (text) {
            lines.push(`${label} ${text}`);
            lines.push('');
        }
    });

    lines.push('================================');
    lines.push('Generated by PetCare Triage Assistant');

    const blob = new Blob([lines.join('\n')], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    const fileDate = now.toISOString().slice(0, 10);
    a.href = url;
    a.download = `petcare_transcript_${fileDate}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// ---------------------------------------------------------------------------
// Feature 2b: Export Triage Summary as PDF
// ---------------------------------------------------------------------------

async function downloadSummary() {
    if (!sessionId) return;

    try {
        const res = await fetch(`/api/session/${sessionId}/export`);
        if (!res.ok) {
            if (res.status === 404) {
                addMessage('Session expired — please complete a new triage to download a summary.', 'assistant');
                return;
            }
            const err = await res.json();
            addMessage(`Could not generate PDF: ${err.error || 'Unknown error'}`, 'assistant');
            return;
        }

        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `petcare_triage_summary.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        addMessage('📄 Your triage summary PDF has been downloaded. Share it with your veterinarian.', 'assistant');
    } catch (err) {
        console.error('PDF download failed:', err);
        addMessage('Failed to download summary. Please try again.', 'assistant');
    }
}

// ---------------------------------------------------------------------------
// Feature 3: Photo Upload & Visual Analysis
// ---------------------------------------------------------------------------

async function handlePhotoUpload(input) {
    const file = input.files[0];
    if (!file || !sessionId) return;

    input.value = '';

    const reader = new FileReader();
    reader.onload = (e) => {
        const container = document.getElementById('chat-messages');
        const div = document.createElement('div');
        div.className = 'message user photo-message';
        div.innerHTML = `<img src="${e.target.result}" alt="Uploaded photo" class="photo-preview">
                         <span>📷 Photo uploaded for analysis</span>`;
        container.appendChild(div);
        container.scrollTop = container.scrollHeight;
    };
    reader.readAsDataURL(file);

    showTypingIndicator();

    try {
        const formData = new FormData();
        formData.append('photo', file);

        const res = await fetch(`/api/session/${sessionId}/photo`, {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        removeTypingIndicator();

        if (data.error) {
            addMessage(`Photo analysis failed: ${data.error}`, 'assistant');
            return;
        }

        addMessage(`📷 Visual observation: ${data.observation}`, 'assistant');
        speakText(data.observation);

    } catch (err) {
        removeTypingIndicator();
        addMessage('Photo analysis failed. Please try again or describe the symptoms in text.', 'assistant');
        console.error('Photo upload error:', err);
    }
}

// ---------------------------------------------------------------------------
// Feature 4: Pet Profile Persistence
// ---------------------------------------------------------------------------

function _savePetProfile(profile) {
    if (!profile || !profile.species) return;
    try {
        const saved = {
            species: profile.species,
            pet_name: profile.pet_name || '',
            breed: profile.breed || '',
            age: profile.age || '',
            saved_at: new Date().toISOString()
        };
        localStorage.setItem('petcare_pet_profile', JSON.stringify(saved));
    } catch (_) { /* localStorage unavailable */ }
}

function _loadPetProfile() {
    try {
        const raw = localStorage.getItem('petcare_pet_profile');
        if (!raw) return;
        const profile = JSON.parse(raw);
        if (!profile.species) return;

        const daysSince = (Date.now() - new Date(profile.saved_at).getTime()) / 86400000;
        if (daysSince > 90) {
            localStorage.removeItem('petcare_pet_profile');
            return;
        }

        const name = profile.pet_name || profile.species;
        const container = document.getElementById('chat-messages');
        const div = document.createElement('div');
        div.className = 'message assistant pet-profile-prompt';
        div.innerHTML = `
            <div class="profile-prompt">
                <span>👋 Welcome back! Last time you told us about <strong>${name}</strong> (${profile.species}).</span>
                <div class="profile-actions">
                    <button onclick="_useSavedProfile()" class="action-btn-sm">Use this profile</button>
                    <button onclick="_clearSavedProfile(this.parentElement.parentElement.parentElement)" class="action-btn-sm secondary">New pet</button>
                </div>
            </div>`;
        container.appendChild(div);
    } catch (_) { /* localStorage unavailable */ }
}

function _useSavedProfile() {
    try {
        const raw = localStorage.getItem('petcare_pet_profile');
        if (!raw) return;
        const profile = JSON.parse(raw);

        let msg = `I have a ${profile.species}`;
        if (profile.pet_name) msg += ` named ${profile.pet_name}`;
        if (profile.breed) msg += `, ${profile.breed}`;
        if (profile.age) msg += `, ${profile.age} old`;

        document.getElementById('user-input').value = msg;

        const prompt = document.querySelector('.pet-profile-prompt');
        if (prompt) prompt.remove();
    } catch (_) {}
}

function _clearSavedProfile(el) {
    localStorage.removeItem('petcare_pet_profile');
    if (el) el.remove();
}

// ---------------------------------------------------------------------------
// Feature 5: Symptom History Tracker
// ---------------------------------------------------------------------------

function _saveSymptomHistory(summaryData) {
    try {
        const history = JSON.parse(localStorage.getItem('petcare_symptom_history') || '[]');
        const pet = summaryData.pet_profile || {};
        const out = summaryData.agent_outputs || {};
        const triage = (out.triage || {}).output || {};
        const symptoms = summaryData.symptoms || {};

        history.push({
            date: new Date().toISOString(),
            species: pet.species || '',
            pet_name: pet.pet_name || '',
            chief_complaint: symptoms.chief_complaint || '',
            urgency: triage.urgency_tier || '',
            session_id: sessionId
        });

        // Keep only last 20 entries
        if (history.length > 20) history.splice(0, history.length - 20);
        localStorage.setItem('petcare_symptom_history', JSON.stringify(history));
    } catch (_) {}
}

function _showSymptomHistory() {
    try {
        const raw = localStorage.getItem('petcare_symptom_history');
        if (!raw) return;
        const history = JSON.parse(raw);
        if (history.length === 0) return;

        const recent = history.slice(-5).reverse();
        const container = document.getElementById('chat-messages');
        const div = document.createElement('div');
        div.className = 'message assistant symptom-history';

        let html = '<div class="history-header">📋 Recent Visit History</div>';
        html += '<div class="history-entries">';
        for (const entry of recent) {
            const date = new Date(entry.date);
            const dateStr = date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
            const name = entry.pet_name || entry.species || 'Pet';
            const urgencyColors = {
                Emergency: '#dc2626', 'Same-day': '#f59e0b',
                Soon: '#d4ac0d', Routine: '#16a34a'
            };
            const color = urgencyColors[entry.urgency] || '#64748b';
            html += `
                <div class="history-entry">
                    <span class="history-date">${dateStr}</span>
                    <span class="history-pet">${name}</span>
                    <span class="history-complaint">${entry.chief_complaint}</span>
                    <span class="history-urgency" style="color:${color}">${entry.urgency}</span>
                </div>`;
        }
        html += '</div>';
        html += '<button onclick="this.parentElement.remove()" class="action-btn-sm secondary" style="margin-top:8px">Dismiss</button>';
        div.innerHTML = html;
        container.appendChild(div);
    } catch (_) {}
}

// ---------------------------------------------------------------------------
// Clinic Summary Panel
// ---------------------------------------------------------------------------

function _showClinicPanel(sumData) {
    const existing = document.getElementById('clinic-panel');
    if (existing) existing.remove();

    const metrics  = sumData.evaluation_metrics || {};
    const out      = sumData.agent_outputs || {};
    const triage   = (out.triage   || {}).output || {};
    const routing  = (out.routing  || {}).output || {};
    const sched    = (out.scheduling || {}).output || {};
    const pet      = sumData.pet_profile || {};

    const tier = triage.urgency_tier || 'Unknown';
    const tierColor = { Emergency: '#c0392b', 'Same-day': '#e67e22', Soon: '#d4ac0d', Routine: '#27ae60' }[tier] || '#7f8c8d';

    const slots = (sched.proposed_slots || []).slice(0, 3)
        .map(s => `<li style="margin:3px 0">${s.datetime || '—'} &nbsp;·&nbsp; ${s.provider || '—'}</li>`)
        .join('');

    const factors = (triage.contributing_factors || []).join(', ') || '—';
    const providers = (routing.providers || []).join(', ') || '—';
    const fieldsCapt = metrics.required_fields_captured_pct != null
        ? metrics.required_fields_captured_pct + '%' : '—';

    // Safely encode the full JSON for clipboard copy
    const jsonStr = JSON.stringify(sumData, null, 2).replace(/\\/g, '\\\\').replace(/`/g, '\\`');

    const panel = document.createElement('div');
    panel.id = 'clinic-panel';
    panel.style.cssText = 'border:1px solid #d0d0d0;border-radius:8px;margin:16px 0;background:#fafafa;overflow:hidden;font-size:14px;line-height:1.5;';
    panel.innerHTML = `
        <div id="clinic-panel-header" style="background:#2c3e50;color:white;padding:10px 16px;cursor:pointer;display:flex;justify-content:space-between;align-items:center;"
             onclick="const b=document.getElementById('clinic-panel-body');b.style.display=b.style.display==='none'?'block':'none';">
            <span>📋 <strong>Clinic Summary</strong> <span style="font-size:11px;opacity:0.75;font-weight:normal;">(staff view only — not shown to owner)</span></span>
            <span style="font-size:11px;opacity:0.7">click to expand / collapse</span>
        </div>
        <div id="clinic-panel-body" style="padding:14px 16px;">
            <table style="width:100%;border-collapse:collapse;margin-bottom:10px;">
                <tr><td style="padding:3px 8px 3px 0;color:#555;width:160px;">Pet</td>
                    <td><strong>${pet.species || '—'}</strong>${pet.pet_name ? ' &nbsp;"' + pet.pet_name + '"' : ''}${pet.age ? ' &nbsp;· Age: ' + pet.age : ''}${pet.breed ? ' &nbsp;· ' + pet.breed : ''}</td></tr>
                <tr><td style="padding:3px 8px 3px 0;color:#555;">Urgency</td>
                    <td><span style="background:${tierColor};color:white;padding:2px 12px;border-radius:12px;font-weight:bold;font-size:13px;">${tier}</span></td></tr>
                <tr><td style="padding:3px 8px 3px 0;color:#555;">Rationale</td>
                    <td style="color:#333;">${triage.rationale || '—'}</td></tr>
                <tr><td style="padding:3px 8px 3px 0;color:#555;">Key factors</td>
                    <td style="color:#333;">${factors}</td></tr>
                <tr><td style="padding:3px 8px 3px 0;color:#555;">Appt type</td>
                    <td>${routing.appointment_type || '—'}</td></tr>
                <tr><td style="padding:3px 8px 3px 0;color:#555;">Providers</td>
                    <td>${providers}</td></tr>
                <tr><td style="padding:3px 8px 3px 0;color:#555;">Fields captured</td>
                    <td>${fieldsCapt}</td></tr>
            </table>
            ${slots ? `<p style="margin:6px 0 3px;color:#555;">Proposed slots:</p><ul style="margin:0 0 10px 18px;padding:0;">${slots}</ul>` : ''}
            <p style="margin:4px 0 6px;font-size:12px;color:#888;">⚠ Triage is a suggestion only. Clinic staff must review and confirm before acting.</p>
            <button id="clinic-copy-btn"
                onclick="const j=\`${jsonStr}\`;navigator.clipboard.writeText(j).then(()=>{this.textContent='✓ Copied!';setTimeout(()=>this.textContent='Copy full JSON',2000);}).catch(()=>this.textContent='Copy failed');"
                style="padding:6px 16px;background:#2c3e50;color:white;border:none;border-radius:4px;cursor:pointer;font-size:13px;">
                Copy full JSON
            </button>
        </div>`;

    document.getElementById('chat-messages').appendChild(panel);
}

// ---------------------------------------------------------------------------
// Cost Estimator & Feedback
// ---------------------------------------------------------------------------

function _detectUrgencyTier(message) {
    if (!message) return 'Routine';
    if (/emergency/i.test(message)) return 'Emergency';
    if (/same[- ]?day/i.test(message)) return 'Same-day';
    if (/\bsoon\b/i.test(message)) return 'Soon';
    return 'Routine';
}

function _showCostEstimate(urgencyTier) {
    if (document.getElementById('cost-estimate')) return;

    const costRanges = {
        'Emergency': '$300 - $800+',
        'Same-day': '$150 - $400',
        'Soon': '$100 - $250',
        'Routine': '$50 - $150'
    };

    const tierColors = {
        'Emergency': '#dc2626',
        'Same-day': '#f59e0b',
        'Soon': '#d4ac0d',
        'Routine': '#16a34a'
    };

    const range = costRanges[urgencyTier] || costRanges['Routine'];
    const color = tierColors[urgencyTier] || tierColors['Routine'];

    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.id = 'cost-estimate';
    div.className = 'cost-estimate-card';
    div.innerHTML = `
        <div class="cost-estimate-header">
            <span class="cost-estimate-icon">💰</span>
            <span class="cost-estimate-title">Estimated Visit Cost</span>
        </div>
        <span class="urgency-badge" style="background:${color}">${urgencyTier}</span>
        <div class="cost-range">${range}</div>
        <div class="cost-note">Estimates vary by clinic and location</div>
    `;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function _showFeedbackPrompt() {
    if (document.getElementById('feedback-prompt')) return;

    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.id = 'feedback-prompt';
    div.className = 'feedback-prompt';
    div.innerHTML = `
        <div class="feedback-question">How helpful was this triage?</div>
        <div class="feedback-stars">
            ${[1,2,3,4,5].map(n =>
                `<button class="feedback-star" data-rating="${n}" onclick="_submitFeedback(${n})">⭐</button>`
            ).join('')}
        </div>
    `;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;

    const stars = div.querySelectorAll('.feedback-star');
    stars.forEach(star => {
        star.addEventListener('mouseenter', () => {
            const rating = parseInt(star.dataset.rating);
            stars.forEach(s => {
                s.classList.toggle('hover', parseInt(s.dataset.rating) <= rating);
            });
        });
        star.addEventListener('mouseleave', () => {
            stars.forEach(s => s.classList.remove('hover'));
        });
    });
}

function _submitFeedback(rating) {
    const stars = document.querySelectorAll('.feedback-star');
    stars.forEach(star => {
        const r = parseInt(star.dataset.rating);
        star.classList.toggle('active', r <= rating);
    });

    try {
        localStorage.setItem(`petcare_feedback_${sessionId}`, JSON.stringify({
            rating,
            session_id: sessionId,
            timestamp: new Date().toISOString()
        }));
    } catch (_) {}

    const prompt = document.getElementById('feedback-prompt');
    if (!prompt.querySelector('.feedback-thanks')) {
        const thanks = document.createElement('div');
        thanks.className = 'feedback-thanks';
        thanks.textContent = 'Thank you for your feedback!';
        prompt.appendChild(thanks);
    }
}

// ---------------------------------------------------------------------------
// Follow-up Appointment Reminders
// ---------------------------------------------------------------------------

function _showReminderPrompt() {
    if (document.getElementById('reminder-card')) return;

    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.id = 'reminder-card';
    div.className = 'reminder-card';
    div.innerHTML = `
        <div class="reminder-header">🔔 Set an appointment reminder?</div>
        <div class="reminder-options">
            <button class="reminder-option" onclick="_setReminder('1 day before', 86400000)">Day before</button>
            <button class="reminder-option" onclick="_setReminder('1 hour before', 3600000)">1 hour before</button>
            <button class="reminder-option" onclick="_setReminder('30 minutes before', 1800000)">30 min before</button>
            <button class="reminder-option test-btn" onclick="_setReminder('now (test)', 100)">🧪 Test now</button>
        </div>
    `;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function _setReminder(label, ms) {
    if (!('Notification' in window)) {
        addMessage('Browser notifications are not supported.', 'assistant');
        return;
    }

    Notification.requestPermission().then(permission => {
        if (permission !== 'granted') {
            addMessage('Please allow notifications to set reminders.', 'assistant');
            return;
        }

        setTimeout(() => {
            new Notification('🐾 PetCare Reminder', {
                body: `Your veterinary appointment is coming up${label === 'now (test)' ? ' (test notification)' : ''}!`,
                icon: '/icons/icon-192.svg'
            });
        }, ms);

        try {
            localStorage.setItem(`petcare_reminder_${sessionId}`, JSON.stringify({
                label, session_id: sessionId, set_at: new Date().toISOString()
            }));
        } catch (_) {}

        const card = document.getElementById('reminder-card');
        if (card && !card.querySelector('.reminder-confirmed')) {
            const conf = document.createElement('div');
            conf.className = 'reminder-confirmed';
            conf.textContent = `✓ Reminder set! You'll be notified ${label} your appointment.`;
            card.appendChild(conf);
        }
    });
}

// ---------------------------------------------------------------------------
// Breed-Specific Risk Alerts
// ---------------------------------------------------------------------------

function _checkBreedRisks(message) {
    if (!message) return;
    const lower = message.toLowerCase();

    for (const [breed, info] of Object.entries(BREED_RISKS)) {
        if (lower.includes(breed) && !_shownBreeds.has(breed)) {
            _shownBreeds.add(breed);
            const container = document.getElementById('chat-messages');
            const div = document.createElement('div');
            div.className = 'breed-risk-card';

            const displayBreed = breed.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
            div.innerHTML = `
                <div class="breed-risk-title">🧬 ${displayBreed} — Breed Health Insights</div>
                <ul class="breed-risk-list">
                    ${info.risks.map(r => `<li>${r}</li>`).join('')}
                </ul>
                <div class="breed-risk-tip">💡 ${info.tip}</div>
            `;
            container.appendChild(div);
            container.scrollTop = container.scrollHeight;
            break;
        }
    }
}

// ---------------------------------------------------------------------------
// Onboarding Walkthrough
// ---------------------------------------------------------------------------

let _onboardingStep = 1;

function checkOnboarding() {
    if (localStorage.getItem('petcare_onboarding_done')) return;
    const overlay = document.getElementById('onboarding-overlay');
    if (overlay) overlay.classList.remove('hidden');
}

function nextOnboardingStep() {
    const current = document.querySelector(`.onboarding-step[data-step="${_onboardingStep}"]`);
    if (current) current.classList.add('hidden');

    const currentDot = document.querySelector(`.onboarding-dot[data-dot="${_onboardingStep}"]`);
    if (currentDot) currentDot.classList.remove('active');

    _onboardingStep++;

    if (_onboardingStep > 3) {
        dismissOnboarding();
        return;
    }

    const next = document.querySelector(`.onboarding-step[data-step="${_onboardingStep}"]`);
    if (next) next.classList.remove('hidden');

    const nextDot = document.querySelector(`.onboarding-dot[data-dot="${_onboardingStep}"]`);
    if (nextDot) nextDot.classList.add('active');

    const btn = document.querySelector('.onboarding-next');
    if (_onboardingStep === 3 && btn) btn.textContent = 'Get Started';
}

function dismissOnboarding() {
    localStorage.setItem('petcare_onboarding_done', 'true');
    const overlay = document.getElementById('onboarding-overlay');
    if (overlay) {
        overlay.style.opacity = '0';
        setTimeout(() => overlay.remove(), 300);
    }
}
