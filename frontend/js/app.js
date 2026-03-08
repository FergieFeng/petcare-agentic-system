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
            audioFail: 'Could not understand the audio. Please try again.',
            // Vet Finder
            findNearbyVets: '📍 Find Nearby Vets',
            searchingVets: '📍 Searching for nearby veterinary clinics...',
            noVetsFound: 'No veterinary clinics found within 10 km. Try expanding your search area.',
            nearbyVetsHeader: '🏥 Nearby Veterinary Clinics',
            openNow: '🟢 Open now',
            closed: '🔴 Closed',
            getDirections: '🗺️ Get Directions',
            call: '📞 Call',
            website: '🌐 Website',
            refreshResults: '🔄 Refresh results',
            noPhone: 'No phone listed',
            // Download/Export
            downloadSummary: '📄 Download Summary',
            downloadTranscript: '💬 Download Transcript',
            // Cost Estimator
            costEstimateTitle: '💰 Estimated Visit Cost',
            costEmergency: 'Emergency visit',
            costUrgent: 'Urgent care visit',
            costRoutine: 'Routine checkup',
            costNote: 'Actual costs may vary by clinic and location',
            // Feedback
            feedbackQuestion: 'How helpful was this triage?',
            feedbackThanks: 'Thank you for your feedback!',
            // Reminders
            reminderTitle: '🔔 Set an appointment reminder?',
            reminderDayBefore: 'Day before',
            reminder1Hour: '1 hour before',
            reminder30Min: '30 min before',
            reminderTest: '🧪 Test now',
            reminderSet: '✓ Reminder set! You\'ll be notified',
            reminderBody: 'Your veterinary appointment is coming up',
            reminderTestBody: '(test notification)',
            // Breed Risk
            breedRiskTitle: '🧬 {breed} — Breed Health Insights',
            breedRiskTip: '💡 Mention these to your vet during the visit',
            // History
            historyTitle: '📋 Recent Visit History',
            // Emergency
            emergencyBanner: '🚨 EMERGENCY — Please take your pet to an emergency veterinary clinic immediately. Do not wait.',
            // Photo
            photoUploaded: '📷 Photo uploaded for analysis',
            // Location fallback
            locationDenied: '📍 Location access was denied.',
            locationTimeout: '📍 Location request timed out.',
            locationUnavailable: '📍 Could not determine your location.',
            fallbackHint: 'You can still find vets by entering your location manually:',
            enterCity: '🏙️ Enter City/Postal Code',
            useDefaultLocation: '📍 Use Default (Toronto)',
            locationHelp: '💡 Tip: To enable location services on macOS, go to System Settings → Privacy & Security → Location Services',
            searchingCity: '🏙️ Searching for vets near',
            noVetsInCity: 'No veterinary clinics found near',
            // API Errors
            placesApiDisabled: '⚠️ The Google Places API needs to be enabled for your project. Visit your Google Cloud Console → APIs & Services → Enable "Places API (New)".',
            // Session / onboarding
            sessionExpired: 'Session expired. Reconnecting...',
            getStarted: 'Get Started',
            charCount: '{count} / 2000'
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
            audioFail: 'Impossible de comprendre l\'audio. Veuillez réessayer.',
            // Vet Finder
            findNearbyVets: '📍 Trouver des vétérinaires',
            searchingVets: '📍 Recherche de cliniques vétérinaires à proximité...',
            noVetsFound: 'Aucune clinique vétérinaire trouvée dans un rayon de 10 km. Essayez d\'étendre votre zone de recherche.',
            nearbyVetsHeader: '🏥 Cliniques Vétérinaires à Proximité',
            openNow: '🟢 Ouvert',
            closed: '🔴 Fermé',
            getDirections: '🗺️ Itinéraire',
            call: '📞 Appeler',
            website: '🌐 Site web',
            refreshResults: '🔄 Actualiser',
            noPhone: 'Pas de téléphone',
            // Download/Export
            downloadSummary: '📄 Télécharger le résumé',
            downloadTranscript: '💬 Télécharger la conversation',
            // Cost Estimator
            costEstimateTitle: '💰 Coût estimé de la visite',
            costEmergency: 'Visite d\'urgence',
            costUrgent: 'Soins urgents',
            costRoutine: 'Consultation de routine',
            costNote: 'Les coûts réels peuvent varier selon la clinique et l\'emplacement',
            // Feedback
            feedbackQuestion: 'Ce triage vous a-t-il été utile ?',
            feedbackThanks: 'Merci pour votre retour !',
            // Reminders
            reminderTitle: '🔔 Définir un rappel de rendez-vous ?',
            reminderDayBefore: 'La veille',
            reminder1Hour: '1 heure avant',
            reminder30Min: '30 min avant',
            reminderTest: '🧪 Tester maintenant',
            reminderSet: '✓ Rappel défini ! Vous serez notifié',
            reminderBody: 'Votre rendez-vous vétérinaire approche',
            reminderTestBody: '(notification test)',
            // Breed Risk
            breedRiskTitle: '🧬 {breed} — Insights de Santé de la Race',
            breedRiskTip: '💡 Mentionnez ces points à votre vétérinaire lors de la visite',
            // History
            historyTitle: '📋 Historique des Visites Récentes',
            // Emergency
            emergencyBanner: '🚨 URGENCE — Veuillez emmener votre animal immédiatement dans une clinique vétérinaire d\'urgence. N\'attendez pas.',
            // Photo
            photoUploaded: '📷 Photo téléchargée pour analyse',
            // Location fallback
            locationDenied: '📍 L\'accès à la localisation a été refusé.',
            locationTimeout: '📍 La demande de localisation a expiré.',
            locationUnavailable: '📍 Impossible de déterminer votre position.',
            fallbackHint: 'Vous pouvez toujours trouver des vétérinaires en saisissant votre localisation manuellement :',
            enterCity: '🏙️ Saisir ville/code postal',
            useDefaultLocation: '📍 Utiliser par défaut (Toronto)',
            locationHelp: '💡 Astuce : Pour activer les services de localisation sur macOS, allez dans Réglages Système → Confidentialité et sécurité → Services de localisation',
            searchingCity: '🏙️ Recherche de vétérinaires près de',
            noVetsInCity: 'Aucune clinique vétérinaire trouvée près de',
            // API Errors
            placesApiDisabled: '⚠️ L\'API Google Places doit être activée pour votre projet. Visitez Google Cloud Console → APIs et Services → Activez "Places API (New)".',
            sessionExpired: 'Session expirée. Reconnexion...',
            getStarted: 'Commencer',
            charCount: '{count} / 2000'
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
            audioFail: '无法理解音频。请重试。',
            // Vet Finder
            findNearbyVets: '📍 查找附近的兽医',
            searchingVets: '📍 正在搜索附近的兽医诊所...',
            noVetsFound: '10公里范围内未找到兽医诊所。请尝试扩大搜索范围。',
            nearbyVetsHeader: '🏥 附近兽医诊所',
            openNow: '🟢 营业中',
            closed: '🔴 休息中',
            getDirections: '🗺️ 获取路线',
            call: '📞 致电',
            website: '🌐 网站',
            refreshResults: '🔄 刷新结果',
            noPhone: '无电话号码',
            // Download/Export
            downloadSummary: '📄 下载摘要',
            downloadTranscript: '💬 下载对话记录',
            // Cost Estimator
            costEstimateTitle: '💰 预估就诊费用',
            costEmergency: '急诊',
            costUrgent: '紧急护理',
            costRoutine: '常规检查',
            costNote: '实际费用可能因诊所和地点而异',
            // Feedback
            feedbackQuestion: '这次分诊对您有帮助吗？',
            feedbackThanks: '感谢您的反馈！',
            // Reminders
            reminderTitle: '🔔 设置预约提醒？',
            reminderDayBefore: '前一天',
            reminder1Hour: '1小时前',
            reminder30Min: '30分钟前',
            reminderTest: '🧪 立即测试',
            reminderSet: '✓ 提醒已设置！您将收到通知',
            reminderBody: '您的兽医预约即将到来',
            reminderTestBody: '(测试通知)',
            // Breed Risk
            breedRiskTitle: '🧬 {breed} — 品种健康洞察',
            breedRiskTip: '💡 就诊时向兽医提及这些',
            // History
            historyTitle: '📋 近期就诊记录',
            // Emergency
            emergencyBanner: '🚨 紧急情况 — 请立即将您的宠物送往急诊兽医诊所。不要等待。',
            // Photo
            photoUploaded: '📷 照片已上传以供分析',
            // Location fallback
            locationDenied: '📍 位置访问被拒绝。',
            locationTimeout: '📍 位置请求超时。',
            locationUnavailable: '📍 无法确定您的位置。',
            fallbackHint: '您仍然可以通过手动输入位置来查找兽医：',
            enterCity: '🏙️ 输入城市/邮政编码',
            useDefaultLocation: '📍 使用默认位置（多伦多）',
            locationHelp: '💡 提示：要在macOS上启用位置服务，请前往系统设置 → 隐私与安全 → 定位服务',
            searchingCity: '🏙️ 正在搜索附近的兽医',
            noVetsInCity: '附近未找到兽医诊所',
            // API Errors
            placesApiDisabled: '⚠️ 需要为您的项目启用Google Places API。请访问Google Cloud Console → API和服务 → 启用"Places API (New)"。',
            sessionExpired: '会话已过期，正在重新连接...',
            getStarted: '开始',
            charCount: '{count} / 2000'
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
            audioFail: 'تعذر فهم الصوت. يرجى المحاولة مرة أخرى.',
            // Vet Finder
            findNearbyVets: '📍 البحث عن طبيب بيطري قريب',
            searchingVets: '📍 جاري البحث عن العيادات البيطرية القريبة...',
            noVetsFound: 'لم يتم العثور على عيادات بيطرية في نطاق 10 كم. حاول توسيع منطقة البحث.',
            nearbyVetsHeader: '🏥 العيادات البيطرية القريبة',
            openNow: '🟢 مفتوح الآن',
            closed: '🔴 مغلق',
            getDirections: '🗺️ الاتجاهات',
            call: '📞 اتصل',
            website: '🌐 الموقع',
            refreshResults: '🔄 تحديث النتائج',
            noPhone: 'لا يوجد هاتف',
            // Download/Export
            downloadSummary: '📄 تحميل الملخص',
            downloadTranscript: '💬 تحميل المحادثة',
            // Cost Estimator
            costEstimateTitle: '💰 تكلفة الزيارة المقدرة',
            costEmergency: 'زيارة طوارئ',
            costUrgent: 'رعاية عاجلة',
            costRoutine: 'فحص روتيني',
            costNote: 'قد تختلف التكاليف الفعلية حسب العيادة والموقع',
            // Feedback
            feedbackQuestion: 'هل كان هذا الفرز مفيداً؟',
            feedbackThanks: 'شكراً لملاحظاتك!',
            // Reminders
            reminderTitle: '🔔 تعيين تذكير بالموعد؟',
            reminderDayBefore: 'يوم قبل',
            reminder1Hour: 'ساعة قبل',
            reminder30Min: '٣٠ دقيقة قبل',
            reminderTest: '🧪 اختبار الآن',
            reminderSet: '✓ تم تعيين التذكير! سيتم إخطارك',
            reminderBody: 'موعدك البيطري اقترب',
            reminderTestBody: '(إشعار تجريبي)',
            // Breed Risk
            breedRiskTitle: '🧬 {breed} — رؤى صحة السلالة',
            breedRiskTip: '💡 اذكر هذه الأمور لطبيبك البيطري أثناء الزيارة',
            // History
            historyTitle: '📋 سجل الزيارات الأخيرة',
            // Emergency
            emergencyBanner: '🚨 حالة طوارئ — يرجى نقل حيوانك الأليف فوراً إلى عيادة طوارئ بيطرية. لا تنتظر.',
            // Photo
            photoUploaded: '📷 تم رفع الصورة للتحليل',
            // Location fallback
            locationDenied: '📍 تم رفض الوصول إلى الموقع.',
            locationTimeout: '📍 انتهت مهلة طلب الموقع.',
            locationUnavailable: '📍 تعذر تحديد موقعك.',
            fallbackHint: 'يمكنك البحث عن الأطباء البيطريين بإدخال موقعك يدوياً:',
            enterCity: '🏙️ أدخل المدينة/الرمز البريدي',
            useDefaultLocation: '📍 استخدم الموقع الافتراضي (تورنتو)',
            locationHelp: '💡 تلميح: لتمكين خدمات الموقع على macOS، انتقل إلى إعدادات النظام → الخصوصية والأمان → خدمات الموقع',
            searchingCity: '🏙️ جاري البحث عن أطباء بيطريين بالقرب من',
            noVetsInCity: 'لم يتم العثور على عيادات بيطرية بالقرب من',
            // API Errors
            placesApiDisabled: '⚠️ يجب تمكين Google Places API لمشروعك. قم بزيارة Google Cloud Console → APIs & Services → فعّل "Places API (New)".',
            sessionExpired: 'انتهت الجلسة. إعادة الاتصال...',
            getStarted: 'ابدأ',
            charCount: '{count} / 2000'
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
            audioFail: 'No se pudo entender el audio. Inténtelo de nuevo.',
            // Vet Finder
            findNearbyVets: '📍 Buscar veterinarios cercanos',
            searchingVets: '📍 Buscando clínicas veterinarias cercanas...',
            noVetsFound: 'No se encontraron clínicas veterinarias en un radio de 10 km. Intente ampliar su área de búsqueda.',
            nearbyVetsHeader: '🏥 Clínicas Veterinarias Cercanas',
            openNow: '🟢 Abierto',
            closed: '🔴 Cerrado',
            getDirections: '🗺️ Cómo llegar',
            call: '📞 Llamar',
            website: '🌐 Sitio web',
            refreshResults: '🔄 Actualizar',
            noPhone: 'Sin teléfono',
            // Download/Export
            downloadSummary: '📄 Descargar resumen',
            downloadTranscript: '💬 Descargar conversación',
            // Cost Estimator
            costEstimateTitle: '💰 Costo estimado de la visita',
            costEmergency: 'Visita de emergencia',
            costUrgent: 'Atención urgente',
            costRoutine: 'Chequeo de rutina',
            costNote: 'Los costos reales pueden variar según la clínica y la ubicación',
            // Feedback
            feedbackQuestion: '¿Le fue útil este triaje?',
            feedbackThanks: '¡Gracias por sus comentarios!',
            // Reminders
            reminderTitle: '🔔 ¿Establecer un recordatorio de cita?',
            reminderDayBefore: 'Día anterior',
            reminder1Hour: '1 hora antes',
            reminder30Min: '30 min antes',
            reminderTest: '🧪 Probar ahora',
            reminderSet: '✓ ¡Recordatorio establecido! Será notificado',
            reminderBody: 'Su cita veterinaria se acerca',
            reminderTestBody: '(notificación de prueba)',
            // Breed Risk
            breedRiskTitle: '🧬 {breed} — Perspectivas de Salud de la Raza',
            breedRiskTip: '💡 Mencione estos puntos a su veterinario durante la visita',
            // History
            historyTitle: '📋 Historial de Visitas Recientes',
            // Emergency
            emergencyBanner: '🚨 EMERGENCIA — Lleve a su mascota inmediatamente a una clínica veterinaria de emergencia. No espere.',
            // Photo
            photoUploaded: '📷 Foto subida para análisis',
            // Location fallback
            locationDenied: '📍 Se denegó el acceso a la ubicación.',
            locationTimeout: '📍 La solicitud de ubicación expiró.',
            locationUnavailable: '📍 No se pudo determinar su ubicación.',
            fallbackHint: 'Aún puede encontrar veterinarios ingresando su ubicación manualmente:',
            enterCity: '🏙️ Ingresar ciudad/código postal',
            useDefaultLocation: '📍 Usar ubicación predeterminada (Toronto)',
            locationHelp: '💡 Consejo: Para habilitar servicios de ubicación en macOS, vaya a Configuración del Sistema → Privacidad y Seguridad → Servicios de Ubicación',
            searchingCity: '🏙️ Buscando veterinarios cerca de',
            noVetsInCity: 'No se encontraron clínicas veterinarias cerca de',
            // API Errors
            placesApiDisabled: '⚠️ Se debe habilitar Google Places API para su proyecto. Visite Google Cloud Console → APIs y Servicios → Habilite "Places API (New)".',
            sessionExpired: 'Sesión expirada. Reconectando...',
            getStarted: 'Comenzar',
            charCount: '{count} / 2000'
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
            audioFail: 'ऑडियो समझ नहीं आया। कृपया पुनः प्रयास करें।',
            // Vet Finder
            findNearbyVets: '📍 पास के पशु चिकित्सक खोजें',
            searchingVets: '📍 पास के पशु चिकित्सा क्लिनिक खोज रहे हैं...',
            noVetsFound: '10 किमी की दूरी के भीतर कोई पशु चिकित्सा क्लिनिक नहीं मिला। अपने खोज क्षेत्र का विस्तार करने का प्रयास करें।',
            nearbyVetsHeader: '🏥 पास के पशु चिकित्सा क्लिनिक',
            openNow: '🟢 अभी खुला है',
            closed: '🔴 बंद',
            getDirections: '🗺️ दिशा-निर्देश',
            call: '📞 कॉल करें',
            website: '🌐 वेबसाइट',
            refreshResults: '🔄 रिफ्रेश करें',
            noPhone: 'कोई फोन नहीं',
            // Download/Export
            downloadSummary: '📄 सारांश डाउनलोड करें',
            downloadTranscript: '💬 बातचीत डाउनलोड करें',
            // Cost Estimator
            costEstimateTitle: '💰 अनुमानित विजिट लागत',
            costEmergency: 'आपातकालीन यात्रा',
            costUrgent: 'तत्काल देखभाल',
            costRoutine: 'नियमित जांच',
            costNote: 'वास्तविक लागत क्लिनिक और स्थान के अनुसार भिन्न हो सकती है',
            // Feedback
            feedbackQuestion: 'क्या यह ट्राइएज आपके लिए सहायक था?',
            feedbackThanks: 'आपकी प्रतिक्रिया के लिए धन्यवाद!',
            // Reminders
            reminderTitle: '🔔 अपॉइंटमेंट रिमाइंडर सेट करें?',
            reminderDayBefore: 'एक दिन पहले',
            reminder1Hour: '1 घंटे पहले',
            reminder30Min: '30 मिनट पहले',
            reminderTest: '🧪 अभी टेस्ट करें',
            reminderSet: '✓ रिमाइंडर सेट हो गया! आपको सूचित किया जाएगा',
            reminderBody: 'आपका पशु चिकित्सक नियुक्ति समय आ रहा है',
            reminderTestBody: '(टेस्ट सूचना)',
            // Breed Risk
            breedRiskTitle: '🧬 {breed} — नस्ल स्वास्थ्य अंतर्दृष्टि',
            breedRiskTip: '💡 विजिट के दौरान इन बिंदुओं का उल्लेख अपने पशु चिकित्सक से करें',
            // History
            historyTitle: '📋 हालिया विजिट इतिहास',
            // Emergency
            emergencyBanner: '🚨 आपातकाल — कृपया तुरंत अपने पालतू जानवर को आपातकालीन पशु चिकित्सा क्लिनिक ले जाएं। इंतजार न करें।',
            // Photo
            photoUploaded: '📷 विश्लेषण के लिए फोटो अपलोड किया गया',
            // Location fallback
            locationDenied: '📍 स्थान पहुंच अस्वीकार कर दी गई।',
            locationTimeout: '📍 स्थान अनुरोध का समय समाप्त हो गया।',
            locationUnavailable: '📍 आपका स्थान निर्धारित नहीं किया जा सका।',
            fallbackHint: 'आप अभी भी अपना स्थान मैन्युअल रूप से दर्ज करके पशु चिकित्सक खोज सकते हैं:',
            enterCity: '🏙️ शहर/पिन कोड दर्ज करें',
            useDefaultLocation: '📍 डिफ़ॉल्ट का उपयोग करें (टोरंटो)',
            locationHelp: '💡 टिप: macOS पर स्थान सेवाओं को सक्षम करने के लिए, सिस्टम सेटिंग्स → गोपनीयता और सुरक्षा → स्थान सेवाओं पर जाएं',
            searchingCity: '🏙️ पास के पशु चिकित्सक खोज रहे हैं',
            noVetsInCity: 'के पास कोई पशु चिकित्सा क्लिनिक नहीं मिला',
            // API Errors
            placesApiDisabled: '⚠️ आपकी परियोजना के लिए Google Places API को सक्षम करने की आवश्यकता है। Google Cloud Console → APIs & Services → "Places API (New)" सक्षम करें।',
            sessionExpired: 'सत्र समाप्त हो गया। पुनः कनेक्ट हो रहा है...',
            getStarted: 'शुरू करें',
            charCount: '{count} / 2000'
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
            audioFail: 'آڈیو سمجھ نہیں آئی۔ براہ کرم دوبارہ کوشش کریں۔',
            // Vet Finder
            findNearbyVets: '📍 قریب کے ویٹرنری ڈاکٹر تلاش کریں',
            searchingVets: '📍 قریب کے ویٹرنری کلینک تلاش کر رہے ہیں...',
            noVetsFound: '10 کلومیٹر کے فاصلے کے اندر کوئی ویٹرنری کلینک نہیں ملا۔ اپنا تلاش کا دائرہ بڑھانے کی کوشش کریں۔',
            nearbyVetsHeader: '🏥 قریب کے ویٹرنری کلینک',
            openNow: '🟢 ابھی کھلا ہے',
            closed: '🔴 بند',
            getDirections: '🗺️ سمتیں',
            call: '📞 کال کریں',
            website: '🌐 ویب سائٹ',
            refreshResults: '🔄 ریفریش کریں',
            noPhone: 'کوئی فون نہیں',
            // Download/Export
            downloadSummary: '📄 خلاصہ ڈاؤن لوڈ کریں',
            downloadTranscript: '💬 گفتگو ڈاؤن لوڈ کریں',
            // Cost Estimator
            costEstimateTitle: '💰 تخمینہ شدہ دورہ لاگت',
            costEmergency: 'ایمرجنسی دورہ',
            costUrgent: 'فوری دیکھ بھال',
            costRoutine: 'معمول کا معائنہ',
            costNote: 'اصل لاگت کلینک اور مقام کے لحاظ سے مختلف ہو سکتی ہے',
            // Feedback
            feedbackQuestion: 'کیا یہ ٹرائیج آپ کے لیے مددگار تھا؟',
            feedbackThanks: 'آپ کی رائے کا شکریہ!',
            // Reminders
            reminderTitle: '🔔 ملاقات کی یاد دہانی سیٹ کریں؟',
            reminderDayBefore: 'ایک دن پہلے',
            reminder1Hour: 'ایک گھنٹہ پہلے',
            reminder30Min: '30 منٹ پہلے',
            reminderTest: '🧪 ابھی ٹیسٹ کریں',
            reminderSet: '✓ یاد دہانی سیٹ ہو گئی! آپ کو مطلع کیا جائے گا',
            reminderBody: 'آپ کی ویٹرنری ملاقات قریب ہے',
            reminderTestBody: '(ٹیسٹ اطلاع)',
            // Breed Risk
            breedRiskTitle: '🧬 {breed} — نسل صحت کے بصیرت',
            breedRiskTip: '💡 دورے کے دوران ان باتوں کا ذکر اپنے ویٹرنری ڈاکٹر سے کریں',
            // History
            historyTitle: '📋 حالیہ دوروں کی تاریخ',
            // Emergency
            emergencyBanner: '🚨 ایمرجنسی — براہ کرم فوراً اپنے پالتو جانور کو ایمرجنسی ویٹرنری کلینک لے جائیں۔ انتظار نہ کریں۔',
            // Photo
            photoUploaded: '📷 تجزیے کے لیے تصویر اپ لوڈ کی گئی',
            // Location fallback
            locationDenied: '📍 مقام کی رسائی سے انکار کر دیا گیا۔',
            locationTimeout: '📍 مقام کی درخواست کا وقت ختم ہو گیا۔',
            locationUnavailable: '📍 آپ کا مقام طے نہیں کیا جا سکا۔',
            fallbackHint: 'آپ اب بھی اپنے مقام کو دستی طور پر درج کر کے ویٹرنری ڈاکٹر تلاش کر سکتے ہیں:',
            enterCity: '🏙️ شہر/پوسٹل کوڈ درج کریں',
            useDefaultLocation: '📍 ڈیفالٹ مقام استعمال کریں (ٹورنٹو)',
            locationHelp: '💡 ٹپ: macOS پر مقام کی خدمات کو فعال کرنے کے لیے، سسٹم سیٹنگز → رازداری اور سلامتی → مقام کی خدمات پر جائیں',
            searchingCity: '🏙️ قریب کے ویٹرنری ڈاکٹر تلاش کر رہے ہیں',
            noVetsInCity: 'کے قریب کوئی ویٹرنری کلینک نہیں ملا',
            // API Errors
            placesApiDisabled: '⚠️ آپ کے پروجیکٹ کے لیے Google Places API کو فعال کرنے کی ضرورت ہے۔ Google Cloud Console → APIs & Services → "Places API (New)" فعال کریں۔',
            sessionExpired: 'سیشن ختم ہو گیا۔ دوبارہ جوڑ رہا ہے...',
            getStarted: 'شروع کریں',
            charCount: '{count} / 2000'
        }
    }
};

/**
 * Get translated string for current language
 */
function t(key, replacements = {}) {
    const lang = LANGUAGES[currentLang] || LANGUAGES.en;
    let text = lang.ui[key] || LANGUAGES.en.ui[key] || key;
    
    // Replace placeholders like {breed}
    for (const [placeholder, value] of Object.entries(replacements)) {
        text = text.replace(`{${placeholder}}`, value);
    }
    
    return text;
}

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
let _currentTtsAudio = null;
let _ttsGeneration = 0;
let currentLang = 'en';
let lastTriageState = null;  // tracks post-triage state for action buttons
// AbortController for the in-flight /message fetch; cancels the previous
// request if the user sends another before the first response arrives.
let _sendController = null;
let _twilioEnabled = false;  // set on init by /api/twilio/status
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
const APP_VERSION = '2026.03.06d';

async function initApp() {
    console.log(`PetCare v${APP_VERSION} loaded`);
    const input = document.getElementById('user-input');
    checkOnboarding();
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Auto-grow textarea: expand height to fit content, up to CSS max-height.
    // Resets to min-height before measuring so shrinking also works.
    const MAX_CHARS = 2000;
    const charCounterEl = document.getElementById('char-counter');
    input.addEventListener('input', () => {
        // Auto-grow
        input.style.height = 'auto';
        input.style.height = input.scrollHeight + 'px';
        // Character counter
        const remaining = input.value.length;
        if (charCounterEl) {
            charCounterEl.textContent = t('charCount', { count: remaining });
            charCounterEl.classList.remove('near-limit', 'at-limit');
            if (remaining >= MAX_CHARS) {
                charCounterEl.classList.add('at-limit');
            } else if (remaining >= MAX_CHARS * 0.8) {
                charCounterEl.classList.add('near-limit');
            }
        }
        // Hard cap — prevent typing beyond limit
        if (remaining > MAX_CHARS) {
            input.value = input.value.slice(0, MAX_CHARS);
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
    _checkTwilioStatus();

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
    document.getElementById('chat-messages').innerHTML = '';

    try {
        const res = await fetch('/api/session/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ language: currentLang })
        });
        if (!res.ok) {
            console.error('Session start failed:', res.status, res.statusText);
            addMessage(t('connectError'), 'assistant');
            return;
        }
        const data = await res.json();
        sessionId = data.session_id;
        console.log('Session started:', sessionId);
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
    // Reset textarea height and char counter after clearing
    input.style.height = 'auto';
    const charCounterEl = document.getElementById('char-counter');
    if (charCounterEl) charCounterEl.textContent = '';

    addMessage(message, 'user');
    _checkBreedRisks(message);

    const sendBtn = document.getElementById('send-btn');
    sendBtn.disabled = true;
    showTypingIndicator();

    // Abort any previous in-flight request before starting a new one.
    // This prevents double-submission if the user sends quickly.
    if (_sendController) {
        _sendController.abort();
    }
    _sendController = new AbortController();

    try {
        const res = await fetch(`/api/session/${sessionId}/message`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, source, language: currentLang }),
            signal: _sendController.signal
        });

        if (!res.ok) {
            removeTypingIndicator();
            console.error('Message API error:', res.status, res.statusText);
            if (res.status === 404) {
                console.log('Session expired, reconnecting...');
                addMessage(t('sessionExpired'), 'assistant');
                await startSession();
                input.value = message;
                await sendMessage(source);
                return;
            }
            try {
                const errBody = await res.json();
                console.error('Error body:', errBody);
            } catch (_) { /* non-JSON error body */ }
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
                // Use CSS class instead of inline styles so dark mode theming applies
                banner.className = 'emergency-banner-bar';
                banner.textContent = t('emergencyBanner');
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
                console.error('Clinic summary error:', err);
            }
            try { _showActionButtons(); } catch (e) { console.error('Action buttons error:', e); }
            try {
                const urgencyTier = _detectUrgencyTier(data.message);
                _showCostEstimate(urgencyTier);
            } catch (e) { console.error('Cost estimate error:', e); }
            try { _showFeedbackPrompt(); } catch (e) { console.error('Feedback error:', e); }
        }

        if (data.state === 'booked') {
            try { _showActionButtons(); } catch (e) { console.error('Action buttons error:', e); }
            try { _showReminderPrompt(); } catch (e) { console.error('Reminder error:', e); }
        }

    } catch (err) {
        // AbortError is intentional (new message sent before response arrived) — ignore silently
        if (err.name === 'AbortError') return;
        removeTypingIndicator();
        addMessage(t('sendError'), 'assistant');
        console.error('Failed to send message:', err);
    } finally {
        _sendController = null;
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

    _stopAllAudio();
    const myGen = ++_ttsGeneration;

    if (voiceTier >= 2) {
        try {
            const res = await fetch('/api/voice/synthesize', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text,
                    voice: 'nova',
                    language: currentLang,
                    session_id: sessionId
                })
            });

            if (myGen !== _ttsGeneration) return;

            if (res.ok) {
                const audioBlob = await res.blob();
                if (myGen !== _ttsGeneration) return;

                const audioUrl = URL.createObjectURL(audioBlob);
                const audio = new Audio(audioUrl);
                _currentTtsAudio = audio;
                audio.onended = () => {
                    URL.revokeObjectURL(audioUrl);
                    if (_currentTtsAudio === audio) _currentTtsAudio = null;
                };
                audio.play().catch(() => {});
                return;
            }
        } catch (err) {
            if (myGen !== _ttsGeneration) return;
            console.warn('OpenAI TTS failed, falling back to browser:', err);
        }
    }

    if (myGen !== _ttsGeneration) return;

    if ('speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = LANGUAGES[currentLang].bcp47;
        utterance.rate = 0.95;
        utterance.pitch = 1.0;
        utterance.volume = 1.0;
        window.speechSynthesis.speak(utterance);
    }
}

function _stopAllAudio() {
    if (_currentTtsAudio) {
        _currentTtsAudio.pause();
        _currentTtsAudio.currentTime = 0;
        _currentTtsAudio = null;
    }
    if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
    }
}

/**
 * Toggle text-to-speech on/off.
 */
function toggleTTS() {
    ttsEnabled = !ttsEnabled;
    if (!ttsEnabled) _stopAllAudio();
    const ttsBtn = document.getElementById('tts-btn');
    if (ttsBtn) {
        const label = ttsEnabled ? t('speakerOn') : t('speakerOff');
        ttsBtn.textContent = ttsEnabled ? '🔊' : '🔇';
        ttsBtn.title = label;
        ttsBtn.setAttribute('aria-label', label);
    }
}

// ---------------------------------------------------------------------------
// UI Helpers – Scroll
// ---------------------------------------------------------------------------

/**
 * Check whether the chat container is scrolled near the bottom.
 * Used to avoid yanking the user back down when they are reading history.
 */
function _isNearBottom(threshold = 150) {
    const c = document.getElementById('chat-messages');
    return c.scrollHeight - c.scrollTop - c.clientHeight < threshold;
}

/**
 * Scroll the chat container to the very bottom.
 *
 * @param {'smooth'|'instant'} behavior – 'instant' during typing animation
 *        to avoid scroll-lag from CSS smooth-scroll; 'smooth' everywhere else.
 */
function _scrollToBottom(behavior = 'smooth') {
    const c = document.getElementById('chat-messages');
    c.scrollTo({ top: c.scrollHeight, behavior });
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
        _scrollToBottom();
    }
}

function _typeMessage(element, html, speed = 15) {
    let i = 0;
    const chunkSize = 3;

    function revealNext() {
        if (i >= html.length) {
            element.innerHTML = html;
            _scrollToBottom();
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

        _scrollToBottom('instant');

        setTimeout(revealNext, speed);
    }

    revealNext();
}

function _escapeHtml(str) {
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function _formatMessage(text) {
    if (!text) return '';
    let html = _escapeHtml(text);

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
    _scrollToBottom();
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
        voiceBtn.setAttribute('aria-label', t('voiceStop'));
    } else {
        voiceBtn.classList.remove('recording');
        voiceBtn.textContent = '🎤';
        voiceBtn.title = t('voiceStart');
        voiceBtn.setAttribute('aria-label', t('voiceStart'));
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
    const lang = LANGUAGES[currentLang] || LANGUAGES.en;
    div.innerHTML = `
        <button onclick="findNearbyVets()" class="action-btn vet-finder-btn">
            ${lang.ui.findNearbyVets}
        </button>
        <button onclick="downloadSummary()" class="action-btn export-btn">
            ${lang.ui.downloadSummary}
        </button>
        <button onclick="downloadTranscript()" class="action-btn export-btn">
            ${lang.ui.downloadTranscript}
        </button>
    `;
    container.appendChild(div);
    _scrollToBottom();

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
    _scrollToBottom();
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
        _showLocationFallback(2, 'Geolocation not supported');
        return;
    }

    // If location permission is already denied, skip straight to fallback
    if (navigator.permissions) {
        try {
            const perm = await navigator.permissions.query({ name: 'geolocation' });
            if (perm.state === 'denied') {
                _showLocationFallback(1, 'Permission denied');
                return;
            }
        } catch (_) { /* permissions API not supported — continue normally */ }
    }

    const existing = document.querySelector('.vet-results');
    if (existing) existing.remove();

    addMessage(t('searchingVets'), 'assistant');
    showTypingIndicator();

    try {
        const pos = await Promise.race([
            new Promise((resolve, reject) => {
                navigator.geolocation.getCurrentPosition(resolve, reject, {
                    enableHighAccuracy: false,
                    timeout: 15000,
                    maximumAge: 300000
                });
            }),
            new Promise((_, reject) =>
                setTimeout(() => reject({ code: 3, message: 'Location request timed out' }), 20000)
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
            const isApiDisabled = data.error.includes('not been used') || data.error.includes('disabled') || 
                                 data.error.includes('API has not been used') || data.error.includes('PERMISSION_DENIED');
            if (isApiDisabled) {
                addMessage(t('placesApiDisabled'), 'assistant');
            } else {
                addMessage(`${t('noVetsFound')}: ${data.error}`, 'assistant');
            }
            return;
        }

        if (!data.vets || data.vets.length === 0) {
            addMessage(t('noVetsFound'), 'assistant');
            return;
        }

        _renderVetResults(data.vets);

    } catch (err) {
        removeTypingIndicator();
        console.error('Geolocation error:', err);
        _showLocationFallback(err.code, err.message);
    }
}

/**
 * Show location fallback options when geolocation fails.
 * Inserts directly into the DOM to preserve interactive HTML buttons
 * (addMessage escapes HTML via _escapeHtml, so we bypass it here).
 */
function _showLocationFallback(code, message) {
    let errorKey = 'locationUnavailable';
    if (code === 1) {
        errorKey = 'locationDenied';
    } else if (code === 3 || (message && message.includes('timed out'))) {
        errorKey = 'locationTimeout';
    }

    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = 'message assistant';
    div.innerHTML = `
        <div class="location-fallback">
            <p>${t(errorKey)}</p>
            <p class="fallback-hint">${t('fallbackHint')}</p>
            <div class="fallback-options">
                <button onclick="_findVetsByCity()" class="fallback-btn">${t('enterCity')}</button>
                <button onclick="_findVetsDefaultLocation()" class="fallback-btn secondary">${t('useDefaultLocation')}</button>
            </div>
            <p class="fallback-help">${t('locationHelp')}</p>
        </div>
    `;
    container.appendChild(div);
    _scrollToBottom();
}

/**
 * Find vets by city/postal code (manual entry)
 */
async function _findVetsByCity() {
    const promptText = currentLang === 'en' ? 'Enter your city or postal code:' :
                      currentLang === 'fr' ? 'Entrez votre ville ou code postal :' :
                      currentLang === 'es' ? 'Ingrese su ciudad o código postal:' :
                      currentLang === 'zh' ? '请输入您的城市或邮政编码：' :
                      currentLang === 'hi' ? 'अपना शहर या पिन कोड दर्ज करें:' :
                      currentLang === 'ar' ? 'أدخل مدينتك أو الرمز البريدي:' :
                      currentLang === 'ur' ? 'اپنا شہر یا پوسٹل کوڈ درج کریں:' : 'Enter your city or postal code:';
    const city = prompt(promptText);
    if (!city) return;

    addMessage(`${t('searchingCity')} "${city}"...`, 'assistant');
    showTypingIndicator();

    try {
        // Use a geocoding API to convert city to coordinates
        // For POC, we'll use OpenStreetMap's free Nominatim API
        const geoRes = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(city)}&limit=1`);
        const geoData = await geoRes.json();

        removeTypingIndicator();

        if (!geoData || geoData.length === 0) {
            addMessage(`❌ Could not find location "${city}". Please try a different city or postal code.`, 'assistant');
            return;
        }

        const { lat, lon: lng } = geoData[0];
        const res = await fetch('/api/nearby-vets', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ lat: parseFloat(lat), lng: parseFloat(lng), radius_km: 10 })
        });
        const data = await res.json();

        if (data.error) {
            addMessage(`Could not find nearby vets: ${data.error}`, 'assistant');
            return;
        }

        if (!data.vets || data.vets.length === 0) {
            addMessage(`${t('noVetsInCity')} "${city}".`, 'assistant');
            return;
        }

        _renderVetResults(data.vets);
    } catch (err) {
        removeTypingIndicator();
        const errorMsg = currentLang === 'en' ? '❌ Error searching for location. Please try again.' :
                        currentLang === 'fr' ? '❌ Erreur lors de la recherche de localisation. Veuillez réessayer.' :
                        currentLang === 'es' ? '❌ Error al buscar la ubicación. Inténtelo de nuevo.' :
                        currentLang === 'zh' ? '❌ 搜索位置时出错。请重试。' :
                        currentLang === 'hi' ? '❌ स्थान खोजने में त्रुटि। कृपया पुनः प्रयास करें।' :
                        currentLang === 'ar' ? '❌ خطأ في البحث عن الموقع. يرجى المحاولة مرة أخرى.' :
                        currentLang === 'ur' ? '❌ مقام تلاش کرنے میں خرابی۔ براہ کرم دوبارہ کوشش کریں۔' : '❌ Error searching for location. Please try again.';
        addMessage(errorMsg, 'assistant');
        console.error('City search error:', err);
    }
}

/**
 * Find vets using a default location (Toronto)
 */
async function _findVetsDefaultLocation() {
    const defaultMsg = currentLang === 'en' ? '📍 Using default location (Toronto, ON) to show nearby vets...' :
                      currentLang === 'fr' ? '📍 Utilisation de la localisation par défaut (Toronto) pour afficher les vétérinaires...' :
                      currentLang === 'es' ? '📍 Usando ubicación predeterminada (Toronto) para mostrar veterinarios...' :
                      currentLang === 'zh' ? '📍 使用默认位置（多伦多）显示附近的兽医...' :
                      currentLang === 'hi' ? '📍 डिफ़ॉल्ट स्थान (टोरंटो) का उपयोग करके पास के पशु चिकित्सक दिखा रहे हैं...' :
                      currentLang === 'ar' ? '📍 استخدام الموقع الافتراضي (تورنتو) لعرض الأطباء البيطريين...' :
                      currentLang === 'ur' ? '📍 ڈیفالٹ مقام (ٹورنٹو) استعمال کرکے قریب کے ویٹرنری ڈاکٹر دکھا رہے ہیں...' : '📍 Using default location (Toronto, ON) to show nearby vets...';
    addMessage(defaultMsg, 'assistant');
    showTypingIndicator();

    try {
        // Toronto coordinates
        const lat = 43.6532;
        const lng = -79.3832;

        const res = await fetch('/api/nearby-vets', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ lat, lng, radius_km: 10 })
        });
        const data = await res.json();
        removeTypingIndicator();

        if (data.error) {
            const isApiDisabled = data.error.includes('not been used') || data.error.includes('disabled') || 
                                 data.error.includes('PERMISSION_DENIED');
            if (isApiDisabled) {
                addMessage(t('placesApiDisabled'), 'assistant');
            } else {
                addMessage(`${t('noVetsFound')}: ${data.error}`, 'assistant');
            }
            return;
        }

        if (!data.vets || data.vets.length === 0) {
            addMessage(t('noVetsFound'), 'assistant');
            return;
        }

        _renderVetResults(data.vets);
    } catch (err) {
        removeTypingIndicator();
        const errorMsg = currentLang === 'en' ? '❌ Could not load vet finder. Please try again later.' :
                        currentLang === 'fr' ? '❌ Impossible de charger le recherche. Veuillez réessayer.' :
                        currentLang === 'es' ? '❌ No se pudo cargar el buscador. Inténtelo de nuevo.' :
                        currentLang === 'zh' ? '❌ 无法加载兽医查找器。请稍后重试。' :
                        currentLang === 'hi' ? '❌ वेट फाइंडर लोड नहीं हो सका। कृपया बाद में पुनः प्रयास करें।' :
                        currentLang === 'ar' ? '❌ تعذر تحميل الباحث. يرجى المحاولة لاحقاً.' :
                        currentLang === 'ur' ? '❌ ویٹ فائنڈر لوڈ نہیں ہو سکا۔ براہ کرم بعد میں دوبارہ کوشش کریں۔' : '❌ Could not load vet finder. Please try again later.';
        addMessage(errorMsg, 'assistant');
        console.error('Default location error:', err);
    }
}

function _renderVetResults(vets) {
    const container = document.getElementById('chat-messages');
    const wrapper = document.createElement('div');
    wrapper.className = 'message assistant vet-results';

    // Translations for vet card elements
    const kmAway = currentLang === 'en' ? 'km away' :
                  currentLang === 'fr' ? 'km' :
                  currentLang === 'es' ? 'km de distancia' :
                  currentLang === 'zh' ? '公里远' :
                  currentLang === 'hi' ? 'किमी दूर' :
                  currentLang === 'ar' ? 'كم' :
                  currentLang === 'ur' ? 'کلومیٹر دور' : 'km away';
    
    const reviewsText = currentLang === 'en' ? 'reviews' :
                       currentLang === 'fr' ? 'avis' :
                       currentLang === 'es' ? 'reseñas' :
                       currentLang === 'zh' ? '评论' :
                       currentLang === 'hi' ? 'समीक्षाएं' :
                       currentLang === 'ar' ? 'تقييمات' :
                       currentLang === 'ur' ? 'جائزے' : 'reviews';

    let html = `<div class="vet-results-header">${t('nearbyVetsHeader')}</div>`;
    html += '<div class="vet-cards">';

    for (const vet of vets.slice(0, 5)) {
        const stars = vet.rating ? '⭐'.repeat(Math.round(vet.rating)) : '';
        const ratingText = vet.rating ? `${vet.rating}/5 (${vet.total_ratings} ${reviewsText})` : 
                           currentLang === 'en' ? 'No ratings' :
                           currentLang === 'fr' ? 'Pas d\'avis' :
                           currentLang === 'es' ? 'Sin reseñas' :
                           currentLang === 'zh' ? '无评分' :
                           currentLang === 'hi' ? 'कोई रेटिंग नहीं' :
                           currentLang === 'ar' ? 'لا تقييمات' :
                           currentLang === 'ur' ? 'کوئی درجہ بندی نہیں' : 'No ratings';
        const statusClass = vet.open_now ? 'open' : 'closed';
        const statusText = vet.open_now === true ? t('openNow') : vet.open_now === false ? t('closed') : '';
        const mapsLink = vet.maps_url
            ? `<a href="${vet.maps_url}" target="_blank" rel="noopener" class="vet-directions-btn">${t('getDirections')}</a>`
            : '';

        const callText = currentLang === 'en' ? 'Call' :
                         currentLang === 'fr' ? 'Appeler' :
                         currentLang === 'es' ? 'Llamar' :
                         currentLang === 'zh' ? '致电' :
                         currentLang === 'hi' ? 'कॉल करें' :
                         currentLang === 'ar' ? 'اتصل' :
                         currentLang === 'ur' ? 'کال کریں' : 'Call';
        const callBtn = vet.phone
            ? `<a href="tel:${_escapeHtml(vet.phone)}" class="vet-call-btn">📞 ${callText} ${_escapeHtml(vet.phone)}</a>`
            : `<span class="vet-no-phone">${t('noPhone')}</span>`;

        const twilioBtn = (vet.phone && _twilioEnabled)
            ? `<button onclick="_twilioCall('${_escapeHtml(vet.phone)}')" class="vet-call-btn twilio-call-btn">📲 ${callText} via app</button>`
            : '';

        const websiteLink = vet.website
            ? `<a href="${vet.website}" target="_blank" rel="noopener" class="vet-website-btn">${t('website')}</a>`
            : '';

        const hoursInfo = vet.hours_today
            ? `<div class="vet-hours">🕐 ${_escapeHtml(vet.hours_today)}</div>`
            : '';

        html += `
            <div class="vet-card">
                <div class="vet-card-header">
                    <div>
                        <div class="vet-name">${_escapeHtml(vet.name)}</div>
                        <div class="vet-address">${_escapeHtml(vet.address)}</div>
                    </div>
                    ${statusText ? `<span class="vet-status-badge ${statusClass}">${statusText}</span>` : ''}
                </div>
                <div class="vet-meta">
                    <span class="vet-distance">${vet.distance_km} ${kmAway}</span>
                    <span class="vet-rating">${stars} ${ratingText}</span>
                </div>
                ${hoursInfo}
                <div class="vet-actions">
                    ${callBtn}
                    ${twilioBtn}
                    ${mapsLink}
                    ${websiteLink}
                </div>
            </div>`;
    }

    html += '</div>';
    html += `<div class="vet-results-footer">
        <button onclick="findNearbyVets()" class="action-btn-sm secondary">${t('refreshResults')}</button>
    </div>`;
    wrapper.innerHTML = html;
    container.appendChild(wrapper);
    _scrollToBottom();
}

// ---------------------------------------------------------------------------
// Twilio Click-to-Call
// ---------------------------------------------------------------------------

async function _checkTwilioStatus() {
    try {
        const res = await fetch('/api/twilio/status');
        const data = await res.json();
        _twilioEnabled = !!data.enabled;
    } catch (_) {
        _twilioEnabled = false;
    }
}

async function _twilioCall(clinicPhone) {
    const promptText = currentLang === 'en' ? 'Enter your phone number (with country code, e.g. +1234567890):' :
                       currentLang === 'fr' ? 'Entrez votre numéro de téléphone (avec indicatif, ex: +1234567890) :' :
                       currentLang === 'es' ? 'Ingrese su número de teléfono (con código de país, ej: +1234567890):' :
                       'Enter your phone number (with country code, e.g. +1234567890):';
    const userPhone = prompt(promptText);
    if (!userPhone) return;

    try {
        const res = await fetch('/api/call', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ clinic_phone: clinicPhone, user_phone: userPhone.trim() })
        });
        const data = await res.json();
        if (data.error) {
            addMessage(data.error, 'assistant');
        } else {
            addMessage(currentLang === 'en' ? 'Calling your phone now — answer to be connected to the clinic.' :
                       currentLang === 'fr' ? 'Appel en cours — répondez pour être connecté à la clinique.' :
                       currentLang === 'es' ? 'Llamando a tu teléfono — contesta para ser conectado con la clínica.' :
                       'Calling your phone now — answer to be connected to the clinic.', 'assistant');
        }
    } catch (_) {
        addMessage(t('sendError'), 'assistant');
    }
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
        div.innerHTML = `<img src="${e.target.result}" alt="${currentLang === 'en' ? 'Uploaded photo' : t('photoUploaded').replace('📷 ', '')}" class="photo-preview">
                         <span>${t('photoUploaded')}</span>`;
        container.appendChild(div);
        _scrollToBottom();
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

        let html = `<div class="history-header">${t('historyTitle')}</div>`;
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
                    <span class="history-date">${_escapeHtml(dateStr)}</span>
                    <span class="history-pet">${_escapeHtml(name)}</span>
                    <span class="history-complaint">${_escapeHtml(entry.chief_complaint || '')}</span>
                    <span class="history-urgency" style="color:${color}">${_escapeHtml(entry.urgency || '')}</span>
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
        .map(s => `<li style="margin:3px 0">${_escapeHtml(s.datetime || '—')} &nbsp;·&nbsp; ${_escapeHtml(s.provider || '—')}</li>`)
        .join('');

    const factors = (triage.contributing_factors || []).join(', ') || '—';
    const providers = (routing.providers || []).join(', ') || '—';
    const fieldsCapt = metrics.required_fields_captured_pct != null
        ? metrics.required_fields_captured_pct + '%' : '—';

    const panel = document.createElement('div');
    panel.id = 'clinic-panel';
    panel.style.cssText = 'border:1px solid #d0d0d0;border-radius:8px;margin:16px 0;background:#fafafa;overflow:hidden;font-size:14px;line-height:1.5;';
    panel.innerHTML = `
        <div id="clinic-panel-header" style="background:#2c3e50;color:white;padding:10px 16px;cursor:pointer;display:flex;justify-content:space-between;align-items:center;"
             onclick="const b=document.getElementById('clinic-panel-body');b.style.display=b.style.display==='none'?'block':'none';">
            <span>📋 <strong>Clinic Summary</strong> <span style="font-size:11px;opacity:0.75;font-weight:normal;">(staff view only)</span></span>
            <span style="font-size:11px;opacity:0.7">click to expand / collapse</span>
        </div>
        <div id="clinic-panel-body" style="padding:14px 16px;">
            <table style="width:100%;border-collapse:collapse;margin-bottom:10px;">
                <tr><td style="padding:3px 8px 3px 0;color:#555;width:160px;">Pet</td>
                    <td><strong>${_escapeHtml(pet.species || '—')}</strong>${pet.pet_name ? ' &nbsp;"' + _escapeHtml(pet.pet_name) + '"' : ''}${pet.age ? ' &nbsp;· Age: ' + _escapeHtml(pet.age) : ''}${pet.breed ? ' &nbsp;· ' + _escapeHtml(pet.breed) : ''}</td></tr>
                <tr><td style="padding:3px 8px 3px 0;color:#555;">Urgency</td>
                    <td><span style="background:${tierColor};color:white;padding:2px 12px;border-radius:12px;font-weight:bold;font-size:13px;">${_escapeHtml(tier)}</span></td></tr>
                <tr><td style="padding:3px 8px 3px 0;color:#555;">Rationale</td>
                    <td style="color:#333;">${_escapeHtml(triage.rationale || '—')}</td></tr>
                <tr><td style="padding:3px 8px 3px 0;color:#555;">Key factors</td>
                    <td style="color:#333;">${_escapeHtml(factors)}</td></tr>
                <tr><td style="padding:3px 8px 3px 0;color:#555;">Appt type</td>
                    <td>${_escapeHtml(routing.appointment_type || '—')}</td></tr>
                <tr><td style="padding:3px 8px 3px 0;color:#555;">Providers</td>
                    <td>${_escapeHtml(providers)}</td></tr>
                <tr><td style="padding:3px 8px 3px 0;color:#555;">Fields captured</td>
                    <td>${fieldsCapt}</td></tr>
            </table>
            ${slots ? `<p style="margin:6px 0 3px;color:#555;">Proposed slots:</p><ul style="margin:0 0 10px 18px;padding:0;">${slots}</ul>` : ''}
            <p style="margin:4px 0 6px;font-size:12px;color:#888;">⚠ Triage is a suggestion only. Clinic staff must review and confirm before acting.</p>
            <button id="clinic-copy-btn"
                style="padding:6px 16px;background:#2c3e50;color:white;border:none;border-radius:4px;cursor:pointer;font-size:13px;">
                Copy full JSON
            </button>
        </div>`;

    panel.querySelector('#clinic-copy-btn').addEventListener('click', function() {
        const json = JSON.stringify(sumData, null, 2);
        navigator.clipboard.writeText(json)
            .then(() => { this.textContent = '✓ Copied!'; setTimeout(() => this.textContent = 'Copy full JSON', 2000); })
            .catch(() => { this.textContent = 'Copy failed'; });
    });

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
    _scrollToBottom();
}

function _showFeedbackPrompt() {
    if (document.getElementById('feedback-prompt')) return;

    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.id = 'feedback-prompt';
    div.className = 'feedback-prompt';
    div.innerHTML = `
        <div class="feedback-question">${t('feedbackQuestion')}</div>
        <div class="feedback-stars">
            ${[1,2,3,4,5].map(n =>
                `<button class="feedback-star" data-rating="${n}" onclick="_submitFeedback(${n})">⭐</button>`
            ).join('')}
        </div>
    `;
    container.appendChild(div);
    _scrollToBottom();

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
        thanks.textContent = t('feedbackThanks');
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
    _scrollToBottom();
}

function _setReminder(label, ms) {
    if (!('Notification' in window)) {
        const notSupportedMsg = currentLang === 'en' ? 'Browser notifications are not supported.' :
                               currentLang === 'fr' ? 'Les notifications du navigateur ne sont pas prises en charge.' :
                               currentLang === 'es' ? 'Las notificaciones del navegador no están soportadas.' :
                               currentLang === 'zh' ? '浏览器不支持通知。' :
                               currentLang === 'hi' ? 'ब्राउज़र सूचनाएं समर्थित नहीं हैं।' :
                               currentLang === 'ar' ? 'إشعارات المتصفح غير مدعومة.' :
                               currentLang === 'ur' ? 'براؤزر نوٹیفیکیشنز معاونت یافتہ نہیں ہیں۔' : 'Browser notifications are not supported.';
        addMessage(notSupportedMsg, 'assistant');
        return;
    }

    Notification.requestPermission().then(permission => {
        if (permission !== 'granted') {
            const allowMsg = currentLang === 'en' ? 'Please allow notifications to set reminders.' :
                             currentLang === 'fr' ? 'Veuillez autoriser les notifications pour définir des rappels.' :
                             currentLang === 'es' ? 'Por favor permita notificaciones para establecer recordatorios.' :
                             currentLang === 'zh' ? '请允许通知以设置提醒。' :
                             currentLang === 'hi' ? 'रिमाइंडर सेट करने के लिए कृपया सूचनाएं अनुमत करें।' :
                             currentLang === 'ar' ? 'يرجى السماح بالإشعارات لتعيين التذكيرات.' :
                             currentLang === 'ur' ? 'یاد دہانیاں سیٹ کرنے کے لیے براہ کرم اطلاعات کی اجازت دیں۔' : 'Please allow notifications to set reminders.';
            addMessage(allowMsg, 'assistant');
            return;
        }

        const isTest = label.toLowerCase().includes('test');
        setTimeout(() => {
            new Notification('🐾 PetCare Reminder', {
                body: isTest ? `${t('reminderBody')} ${t('reminderTestBody')}` : t('reminderBody'),
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
            conf.textContent = `✓ ${t('reminderSet')} ${label}.`;
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
            // Note: Breed health risks are displayed in English as they're medical terms
            // But we translate the title and the "mention to your vet" tip
            const tipText = t('breedRiskTip');
            div.innerHTML = `
                <div class="breed-risk-title">${t('breedRiskTitle', { breed: displayBreed })}</div>
                <ul class="breed-risk-list">
                    ${info.risks.map(r => `<li>${r}</li>`).join('')}
                </ul>
                <div class="breed-risk-tip">${tipText}</div>
            `;
            container.appendChild(div);
            _scrollToBottom();
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
    if (_onboardingStep === 3 && btn) btn.textContent = t('getStarted');
}

function dismissOnboarding() {
    localStorage.setItem('petcare_onboarding_done', 'true');
    const overlay = document.getElementById('onboarding-overlay');
    if (overlay) {
        overlay.style.opacity = '0';
        setTimeout(() => overlay.remove(), 300);
    }
}
