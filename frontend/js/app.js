/**
 * PetCare Triage Assistant -- Frontend Logic
 *
 * Authors: Syed Ali Turab & Fergie Feng | Team: Broadview
 * Date:   March 1, 2026
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
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Detect language from URL param (?lang=fr) or browser preference
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
    document.getElementById('send-btn').textContent = lang.ui.sendBtn;
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

    const sendBtn = document.getElementById('send-btn');
    sendBtn.disabled = true;
    showTypingIndicator();

    try {
        const res = await fetch(`/api/session/${sessionId}/message`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, source, language: currentLang })
        });
        const data = await res.json();
        removeTypingIndicator();

        const isEmergency = data.emergency ||
            data.state === 'emergency' ||
            (data.message && data.message.includes('EMERGENCY'));

        addMessage(data.message, 'assistant', isEmergency);
        speakText(data.message);

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
 * Sets the Web Speech API language for Tier 1, or records
 * audio for Whisper transcription (Tier 2).
 */
async function startRecording() {
    isRecording = true;
    updateVoiceButton(true);

    if (voiceTier === 1 && speechRecognition) {
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

    if (voiceTier === 1 && speechRecognition) {
        speechRecognition.stop();
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
    div.textContent = text;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
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
