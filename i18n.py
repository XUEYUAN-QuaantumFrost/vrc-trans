"""
多语言支持模块
支持: 简体中文, 繁體中文, 英语, 日语, 韩语, 法语, 德语, 西班牙语, 俄语, 葡萄牙语
自动检测系统语言
"""
from PyQt5.QtCore import QLocale

# 支持的语言列表 (code, 中文名, 英文名, 日文名, 韩文名, 法文名, 德文名, 西文名, 俄文名, 葡文名)
LANGUAGES = [
    ("auto", "跟随系统", "Auto (System)", "自動", "자동", "Auto", "Auto", "Auto", "Авто", "Auto"),
    ("zh", "简体中文", "Chinese (Simplified)", "簡体字中国語", "간체 중국어", "Chinois simplifié", "Vereinfachtes Chinesisch", "Chino simplificado", "Упрощенный китайский", "Chinês simplificado"),
    ("zh-tw", "繁體中文", "Chinese (Traditional)", "繁体字中国語", "번체 중국어", "Chinois traditionnel", "Traditionelles Chinesisch", "Chino tradicional", "Традиционный китайский", "Chinês tradicional"),
    ("en", "英语", "English", "英語", "영어", "Anglais", "Englisch", "Inglés", "Английский", "Inglês"),
    ("ja", "日语", "Japanese", "日本語", "일본어", "Japonais", "Japanisch", "Japonés", "Японский", "Japonês"),
    ("ko", "韩语", "Korean", "韓国語", "한국어", "Coréen", "Koreanisch", "Coreano", "Корейский", "Coreano"),
    ("fr", "法语", "French", "フランス語", "프랑스어", "Français", "Französisch", "Francés", "Французский", "Francês"),
    ("de", "德语", "German", "ドイツ語", "독일어", "Allemand", "Deutsch", "Alemán", "Немецкий", "Alemão"),
    ("es", "西班牙语", "Spanish", "スペイン語", "스페인어", "Espagnol", "Spanisch", "Español", "Испанский", "Espanhol"),
    ("ru", "俄语", "Russian", "ロシア語", "러시아어", "Russe", "Russisch", "Ruso", "Русский", "Russo"),
    ("pt", "葡萄牙语", "Portuguese", "ポルトガル語", "포르투갈어", "Portugais", "Portugiesisch", "Portugués", "Португальский", "Português"),
]

# 翻译字典：key -> {lang: translation}
TRANSLATIONS = {
    # ===== 托盘菜单 =====
    "hide_subtitle": {
        "zh": "隐藏悬浮窗", "zh-tw": "隱藏懸浮窗", "en": "Hide Subtitle", "ja": "サブタイトルを隠す",
        "ko": "자막 숨기기", "fr": "Masquer le sous-titre", "de": "Untertitel ausblenden",
        "es": "Ocultar subtítulo", "ru": "Скрыть субтитры", "pt": "Ocultar legenda",
    },
    "show_subtitle": {
        "zh": "显示悬浮窗", "zh-tw": "顯示懸浮窗", "en": "Show Subtitle", "ja": "サブタイトルを表示",
        "ko": "자막 보이기", "fr": "Afficher le sous-titre", "de": "Untertitel anzeigen",
        "es": "Mostrar subtítulo", "ru": "Показать субтитры", "pt": "Mostrar legenda",
    },
    "lock_position": {
        "zh": "锁定位置", "zh-tw": "鎖定位置", "en": "Lock Position", "ja": "位置をロック",
        "ko": "위치 잠금", "fr": "Verrouiller la position", "de": "Position sperren",
        "es": "Bloquear posición", "ru": "Заблокировать позицию", "pt": "Bloquear posição",
    },
    "unlock_position": {
        "zh": "解锁位置", "zh-tw": "解鎖位置", "en": "Unlock Position", "ja": "位置をアンロック",
        "ko": "위치 잠금 해제", "fr": "Déverrouiller la position", "de": "Position entsperren",
        "es": "Desbloquear posición", "ru": "Разблокировать позицию", "pt": "Desbloquear posição",
    },
    "settings": {
        "zh": "设置...", "zh-tw": "設定...", "en": "Settings...", "ja": "設定...",
        "ko": "설정...", "fr": "Paramètres...", "de": "Einstellungen...",
        "es": "Ajustes...", "ru": "Настройки...", "pt": "Configurações...",
    },
    "font": {
        "zh": "字体...", "zh-tw": "字型...", "en": "Font...", "ja": "フォント...",
        "ko": "글꼴...", "fr": "Police...", "de": "Schriftart...",
        "es": "Fuente...", "ru": "Шрифт...", "pt": "Fonte...",
    },
    "subtitle_color": {
        "zh": "字幕颜色", "zh-tw": "字幕顏色", "en": "Subtitle Color", "ja": "字幕カラー",
        "ko": "자막 색상", "fr": "Couleur du sous-titre", "de": "Untertittelfarbe",
        "es": "Color de subtítulo", "ru": "Цвет субтитров", "pt": "Cor da legenda",
    },
    "original_color": {
        "zh": "原文颜色...", "zh-tw": "原文顏色...", "en": "Original Color...", "ja": "原文カラー...",
        "ko": "원문 색상...", "fr": "Couleur originale...", "de": "Originalfarbe...",
        "es": "Color original...", "ru": "Цвет оригинала...", "pt": "Cor original...",
    },
    "translate_color": {
        "zh": "翻译颜色...", "zh-tw": "翻譯顏色...", "en": "Translate Color...", "ja": "翻訳カラー...",
        "ko": "번역 색상...", "fr": "Couleur de traduction...", "de": "Übersetzungsfarbe...",
        "es": "Color de traducción...", "ru": "Цвет перевода...", "pt": "Cor da tradução...",
    },
    "bg_color": {
        "zh": "背景颜色...", "zh-tw": "背景顏色...", "en": "Background Color...", "ja": "背景カラー...",
        "ko": "배경 색상...", "fr": "Couleur de fond...", "de": "Hintergrundfarbe...",
        "es": "Color de fondo...", "ru": "Цвет фона...", "pt": "Cor de fundo...",
    },
    "bg_opacity": {
        "zh": "背景透明度...", "zh-tw": "背景透明度...", "en": "Background Opacity...", "ja": "背景透明度...",
        "ko": "배경 투명도...", "fr": "Opacité du fond...", "de": "Hintergrundtransparenz...",
        "es": "Opacidad de fondo...", "ru": "Прозрачность фона...", "pt": "Opacidade do fundo...",
    },
    "manual_input": {
        "zh": "手动输入文字...", "zh-tw": "手動輸入文字...", "en": "Manual Input...", "ja": "手動入力...",
        "ko": "수동 입력...", "fr": "Saisie manuelle...", "de": "Manuelle Eingabe...",
        "es": "Entrada manual...", "ru": "Ручной ввод...", "pt": "Entrada manual...",
    },
    "history_window": {
        "zh": "历史记录...", "zh-tw": "歷史記錄...", "en": "History...", "ja": "履歴...",
        "ko": "기록...", "fr": "Historique...", "de": "Verlauf...",
        "es": "Historial...", "ru": "История...", "pt": "Histórico...",
    },
    "ai_chat": {
        "zh": "AI 代聊...", "zh-tw": "AI 代聊...", "en": "AI Chat...", "ja": "AIチャット...",
        "ko": "AI 채팅...", "fr": "Chat IA...", "de": "KI-Chat...",
        "es": "Chat con IA...", "ru": "ИИ-чат...", "pt": "Chat com IA...",
    },
    "quit": {
        "zh": "退出", "zh-tw": "退出", "en": "Quit", "ja": "終了",
        "ko": "종료", "fr": "Quitter", "de": "Beenden",
        "es": "Salir", "ru": "Выход", "pt": "Sair",
    },
    # ===== 托盘提示 =====
    "tray_title": {
        "zh": "VRChat 翻译悬浮字幕", "zh-tw": "VRChat 翻譯懸浮字幕", "en": "VRC Translate Subtitle", "ja": "VRChat 翻訳サブタイトル",
        "ko": "VRChat 번역 자막", "fr": "Sous-titre de traduction VRC", "de": "VRC Übersetzungs-Untertitel",
        "es": "Subtítulo de traducción VRC", "ru": "Субтитры перевода VRC", "pt": "Legenda de tradução VRC",
    },
    "tray_started": {
        "zh": "已启动，右键托盘图标进行设置", "zh-tw": "已啟動，右鍵托盤圖示進行設定", "en": "Started. Right-click tray icon to configure.",
        "ja": "起動しました。トレイアイコンを右クリックで設定", "ko": "시작됨. 트레이 아이콘 우클릭으로 설정",
        "fr": "Démarré. Clic droit sur l'icône pour configurer.", "de": "Gestartet. Rechtsklick auf das Tray-Symbol zum Konfigurieren.",
        "es": "Iniciado. Haz clic derecho en el icono para configurar.", "ru": "Запущено. Щёлкните правой кнопкой по иконке для настройки.",
        "pt": "Iniciado. Clique com o botão direito no ícone para configurar.",
    },
    "settings_saved": {
        "zh": "配置已保存", "zh-tw": "配置已儲存", "en": "Settings saved", "ja": "設定を保存しました",
        "ko": "설정이 저장되었습니다", "fr": "Paramètres enregistrés", "de": "Einstellungen gespeichert",
        "es": "Ajustes guardados", "ru": "Настройки сохранены", "pt": "Configurações salvas",
    },
    "config_saved": {
        "zh": "设置", "zh-tw": "設定", "en": "Settings", "ja": "設定",
        "ko": "설정", "fr": "Paramètres", "de": "Einstellungen",
        "es": "Ajustes", "ru": "Настройки", "pt": "Configurações",
    },
    # ===== 设置面板 =====
    "dialog_title": {
        "zh": "设置", "zh-tw": "設定", "en": "Settings", "ja": "設定",
        "ko": "설정", "fr": "Paramètres", "de": "Einstellungen",
        "es": "Ajustes", "ru": "Настройки", "pt": "Configurações",
    },
    "tab_translate": {"zh": "翻译", "zh-tw": "翻譯", "en": "Translate", "ja": "翻訳", "ko": "번역", "fr": "Traduction", "de": "Übersetzung", "es": "Traducción", "ru": "Перевод", "pt": "Tradução"},
    "tab_osc": {"zh": "OSC", "zh-tw": "OSC", "en": "OSC", "ja": "OSC", "ko": "OSC", "fr": "OSC", "de": "OSC", "es": "OSC", "ru": "OSC", "pt": "OSC"},
    "tab_speech": {"zh": "语音识别", "zh-tw": "語音辨識", "en": "Speech", "ja": "音声認識", "ko": "음성 인식", "fr": "Reconnaissance vocale", "de": "Spracherkennung", "es": "Reconocimiento de voz", "ru": "Распознавание речи", "pt": "Reconhecimento de voz"},
    "tab_appearance": {"zh": "外观", "zh-tw": "外觀", "en": "Appearance", "ja": "外観", "ko": "외관", "fr": "Apparence", "de": "Darstellung", "es": "Apariencia", "ru": "Внешний вид", "pt": "Aparência"},
    "tab_history": {"zh": "历史记录", "zh-tw": "歷史記錄", "en": "History", "ja": "履歴", "ko": "기록", "fr": "Historique", "de": "Verlauf", "es": "Historial", "ru": "История", "pt": "Histórico"},
    "api_key": {"zh": "API Key:", "zh-tw": "API Key:", "en": "API Key:", "ja": "APIキー:", "ko": "API 키:", "fr": "Clé API :", "de": "API-Schlüssel:", "es": "Clave API:", "ru": "API-ключ:", "pt": "Chave de API:"},
    "api_base": {"zh": "API 地址:", "zh-tw": "API 位址:", "en": "API URL:", "ja": "API URL:", "ko": "API 주소:", "fr": "URL API :", "de": "API-URL:", "es": "URL de API:", "ru": "URL API:", "pt": "URL da API:"},
    "model": {"zh": "模型:", "zh-tw": "模型:", "en": "Model:", "ja": "モデル:", "ko": "모델:", "fr": "Modèle :", "de": "Modell:", "es": "Modelo:", "ru": "Модель:", "pt": "Modelo:"},
    "target_lang": {"zh": "目标语言:", "zh-tw": "目標語言:", "en": "Target Language:", "ja": "対象言語:", "ko": "대상 언어:", "fr": "Langue cible :", "de": "Zielsprache:", "es": "Idioma objetivo:", "ru": "Целевой язык:", "pt": "Idioma de destino:"},
    "custom_prompt": {"zh": "自定义提示词:", "zh-tw": "自訂提示詞:", "en": "Custom Prompt:", "ja": "カスタムプロンプト:", "ko": "사용자 프롬프트:", "fr": "Prompt personnalisé :", "de": "Benutzerdefinierter Prompt:", "es": "Prompt personalizado:", "ru": "Пользовательский промпт:", "pt": "Prompt personalizado:"},
    "enable_translate": {
        "zh": "启用 AI 翻译（关闭则仅原文输出）", "zh-tw": "啟用 AI 翻譯（關閉則僅原文輸出）", "en": "Enable AI Translate (off = original only)",
        "ja": "AI翻訳を有効化（オフ時は原文のみ）", "ko": "AI 번역 활성화 (끄면 원문만 출력)",
        "fr": "Activer la traduction IA (désactivé = original uniquement)", "de": "AI-Übersetzung aktivieren (aus = nur Original)",
        "es": "Activar traducción IA (desactivado = solo original)", "ru": "Включить перевод ИИ (выкл. = только оригинал)",
        "pt": "Ativar tradução por IA (desligado = apenas original)",
    },
    "enable_osc": {
        "zh": "启用 OSC 发送到 VRChat", "zh-tw": "啟用 OSC 發送到 VRChat", "en": "Enable OSC to VRChat",
        "ja": "VRChatへのOSC送信を有効化", "ko": "VRChat으로 OSC 전송 활성화",
        "fr": "Activer l'envoi OSC vers VRChat", "de": "OSC-Senden an VRChat aktivieren",
        "es": "Activar envío OSC a VRChat", "ru": "Включить отправку OSC в VRChat",
        "pt": "Ativar envio OSC para VRChat",
    },
    "osc_ip": {"zh": "OSC IP:", "zh-tw": "OSC IP:", "en": "OSC IP:", "ja": "OSC IP:", "ko": "OSC IP:", "fr": "IP OSC :", "de": "OSC-IP:", "es": "IP de OSC:", "ru": "OSC IP:", "pt": "IP do OSC:"},
    "osc_port": {"zh": "OSC 端口:", "zh-tw": "OSC 連接埠:", "en": "OSC Port:", "ja": "OSCポート:", "ko": "OSC 포트:", "fr": "Port OSC :", "de": "OSC-Port:", "es": "Puerto OSC:", "ru": "Порт OSC:", "pt": "Porta do OSC:"},
    "osc_bilingual_group": {"zh": "双语 OSC", "zh-tw": "雙語 OSC", "en": "Bilingual OSC", "ja": "バイリンガルOSC", "ko": "양면 언어 OSC", "fr": "OSC bilingue", "de": "Zweisprachiges OSC", "es": "OSC bilingüe", "ru": "Двуязычный OSC", "pt": "OSC bilíngue"},
    "enable_osc_bilingual": {
        "zh": "启用双语 OSC（原文+翻译一起发送）", "zh-tw": "啟用雙語 OSC（原文+翻譯一起發送）", "en": "Enable bilingual OSC (send original + translation)",
        "ja": "バイリンガルOSCを有効化（原文＋翻訳を同時送信）", "ko": "양면 언어 OSC 활성화 (원문+번역 동시 전송)",
        "fr": "Activer l'OSC bilingue (envoyer original + traduction)", "de": "Zweisprachiges OSC aktivieren (Original + Übersetzung senden)",
        "es": "Activar OSC bilingüe (enviar original + traducción)", "ru": "Включить двуязычный OSC (отправлять оригинал + перевод)",
        "pt": "Ativar OSC bilíngue (enviar original + tradução)",
    },
    "osc_bilingual_format": {"zh": "双语格式:", "zh-tw": "雙語格式:", "en": "Bilingual format:", "ja": "バイリンガル形式:", "ko": "양면 언어 형식:", "fr": "Format bilingue :", "de": "Zweisprachiges Format:", "es": "Formato bilingüe:", "ru": "Формат двуязычия:", "pt": "Formato bilíngue:"},
    "osc_format_multiline": {"zh": "多行（每行一种语言）", "zh-tw": "多行（每行一種語言）", "en": "Multiline (one language per line)", "ja": "複数行（1行1言語）", "ko": "여러 줄 (줄당 하나의 언어)", "fr": "Multiligne (une langue par ligne)", "de": "Mehrzeilig (eine Sprache pro Zeile)", "es": "Multilínea (un idioma por línea)", "ru": "Многострочно (по строкам)", "pt": "Multilinha (um idioma por linha)"},
    "osc_format_parenthesis": {"zh": "括号（原文 (翻译)）", "zh-tw": "括號（原文 (翻譯)）", "en": "Parenthesis (original (trans))", "ja": "括弧（原文 (翻訳)）", "ko": "괄호 (원문 (번역))", "fr": "Parenthèse (original (trad))", "de": "Klammer (Original (Übers.))", "es": "Paréntesis (original (trad))", "ru": "Скобки (оригинал (перевод))", "pt": "Parêntese (original (trad))"},
    "osc_format_slash": {"zh": "斜杠（原文 / 翻译）", "zh-tw": "斜線（原文 / 翻譯）", "en": "Slash (original / trans)", "ja": "スラッシュ（原文 / 翻訳）", "ko": "슬래시 (원문 / 번역)", "fr": "Slash (original / trad)", "de": "Schrägstrich (Original / Übers.)", "es": "Barra (original / trad)", "ru": "Слеш (оригинал / перевод)", "pt": "Barra (original / trad)"},
    "osc_format_translate_only": {"zh": "仅翻译", "zh-tw": "僅翻譯", "en": "Translate only", "ja": "翻訳のみ", "ko": "번역만", "fr": "Traduction uniquement", "de": "Nur Übersetzung", "es": "Solo traducción", "ru": "Только перевод", "pt": "Apenas tradução"},
    "osc_bilingual_order": {"zh": "显示顺序:", "zh-tw": "顯示順序:", "en": "Display order:", "ja": "表示順序:", "ko": "표시 순서:", "fr": "Ordre d'affichage :", "de": "Anzeigereihenfolge:", "es": "Orden de visualización:", "ru": "Порядок отображения:", "pt": "Ordem de exibição:"},
    "osc_order_original_first": {"zh": "原文在前", "zh-tw": "原文在前", "en": "Original first", "ja": "原文先行", "ko": "원문 먼저", "fr": "Original d'abord", "de": "Original zuerst", "es": "Original primero", "ru": "Сначала оригинал", "pt": "Original primeiro"},
    "osc_order_translate_first": {"zh": "翻译在前", "zh-tw": "翻譯在前", "en": "Translate first", "ja": "翻訳先行", "ko": "번역 먼저", "fr": "Traduction d'abord", "de": "Übersetzung zuerst", "es": "Traducción primero", "ru": "Сначала перевод", "pt": "Tradução primeiro"},
    "enable_osc_typing": {
        "zh": "启用打字指示器（翻译时显示正在输入）", "zh-tw": "啟用打字指示器（翻譯時顯示正在輸入）", "en": "Enable typing indicator (show typing while translating)",
        "ja": "タイピングインジケーターを有効化（翻訳中は入力中表示）", "ko": "타이핑 표시기 활성화 (번역 중 입력 중 표시)",
        "fr": "Activer l'indicateur de frappe (afficher pendant la traduction)", "de": "Tippindikator aktivieren (während Übersetzung anzeigen)",
        "es": "Activar indicador de escritura (mostrar mientras se traduce)", "ru": "Включить индикатор печати (показывать во время перевода)",
        "pt": "Ativar indicador de digitação (mostrar durante tradução)",
    },
    "auto_send_group": {"zh": "自动发送", "zh-tw": "自動發送", "en": "Auto Send", "ja": "自動送信", "ko": "자동 전송", "fr": "Envoi automatique", "de": "Automatisches Senden", "es": "Envío automático", "ru": "Автоотправка", "pt": "Envio automático"},
    "enable_auto_send": {
        "zh": "识别完成后自动翻译并发送", "zh-tw": "辨識完成後自動翻譯並發送", "en": "Auto translate & send after recognition",
        "ja": "認識後に自動翻訳＆送信", "ko": "인식 후 자동 번역 및 전송",
        "fr": "Traduire et envoyer automatiquement après reconnaissance", "de": "Automatisch übersetzen & senden nach Erkennung",
        "es": "Traducir y enviar automáticamente tras el reconocimiento", "ru": "Автоперевод и отправка после распознавания",
        "pt": "Traduzir e enviar automaticamente após o reconhecimento",
    },
    "send_delay": {"zh": "发送延迟:", "zh-tw": "發送延遲:", "en": "Send Delay:", "ja": "送信遅延:", "ko": "전송 지연:", "fr": "Délai d'envoi :", "de": "Sendeverzögerung:", "es": "Retardo de envío:", "ru": "Задержка отправки:", "pt": "Atraso de envio:"},
    "enable_auto_activate": {
        "zh": "自动激活输入框（防焦点丢失）", "zh-tw": "自動啟用輸入框（防焦點遺失）", "en": "Auto-activate input (prevent focus loss)",
        "ja": "入力欄を自動アクティブ化（フォーカス喪失防止）", "ko": "입력창 자동 활성화 (포커스 손실 방지)",
        "fr": "Activer automatiquement la saisie (éviter la perte de focus)", "de": "Eingabe automatisch aktivieren (Fokusverlust vermeiden)",
        "es": "Activar entrada automáticamente (evitar pérdida de foco)", "ru": "Автоактивация ввода (предотвратить потерю фокуса)",
        "pt": "Ativar entrada automaticamente (evitar perda de foco)",
    },
    "activate_interval": {"zh": "激活间隔:", "zh-tw": "啟用間隔:", "en": "Activate Interval:", "ja": "アクティブ間隔:", "ko": "활성화 간격:", "fr": "Intervalle d'activation :", "de": "Aktivierungsintervall:", "es": "Intervalo de activación:", "ru": "Интервал активации:", "pt": "Intervalo de ativação:"},
    "enable_speech": {
        "zh": "启用实时语音识别", "zh-tw": "啟用即時語音辨識", "en": "Enable Real-time Speech Recognition",
        "ja": "リアルタイム音声認識を有効化", "ko": "실시간 음성 인식 활성화",
        "fr": "Activer la reconnaissance vocale en temps réel", "de": "Echtzeit-Spracherkennung aktivieren",
        "es": "Activar reconocimiento de voz en tiempo real", "ru": "Включить распознавание речи в реальном времени",
        "pt": "Ativar reconhecimento de voz em tempo real",
    },
    "record_source": {"zh": "录音来源:", "zh-tw": "錄音來源:", "en": "Record Source:", "ja": "録音ソース:", "ko": "녹음 소스:", "fr": "Source d'enregistrement :", "de": "Aufnahmequelle:", "es": "Fuente de grabación:", "ru": "Источник записи:", "pt": "Fonte de gravação:"},
    "source_computer": {
        "zh": "电脑声音（立体声混音）- 适合VRC/看视频", "zh-tw": "電腦聲音（立體聲混音）- 適合VRC/看影片", "en": "Computer Audio (Stereo Mix) - for VRC/video",
        "ja": "コンピュータ音声（ステレオミックス）- VRC/動画向け", "ko": "컴퓨터 소리 (스테레오 믹스) - VRC/영상용",
        "fr": "Audio de l'ordinateur (Stéréo Mix) - pour VRC/vidéo", "de": "Computer-Audio (Stereo-Mix) - für VRC/Video",
        "es": "Audio del ordenador (Mezcla estéreo) - para VRC/vídeo", "ru": "Звук компьютера (Стерео-микс) - для VRC/видео",
        "pt": "Áudio do computador (Mistura estéreo) - para VRC/vídeo",
    },
    "source_mic": {
        "zh": "麦克风 - 适合线下/面对面翻译", "zh-tw": "麥克風 - 適合線下/面對面翻譯", "en": "Microphone - for in-person translation",
        "ja": "マイク - 対面翻訳向け", "ko": "마이크 - 대면 번역용",
        "fr": "Microphone - pour traduction en personne", "de": "Mikrofon - für Übersetzung vor Ort",
        "es": "Micrófono - para traducción presencial", "ru": "Микрофон - для устного перевода",
        "pt": "Microfone - para tradução presencial",
    },
    "device_computer": {"zh": "立体声混音设备编号:", "zh-tw": "立體聲混音裝置編號:", "en": "Stereo Mix Device ID:", "ja": "ステレオミックスデバイスID:", "ko": "스테레오 믹스 장치 ID:", "fr": "ID du périphérique Stéréo Mix :", "de": "Stereo-Mix Geräte-ID:", "es": "ID de dispositivo Mezcla estéreo:", "ru": "ID устройства Стерео-микс:", "pt": "ID do dispositivo Mistura estéreo:"},
    "device_mic": {"zh": "麦克风设备编号:", "zh-tw": "麥克風裝置編號:", "en": "Microphone Device ID:", "ja": "マイクデバイスID:", "ko": "마이크 장치 ID:", "fr": "ID du périphérique Microphone :", "de": "Mikrofon Geräte-ID:", "es": "ID de dispositivo Micrófono:", "ru": "ID устройства Микрофон:", "pt": "ID do dispositivo Microfone:"},
    "device_hint": {
        "zh": "运行 list_devices.py 可查看设备编号", "zh-tw": "執行 list_devices.py 可查看裝置編號", "en": "Run list_devices.py to find device IDs",
        "ja": "list_devices.py を実行してデバイスIDを確認", "ko": "list_devices.py를 실행하여 장치 ID 확인",
        "fr": "Exécutez list_devices.py pour trouver les ID", "de": "Führen Sie list_devices.py aus, um Geräte-IDs zu finden",
        "es": "Ejecuta list_devices.py para ver los IDs", "ru": "Запустите list_devices.py для поиска ID устройств",
        "pt": "Execute list_devices.py para encontrar os IDs",
    },
    "engine": {"zh": "识别引擎:", "zh-tw": "辨識引擎:", "en": "Engine:", "ja": "認識エンジン:", "ko": "인식 엔진:", "fr": "Moteur :", "de": "Engine:", "es": "Motor:", "ru": "Движок:", "pt": "Motor:"},
    "engine_faster": {"zh": "faster-whisper（推荐，快4倍）", "zh-tw": "faster-whisper（推薦，快4倍）", "en": "faster-whisper (recommended, 4x faster)", "ja": "faster-whisper（推奨、4倍速）", "ko": "faster-whisper (추천, 4배 빠름)", "fr": "faster-whisper (recommandé, 4x plus rapide)", "de": "faster-whisper (empfohlen, 4x schneller)", "es": "faster-whisper (recomendado, 4x más rápido)", "ru": "faster-whisper (рекомендуется, в 4 раза быстрее)", "pt": "faster-whisper (recomendado, 4x mais rápido)"},
    "engine_openai": {"zh": "openai-whisper（原版）", "zh-tw": "openai-whisper（原版）", "en": "openai-whisper (original)", "ja": "openai-whisper（オリジナル）", "ko": "openai-whisper (원본)", "fr": "openai-whisper (original)", "de": "openai-whisper (Original)", "es": "openai-whisper (original)", "ru": "openai-whisper (оригинал)", "pt": "openai-whisper (original)"},
    "model_size": {"zh": "模型大小:", "zh-tw": "模型大小:", "en": "Model Size:", "ja": "モデルサイズ:", "ko": "모델 크기:", "fr": "Taille du modèle :", "de": "Modellgröße:", "es": "Tamaño del modelo:", "ru": "Размер модели:", "pt": "Tamanho do modelo:"},
    "run_device": {"zh": "运行设备:", "zh-tw": "執行裝置:", "en": "Device:", "ja": "実行デバイス:", "ko": "실행 장치:", "fr": "Périphérique :", "de": "Gerät:", "es": "Dispositivo:", "ru": "Устройство:", "pt": "Dispositivo:"},
    "compute_type": {"zh": "计算精度:", "zh-tw": "計算精度:", "en": "Compute Type:", "ja": "計算精度:", "ko": "연산 정밀도:", "fr": "Type de calcul :", "de": "Berechnungstyp:", "es": "Tipo de cálculo:", "ru": "Тип вычислений:", "pt": "Tipo de cálculo:"},
    "compute_int8": {"zh": "int8（CPU推荐）", "zh-tw": "int8（CPU推薦）", "en": "int8 (CPU recommended)", "ja": "int8（CPU推奨）", "ko": "int8 (CPU 추천)", "fr": "int8 (CPU recommandé)", "de": "int8 (CPU empfohlen)", "es": "int8 (CPU recomendado)", "ru": "int8 (рекомендуется для CPU)", "pt": "int8 (recomendado para CPU)"},
    "compute_fp16": {"zh": "float16（GPU推荐）", "zh-tw": "float16（GPU推薦）", "en": "float16 (GPU recommended)", "ja": "float16（GPU推奨）", "ko": "float16 (GPU 추천)", "fr": "float16 (GPU recommandé)", "de": "float16 (GPU empfohlen)", "es": "float16 (GPU recomendado)", "ru": "float16 (рекомендуется для GPU)", "pt": "float16 (recomendado para GPU)"},
    "compute_fp32": {"zh": "float32", "zh-tw": "float32", "en": "float32", "ja": "float32", "ko": "float32", "fr": "float32", "de": "float32", "es": "float32", "ru": "float32", "pt": "float32"},
    "vad_group": {"zh": "断句参数（webrtcvad）", "zh-tw": "斷句參數（webrtcvad）", "en": "VAD Parameters (webrtcvad)", "ja": "区切りパラメータ（webrtcvad）", "ko": "문장 구분 파라미터 (webrtcvad)", "fr": "Paramètres VAD (webrtcvad)", "de": "VAD-Parameter (webrtcvad)", "es": "Parámetros VAD (webrtcvad)", "ru": "Параметры VAD (webrtcvad)", "pt": "Parâmetros de VAD (webrtcvad)"},
    "vad_aggressive": {"zh": "VAD灵敏度:", "zh-tw": "VAD靈敏度:", "en": "VAD Aggressiveness:", "ja": "VAD感度:", "ko": "VAD 민감도:", "fr": "Sensibilité VAD :", "de": "VAD-Aggressivität:", "es": "Sensibilidad VAD:", "ru": "Агрессивность VAD:", "pt": "Sensibilidade do VAD:"},
    "silence_threshold": {"zh": "静音阈值(句末):", "zh-tw": "靜音閾值(句末):", "en": "Silence Threshold:", "ja": "無音閾値（文末）:", "ko": "침묵 임계값 (문장 끝):", "fr": "Seuil de silence :", "de": "Silence-Schwelle:", "es": "Umbral de silencio:", "ru": "Порог тишины:", "pt": "Limiar de silêncio:"},
    "min_speech": {"zh": "最短说话时长:", "zh-tw": "最短說話時長:", "en": "Min Speech Duration:", "ja": "最短発話時間:", "ko": "최소 발화 시간:", "fr": "Durée min. de parole :", "de": "Min. Sprechdauer:", "es": "Duración mín. de habla:", "ru": "Мин. длительность речи:", "pt": "Duração mín. da fala:"},
    "max_speech": {"zh": "最长说话时长(强制切断):", "zh-tw": "最長說話時長(強制切斷):", "en": "Max Speech Duration (force cut):", "ja": "最長発話時間（強制切断）:", "ko": "최대 발화 시간 (강제 절단):", "fr": "Durée max. de parole (coupe forcée) :", "de": "Max. Sprechdauer (erzw. Schnitt):", "es": "Duración máx. de habla (corte forzado):", "ru": "Макс. длительность речи (принуд. обрезка):", "pt": "Duração máx. da fala (corte forçado):"},
    "filter_words": {"zh": "过滤语气词:", "zh-tw": "過濾語氣詞:", "en": "Filter Filler Words:", "ja": "フィラーワード除外:", "ko": "필러 단어 필터링:", "fr": "Filtrer les mots de remplissage :", "de": "Füllwörter filtern:", "es": "Filtrar muletillas:", "ru": "Фильтр слов-паразитов:", "pt": "Filtrar palavras de preenchimento:"},
    "filter_hint": {
        "zh": "每行一个语气词，识别到这些会忽略不翻译", "zh-tw": "每行一個語氣詞，辨識到這些會忽略不翻譯", "en": "One word per line. These will be ignored.",
        "ja": "1行に1つずつ。認識されても翻訳されません", "ko": "한 줄에 하나씩. 인식되어도 번역되지 않습니다",
        "fr": "Un mot par ligne. Ils seront ignorés.", "de": "Ein Wort pro Zeile. Diese werden ignoriert.",
        "es": "Una palabra por línea. Se ignorarán.", "ru": "По одному слову в строке. Будут игнорироваться.",
        "pt": "Uma palavra por linha. Serão ignoradas.",
    },
    "font_group": {"zh": "字体", "zh-tw": "字型", "en": "Font", "ja": "フォント", "ko": "글꼴", "fr": "Police", "de": "Schriftart", "es": "Fuente", "ru": "Шрифт", "pt": "Fonte"},
    "choose_font": {"zh": "选择字体", "zh-tw": "選擇字型", "en": "Choose Font", "ja": "フォントを選択", "ko": "글꼴 선택", "fr": "Choisir la police", "de": "Schriftart wählen", "es": "Elegir fuente", "ru": "Выбрать шрифт", "pt": "Escolher fonte"},
    "color_group": {"zh": "颜色", "zh-tw": "顏色", "en": "Colors", "ja": "カラー", "ko": "색상", "fr": "Couleurs", "de": "Farben", "es": "Colores", "ru": "Цвета", "pt": "Cores"},
    "shape_group": {"zh": "形状和透明度", "zh-tw": "形狀和透明度", "en": "Shape & Opacity", "ja": "形状と透明度", "ko": "모양 및 투명도", "fr": "Forme et opacité", "de": "Form & Transparenz", "es": "Forma y opacidad", "ru": "Форма и прозрачность", "pt": "Forma e opacidade"},
    "bg_opacity_label": {"zh": "背景透明度:", "zh-tw": "背景透明度:", "en": "Background Opacity:", "ja": "背景透明度:", "ko": "배경 투명도:", "fr": "Opacité du fond :", "de": "Hintergrundtransparenz:", "es": "Opacidad de fondo:", "ru": "Прозрачность фона:", "pt": "Opacidade do fundo:"},
    "corner_radius": {"zh": "圆角半径:", "zh-tw": "圓角半徑:", "en": "Corner Radius:", "ja": "角丸半径:", "ko": "모서리 반경:", "fr": "Rayon des coins :", "de": "Eckenradius:", "es": "Radio de esquinas:", "ru": "Радиус скругления:", "pt": "Raio dos cantos:"},
    "window_width": {"zh": "窗口宽度:", "zh-tw": "視窗寬度:", "en": "Window Width:", "ja": "ウィンドウ幅:", "ko": "창 너비:", "fr": "Largeur de la fenêtre :", "de": "Fensterbreite:", "es": "Ancho de ventana:", "ru": "Ширина окна:", "pt": "Largura da janela:"},
    "display_group": {"zh": "显示", "zh-tw": "顯示", "en": "Display", "ja": "表示", "ko": "표시", "fr": "Affichage", "de": "Anzeige", "es": "Visualización", "ru": "Отображение", "pt": "Exibição"},
    "show_original": {"zh": "显示原文", "zh-tw": "顯示原文", "en": "Show Original", "ja": "原文を表示", "ko": "원문 표시", "fr": "Afficher l'original", "de": "Original anzeigen", "es": "Mostrar original", "ru": "Показать оригинал", "pt": "Mostrar original"},
    "show_translate": {"zh": "显示翻译", "zh-tw": "顯示翻譯", "en": "Show Translation", "ja": "翻訳を表示", "ko": "번역 표시", "fr": "Afficher la traduction", "de": "Übersetzung anzeigen", "es": "Mostrar traducción", "ru": "Показать перевод", "pt": "Mostrar tradução"},
    "text_align": {"zh": "文字对齐:", "zh-tw": "文字對齊:", "en": "Text Alignment:", "ja": "文字配置:", "ko": "텍스트 정렬:", "fr": "Alignement du texte :", "de": "Textausrichtung:", "es": "Alineación del texto:", "ru": "Выравнивание текста:", "pt": "Alinhamento do texto:"},
    "align_center": {"zh": "居中", "zh-tw": "置中", "en": "Center", "ja": "中央", "ko": "가운데", "fr": "Centre", "de": "Zentriert", "es": "Centrado", "ru": "По центру", "pt": "Centralizado"},
    "align_left": {"zh": "左对齐", "zh-tw": "靠左對齊", "en": "Left", "ja": "左揃え", "ko": "왼쪽 정렬", "fr": "Gauche", "de": "Links", "es": "Izquierda", "ru": "Слева", "pt": "Esquerda"},
    "align_right": {"zh": "右对齐", "zh-tw": "靠右對齊", "en": "Right", "ja": "右揃え", "ko": "오른쪽 정렬", "fr": "Droite", "de": "Rechts", "es": "Derecha", "ru": "Справа", "pt": "Direita"},
    "btn_ok": {"zh": "确定", "zh-tw": "確定", "en": "OK", "ja": "OK", "ko": "확인", "fr": "OK", "de": "OK", "es": "Aceptar", "ru": "ОК", "pt": "OK"},
    "btn_cancel": {"zh": "取消", "zh-tw": "取消", "en": "Cancel", "ja": "キャンセル", "ko": "취소", "fr": "Annuler", "de": "Abbrechen", "es": "Cancelar", "ru": "Отмена", "pt": "Cancelar"},
    "manual_input_title": {"zh": "手动输入", "zh-tw": "手動輸入", "en": "Manual Input", "ja": "手動入力", "ko": "수동 입력", "fr": "Saisie manuelle", "de": "Manuelle Eingabe", "es": "Entrada manual", "ru": "Ручной ввод", "pt": "Entrada manual"},
    "manual_input_prompt": {"zh": "输入文字：", "zh-tw": "輸入文字：", "en": "Enter text:", "ja": "文字を入力：", "ko": "텍스트 입력:", "fr": "Entrez le texte :", "de": "Text eingeben:", "es": "Introduce texto:", "ru": "Введите текст:", "pt": "Digite o texto:"},
    "opacity_title": {"zh": "背景透明度", "zh-tw": "背景透明度", "en": "Background Opacity", "ja": "背景透明度", "ko": "배경 투명도", "fr": "Opacité du fond", "de": "Hintergrundtransparenz", "es": "Opacidad de fondo", "ru": "Прозрачность фона", "pt": "Opacidade do fundo"},
    "opacity_prompt": {"zh": "透明度 (0-100):", "zh-tw": "透明度 (0-100):", "en": "Opacity (0-100):", "ja": "透明度 (0-100):", "ko": "투명도 (0-100):", "fr": "Opacité (0-100) :", "de": "Transparenz (0-100):", "es": "Opacidad (0-100):", "ru": "Прозрачность (0-100):", "pt": "Opacidade (0-100):"},
    "locked_tooltip": {
        "zh": "已锁定（鼠标穿透，托盘解锁）", "zh-tw": "已鎖定（滑鼠穿透，托盤解鎖）", "en": "Locked (click-through, unlock via tray)",
        "ja": "ロック中（クリック透過、トレイで解除）", "ko": "잠금됨 (클릭 투과, 트레이에서 해제)",
        "fr": "Verrouillé (clic à travers, déverrouiller via la barre)", "de": "Gesperrt (Klick durchlässig, über Tray entsperren)",
        "es": "Bloqueado (clic a través, desbloquear desde la bandeja)", "ru": "Заблокировано (сквозной клик, разблок. через трей)",
        "pt": "Bloqueado (clique através, desbloquear pela bandeja)",
    },
    "unlocked_tooltip": {
        "zh": "已解锁（可拖动，边缘可调整大小，双击锁定）", "zh-tw": "已解鎖（可拖動，邊緣可調整大小，雙擊鎖定）", "en": "Unlocked (drag to move, edges to resize, double-click to lock)",
        "ja": "ロック解除（ドラッグで移動、縁でサイズ変更、ダブルクリックでロック）", "ko": "잠금 해제 (드래그로 이동, 가장자리로 크기 조절, 더블클릭으로 잠금)",
        "fr": "Déverrouillé (glisser pour déplacer, bords pour redimensionner, double-clic pour verrouiller)", "de": "Entsperrt (ziehen zum Verschieben, Ränder zum Größenändern, Doppelklick zum Sperren)",
        "es": "Desbloqueado (arrastrar para mover, bordes para redimensionar, doble clic para bloquear)", "ru": "Разблокировано (перетаскивание, края для изменения размера, двойной клик для блокировки)",
        "pt": "Desbloqueado (arrastar para mover, bordas para redimensionar, duplo clique para bloquear)",
    },
    "lang_auto": {"zh": "跟随系统", "zh-tw": "跟隨系統", "en": "Auto (System)", "ja": "自動（システム）", "ko": "자동 (시스템)", "fr": "Auto (Système)", "de": "Auto (System)", "es": "Auto (Sistema)", "ru": "Авто (система)", "pt": "Auto (Sistema)"},
    "language": {"zh": "界面语言", "zh-tw": "介面語言", "en": "Interface Language", "ja": "表示言語", "ko": "인터페이스 언어", "fr": "Langue de l'interface", "de": "Oberflächensprache", "es": "Idioma de la interfaz", "ru": "Язык интерфейса", "pt": "Idioma da interface"},
    "translating": {"zh": "翻译中...", "zh-tw": "翻譯中...", "en": "Translating...", "ja": "翻訳中...", "ko": "번역 중...", "fr": "Traduction...", "de": "Übersetze...", "es": "Traduciendo...", "ru": "Перевод...", "pt": "Traduzindo..."},
    "dual_mode_group": {"zh": "双向翻译模式", "zh-tw": "雙向翻譯模式", "en": "Dual Translation Mode", "ja": "デュアル翻訳モード", "ko": "이중 번역 모드", "fr": "Mode double traduction", "de": "Dualer Übersetzungsmodus", "es": "Modo de traducción dual", "ru": "Двойной режим перевода", "pt": "Modo de tradução dupla"},
    "dual_mode_desc": {
        "zh": "启用双向模式（麦克风→OSC，电脑声音→字幕）",
        "zh-tw": "啟用雙向模式（麥克風→OSC，電腦聲音→字幕）",
        "en": "Enable dual mode (Mic→OSC, Computer→Subtitle)",
        "ja": "デュアルモードを有効化（マイク→OSC、PC音声→字幕）",
        "ko": "이중 모드 활성화 (마이크→OSC, 컴퓨터 소리→자막)",
        "fr": "Activer le mode double (Micro→OSC, PC→Sous-titre)",
        "de": "Dualmodus aktivieren (Mikro→OSC, PC→Untertitel)",
        "es": "Activar modo dual (Mic→OSC, PC→Subtítulo)",
        "ru": "Включить двойной режим (Микрофон→OSC, ПК→Субтитры)",
        "pt": "Ativar modo duplo (Mic→OSC, PC→Legenda)",
    },
    "enable_mic_to_osc": {
        "zh": "麦克风 → 翻译 → OSC聊天框",
        "zh-tw": "麥克風 → 翻譯 → OSC聊天框",
        "en": "Microphone → Translate → OSC Chatbox",
        "ja": "マイク → 翻訳 → OSCチャット欄",
        "ko": "마이크 → 번역 → OSC 채팅창",
        "fr": "Micro → Traduction → Boîte de chat OSC",
        "de": "Mikrofon → Übersetzung → OSC-Chatbox",
        "es": "Micrófono → Traducir → Chat OSC",
        "ru": "Микрофон → Перевод → OSC чат",
        "pt": "Microfone → Traduzir → Chat OSC",
    },
    "mic_target_lang": {"zh": "麦克风翻译目标语言:", "zh-tw": "麥克風翻譯目標語言:", "en": "Mic Target Language:", "ja": "マイク翻訳対象言語:", "ko": "마이크 번역 대상 언어:", "fr": "Langue cible micro :", "de": "Mikro-Zielsprache:", "es": "Idioma objetivo del mic:", "ru": "Целевой язык микрофона:", "pt": "Idioma alvo do microfone:"},
    "enable_computer_to_subtitle": {
        "zh": "电脑声音 → 翻译 → 悬浮字幕",
        "zh-tw": "電腦聲音 → 翻譯 → 懸浮字幕",
        "en": "Computer Audio → Translate → Floating Subtitle",
        "ja": "PC音声 → 翻訳 → 浮動字幕",
        "ko": "컴퓨터 소리 → 번역 → 플로팅 자막",
        "fr": "Audio PC → Traduction → Sous-titre flottant",
        "de": "PC-Audio → Übersetzung → Schwebender Untertitel",
        "es": "Audio PC → Traducir → Subtítulo flotante",
        "ru": "Звук ПК → Перевод → Плавающие субтитры",
        "pt": "Áudio PC → Traduzir → Legenda flutuante",
    },
    "computer_target_lang": {"zh": "电脑声音翻译目标语言:", "zh-tw": "電腦聲音翻譯目標語言:", "en": "Computer Target Language:", "ja": "PC音声翻訳対象言語:", "ko": "컴퓨터 소리 번역 대상 언어:", "fr": "Langue cible PC :", "de": "PC-Zielsprache:", "es": "Idioma objetivo del PC:", "ru": "Целевой язык ПК:", "pt": "Idioma alvo do PC:"},
    "dual_mode_hint": {
        "zh": "双向模式下两路同时运行，CPU占用会翻倍。建议性能好的电脑使用。",
        "zh-tw": "雙向模式下兩路同時執行，CPU佔用會翻倍。建議效能好的電腦使用。",
        "en": "Dual mode runs both channels simultaneously, doubling CPU usage. Recommended for powerful PCs.",
        "ja": "デュアルモードでは2系統同時実行のためCPU使用率が倍になります。高性能PC推奨。",
        "ko": "이중 모드는 두 채널을 동시에 실행하여 CPU 사용량이 두 배가 됩니다. 고성능 PC 권장.",
        "fr": "Le mode double exécute les deux canaux simultanément, doublant l'utilisation du CPU. Recommandé pour PC puissants.",
        "de": "Der Dualmodus führt beide Kanäle gleichzeitig aus und verdoppelt die CPU-Auslastung. Für leistungsstarke PCs empfohlen.",
        "es": "El modo dual ejecuta ambos canales simultáneamente, duplicando el uso de CPU. Recomendado para PCs potentes.",
        "ru": "Двойной режим запускает оба канала одновременно, удваивая нагрузку на CPU. Рекомендуется для мощных ПК.",
        "pt": "O modo duplo executa ambos os canais simultaneamente, dobrando o uso da CPU. Recomendado para PCs potentes.",
    },
    "single_mode_only": {"zh": "仅单路模式", "zh-tw": "僅單路模式", "en": "Single mode only", "ja": "シングルモードのみ", "ko": "싱글 모드 전용", "fr": "Mode simple uniquement", "de": "Nur Einzelmodus", "es": "Solo modo individual", "ru": "Только одиночный режим", "pt": "Apenas modo individual"},
    "single_output_group": {"zh": "单路模式输出", "zh-tw": "單路模式輸出", "en": "Single Mode Output", "ja": "シングルモード出力", "ko": "싱글 모드 출력", "fr": "Sortie mode simple", "de": "Einzelmodus-Ausgabe", "es": "Salida modo individual", "ru": "Вывод одиночного режима", "pt": "Saída do modo individual"},
    "single_show_subtitle": {"zh": "显示悬浮字幕", "zh-tw": "顯示懸浮字幕", "en": "Show Floating Subtitle", "ja": "浮動字幕を表示", "ko": "플로팅 자막 표시", "fr": "Afficher le sous-titre flottant", "de": "Schwebenden Untertitel anzeigen", "es": "Mostrar subtítulo flotante", "ru": "Показать плавающие субтитры", "pt": "Mostrar legenda flutuante"},
    "single_send_osc": {"zh": "发送 OSC 到 VRChat 聊天框", "zh-tw": "發送 OSC 到 VRChat 聊天框", "en": "Send OSC to VRChat Chatbox", "ja": "VRChatチャット欄へOSC送信", "ko": "VRChat 채팅창에 OSC 전송", "fr": "Envoyer OSC vers le chat VRChat", "de": "OSC an VRChat-Chatbox senden", "es": "Enviar OSC al chat de VRChat", "ru": "Отправить OSC в чат VRChat", "pt": "Enviar OSC para o chat do VRChat"},
    # ===== 历史记录窗口 =====
    "history_title": {"zh": "翻译历史记录", "zh-tw": "翻譯歷史記錄", "en": "Translation History", "ja": "翻訳履歴", "ko": "번역 기록", "fr": "Historique des traductions", "de": "Übersetzungsverlauf", "es": "Historial de traducciones", "ru": "История переводов", "pt": "Histórico de traduções"},
    "history_clear": {"zh": "清空记录", "zh-tw": "清空記錄", "en": "Clear All", "ja": "履歴をクリア", "ko": "기록 지우기", "fr": "Tout effacer", "de": "Alles löschen", "es": "Borrar todo", "ru": "Очистить всё", "pt": "Limpar tudo"},
    "history_save_toggle": {"zh": "保存到文件", "zh-tw": "儲存到檔案", "en": "Save to file", "ja": "ファイルに保存", "ko": "파일에 저장", "fr": "Enregistrer dans un fichier", "de": "In Datei speichern", "es": "Guardar en archivo", "ru": "Сохранять в файл", "pt": "Salvar em arquivo"},
    "history_retranslate": {"zh": "重新翻译为...", "zh-tw": "重新翻譯為...", "en": "Re-translate to...", "ja": "再翻訳...", "ko": "다시 번역...", "fr": "Retraduire en...", "de": "Neu übersetzen...", "es": "Re-traducir a...", "ru": "Перевести заново...", "pt": "Re-traduzir para..."},
    "history_copy_original": {"zh": "复制原文", "zh-tw": "複製原文", "en": "Copy original", "ja": "原文をコピー", "ko": "원문 복사", "fr": "Copier l'original", "de": "Original kopieren", "es": "Copiar original", "ru": "Копировать оригинал", "pt": "Copiar original"},
    "history_copy_translate": {"zh": "复制翻译", "zh-tw": "複製翻譯", "en": "Copy translation", "ja": "翻訳をコピー", "ko": "번역 복사", "fr": "Copier la traduction", "de": "Übersetzung kopieren", "es": "Copiar traducción", "ru": "Копировать перевод", "pt": "Copiar tradução"},
    "history_resend_osc": {"zh": "重新发送到 OSC", "zh-tw": "重新發送到 OSC", "en": "Re-send to OSC", "ja": "OSCに再送信", "ko": "OSC로 다시 보내기", "fr": "Renvoyer vers OSC", "de": "Erneut an OSC senden", "es": "Re-enviar a OSC", "ru": "Отправить повторно в OSC", "pt": "Re-enviar para OSC"},
    "history_delete": {"zh": "删除这条", "zh-tw": "刪除這條", "en": "Delete this entry", "ja": "この項目を削除", "ko": "이 항목 삭제", "fr": "Supprimer cette entrée", "de": "Diesen Eintrag löschen", "es": "Eliminar esta entrada", "ru": "Удалить запись", "pt": "Excluir esta entrada"},
    "history_empty": {"zh": "暂无记录", "zh-tw": "暫無記錄", "en": "No records yet", "ja": "履歴はありません", "ko": "기록 없음", "fr": "Aucun enregistrement", "de": "Noch keine Einträge", "es": "Sin registros", "ru": "Записей пока нет", "pt": "Sem registros"},
    "history_max_items": {"zh": "最大保留条数:", "zh-tw": "最大保留條數:", "en": "Max items kept:", "ja": "最大保持件数:", "ko": "최대 보관 항목:", "fr": "Max d'éléments conservés :", "de": "Max. gehaltene Einträge:", "es": "Máx. elementos guardados:", "ru": "Макс. записей:", "pt": "Máx. itens guardados:"},
    # ===== AI 代聊窗口 =====
    "aichat_title": {"zh": "AI 代聊", "zh-tw": "AI 代聊", "en": "AI Chat Assistant", "ja": "AIチャットアシスタント", "ko": "AI 채팅 도우미", "fr": "Assistant de chat IA", "de": "KI-Chat-Assistent", "es": "Asistente de chat con IA", "ru": "ИИ-помощник чата", "pt": "Assistente de chat com IA"},
    "aichat_intent": {"zh": "输入你的意图:", "zh-tw": "輸入你的意圖:", "en": "Enter your intent:", "ja": "意図を入力:", "ko": "의도를 입력하세요:", "fr": "Entrez votre intention :", "de": "Geben Sie Ihre Absicht ein:", "es": "Introduce tu intención:", "ru": "Введите ваше намерение:", "pt": "Digite sua intenção:"},
    "aichat_intent_placeholder": {"zh": "例如：跟旁边的日本人打个招呼", "zh-tw": "例如：跟旁邊的日本人打個招呼", "en": "e.g. Say hello to the Japanese person next to me", "ja": "例：隣の日本人に挨拶する", "ko": "예: 옆에 있는 일본인에게 인사하기", "fr": "ex. Dire bonjour au Japonais à côté", "de": "z.B. Begrüße den Japaner neben mir", "es": "ej. Saludar al japonés de al lado", "ru": "напр. Поздороваться с японцем рядом", "pt": "ex. Dizer olá ao japonês ao lado"},
    "aichat_tone": {"zh": "语气:", "zh-tw": "語氣:", "en": "Tone:", "ja": "トーン:", "ko": "말투:", "fr": "Ton :", "de": "Ton:", "es": "Tono:", "ru": "Тон:", "pt": "Tom:"},
    "aichat_tone_friendly": {"zh": "友好", "zh-tw": "友好", "en": "Friendly", "ja": "フレンドリー", "ko": "친절한", "fr": "Amical", "de": "Freundlich", "es": "Amigable", "ru": "Дружелюбный", "pt": "Amigável"},
    "aichat_tone_formal": {"zh": "正式", "zh-tw": "正式", "en": "Formal", "ja": "フォーマル", "ko": "격식 있는", "fr": "Formel", "de": "Formell", "es": "Formal", "ru": "Формальный", "pt": "Formal"},
    "aichat_tone_humorous": {"zh": "幽默", "zh-tw": "幽默", "en": "Humorous", "ja": "ユーモラス", "ko": "유머러스한", "fr": "Humoristique", "de": "Humorvoll", "es": "Humorístico", "ru": "Юмористический", "pt": "Humorístico"},
    "aichat_tone_shy": {"zh": "害羞", "zh-tw": "害羞", "en": "Shy", "ja": "シャイ", "ko": "수줍은", "fr": "Timide", "de": "Schüchtern", "es": "Tímido", "ru": "Стеснительный", "pt": "Tímido"},
    "aichat_tone_cool": {"zh": "高冷", "zh-tw": "高冷", "en": "Cool", "ja": "クール", "ko": "차가운", "fr": "Cool", "de": "Cool", "es": "Genial", "ru": "Холодный", "pt": "Legal"},
    "aichat_target_lang": {"zh": "目标语言:", "zh-tw": "目標語言:", "en": "Target language:", "ja": "対象言語:", "ko": "대상 언어:", "fr": "Langue cible :", "de": "Zielsprache:", "es": "Idioma objetivo:", "ru": "Целевой язык:", "pt": "Idioma alvo:"},
    "aichat_generate": {"zh": "生成", "zh-tw": "生成", "en": "Generate", "ja": "生成", "ko": "생성", "fr": "Générer", "de": "Generieren", "es": "Generar", "ru": "Сгенерировать", "pt": "Gerar"},
    "aichat_send": {"zh": "发送到 OSC", "zh-tw": "發送到 OSC", "en": "Send to OSC", "ja": "OSCに送信", "ko": "OSC로 보내기", "fr": "Envoyer vers OSC", "de": "An OSC senden", "es": "Enviar a OSC", "ru": "Отправить в OSC", "pt": "Enviar para OSC"},
    "aichat_result": {"zh": "生成结果（可编辑）:", "zh-tw": "生成結果（可編輯）:", "en": "Result (editable):", "ja": "生成結果（編集可）:", "ko": "생성 결과 (편집 가능):", "fr": "Résultat (modifiable) :", "de": "Ergebnis (bearbeitbar):", "es": "Resultado (editable):", "ru": "Результат (редактируемый):", "pt": "Resultado (editável):"},
    "aichat_generating": {"zh": "生成中...", "zh-tw": "生成中...", "en": "Generating...", "ja": "生成中...", "ko": "생성 중...", "fr": "Génération...", "de": "Generiere...", "es": "Generando...", "ru": "Генерация...", "pt": "Gerando..."},
    "aichat_preset_greeting": {"zh": "打招呼", "zh-tw": "打招呼", "en": "Greeting", "ja": "挨拶", "ko": "인사", "fr": "Salutation", "de": "Begrüßung", "es": "Saludo", "ru": "Приветствие", "pt": "Saudação"},
    "aichat_preset_thanks": {"zh": "感谢", "zh-tw": "感謝", "en": "Thanks", "ja": "感謝", "ko": "감사", "fr": "Remerciement", "de": "Dank", "es": "Agradecimiento", "ru": "Благодарность", "pt": "Agradecimento"},
    "aichat_preset_apology": {"zh": "道歉", "zh-tw": "道歉", "en": "Apology", "ja": "謝罪", "ko": "사과", "fr": "Excuse", "de": "Entschuldigung", "es": "Disculpa", "ru": "Извинение", "pt": "Desculpa"},
    "aichat_preset_goodbye": {"zh": "告别", "zh-tw": "告別", "en": "Goodbye", "ja": "別れ", "ko": "작별", "fr": "Au revoir", "de": "Abschied", "es": "Despedida", "ru": "Прощание", "pt": "Adeus"},
    "aichat_preset_compliment": {"zh": "夸赞", "zh-tw": "誇讚", "en": "Compliment", "ja": "褒め言葉", "ko": "칭찬", "fr": "Compliment", "de": "Kompliment", "es": "Cumplido", "ru": "Комплимент", "pt": "Elogio"},
    "aichat_preset_friend": {"zh": "加好友", "zh-tw": "加好友", "en": "Add friend", "ja": "フレンド申請", "ko": "친구 추가", "fr": "Ajouter en ami", "de": "Freund hinzufügen", "es": "Añadir amigo", "ru": "Добавить в друзья", "pt": "Adicionar amigo"},
    "aichat_preset_play": {"zh": "邀请一起玩", "zh-tw": "邀請一起玩", "en": "Invite to play", "ja": "一緒に遊ぶ誘い", "ko": "같이 놀자고 초대", "fr": "Inviter à jouer", "de": "Zum Spielen einladen", "es": "Invitar a jugar", "ru": "Пригласить поиграть", "pt": "Convidar para jogar"},
    "aichat_no_api": {"zh": "请先在设置中配置 API Key", "zh-tw": "請先在設定中配置 API Key", "en": "Please configure API Key in settings first", "ja": "設定でAPIキーを設定してください", "ko": "설정에서 API 키를 먼저 설정하세요", "fr": "Veuillez d'abord configurer la clé API dans les paramètres", "de": "Bitte zuerst API-Schlüssel in den Einstellungen konfigurieren", "es": "Primero configura la clave API en los ajustes", "ru": "Сначала настройте API-ключ в настройках", "pt": "Primeiro configure a chave API nas configurações"},
    # ===== 帮助/说明书 =====
    "help_menu": {"zh": "帮助/说明书...", "zh-tw": "說明書...", "en": "Help / Manual...", "ja": "ヘルプ/マニュアル...", "ko": "도움말/매뉴얼...", "fr": "Aide / Manuel...", "de": "Hilfe / Handbuch...", "es": "Ayuda / Manual...", "ru": "Помощь / Руководство...", "pt": "Ajuda / Manual..."},
    "help_title": {"zh": "使用说明书", "zh-tw": "使用說明書", "en": "User Manual", "ja": "使用マニュアル", "ko": "사용 설명서", "fr": "Manuel d'utilisation", "de": "Benutzerhandbuch", "es": "Manual de usuario", "ru": "Руководство пользователя", "pt": "Manual do usuário"},
    "help_tab_quickstart": {"zh": "快速开始", "zh-tw": "快速開始", "en": "Quick Start", "ja": "クイックスタート", "ko": "빠른 시작", "fr": "Démarrage rapide", "de": "Schnellstart", "es": "Inicio rápido", "ru": "Быстрый старт", "pt": "Início rápido"},
    "help_tab_settings": {"zh": "设置详解", "zh-tw": "設定詳解", "en": "Settings Guide", "ja": "設定ガイド", "ko": "설정 가이드", "fr": "Guide des paramètres", "de": "Einstellungsleitfaden", "es": "Guía de ajustes", "ru": "Руководство по настройкам", "pt": "Guia de configurações"},
    "help_tab_shortcuts": {"zh": "快捷键", "zh-tw": "快捷鍵", "en": "Shortcuts", "ja": "ショートカット", "ko": "단축키", "fr": "Raccourcis", "de": "Tastenkürzel", "es": "Atajos", "ru": "Горячие клавиши", "pt": "Atalhos"},
    "help_tab_faq": {"zh": "常见问题", "zh-tw": "常見問題", "en": "FAQ", "ja": "よくある質問", "ko": "자주 묻는 질문", "fr": "FAQ", "de": "Häufige Fragen", "es": "Preguntas frecuentes", "ru": "Частые вопросы", "pt": "Perguntas frequentes"},
    # ===== 配置管理 =====
    "config_menu": {"zh": "配置管理...", "zh-tw": "配置管理...", "en": "Config Manager...", "ja": "設定管理...", "ko": "설정 관리...", "fr": "Gestion des configs...", "de": "Konfigurationsverwaltung...", "es": "Gestión de config...", "ru": "Управление конфигом...", "pt": "Gerir config..."},
    "config_export": {"zh": "导出配置", "zh-tw": "匯出配置", "en": "Export Config", "ja": "設定をエクスポート", "ko": "설정 내보내기", "fr": "Exporter la config", "de": "Konfig exportieren", "es": "Exportar config", "ru": "Экспорт конфига", "pt": "Exportar config"},
    "config_import": {"zh": "导入配置", "zh-tw": "匯入配置", "en": "Import Config", "ja": "設定をインポート", "ko": "설정 가져오기", "fr": "Importer la config", "de": "Konfig importieren", "es": "Importar config", "ru": "Импорт конфига", "pt": "Importar config"},
    "config_reset": {"zh": "恢复默认设置", "zh-tw": "恢復預設設定", "en": "Reset to Default", "ja": "デフォルトに戻す", "ko": "기본값으로 재설정", "fr": "Réinitialiser", "de": "Auf Standard zurücksetzen", "es": "Restablecer", "ru": "Сбросить по умолчанию", "pt": "Restaurar padrão"},
    "config_export_done": {"zh": "配置已导出到：", "zh-tw": "配置已匯出到：", "en": "Config exported to:", "ja": "設定をエクスポートしました：", "ko": "설정이 내보내졌습니다:", "fr": "Config exportée vers :", "de": "Konfig exportiert nach:", "es": "Config exportada a:", "ru": "Конфиг экспортирован в:", "pt": "Config exportada para:"},
    "config_import_done": {"zh": "配置已导入，程序将重启", "zh-tw": "配置已匯入，程式將重啟", "en": "Config imported, app will restart", "ja": "設定をインポートしました、再起動します", "ko": "설정이 가져와졌습니다, 앱이 재시작됩니다", "fr": "Config importée, redémarrage", "de": "Konfig importiert, App startet neu", "es": "Config importada, la app se reiniciará", "ru": "Конфиг импортирован, приложение перезапустится", "pt": "Config importada, o app irá reiniciar"},
    "config_reset_confirm": {"zh": "确定要恢复所有设置为默认值吗？", "zh-tw": "確定要恢復所有設定為預設值嗎？", "en": "Reset all settings to default?", "ja": "すべての設定をデフォルトに戻しますか？", "ko": "모든 설정을 기본값으로 재설정하시겠습니까?", "fr": "Réinitialiser tous les paramètres ?", "de": "Alle Einstellungen auf Standard zurücksetzen?", "es": "¿Restablecer todos los ajustes?", "ru": "Сбросить все настройки по умолчанию?", "pt": "Restaurar todas as configurações?"},
    # ===== AI 代聊免费模型 =====
    "aichat_api_mode": {"zh": "API 模式:", "zh-tw": "API 模式:", "en": "API Mode:", "ja": "APIモード:", "ko": "API 모드:", "fr": "Mode API :", "de": "API-Modus:", "es": "Modo API:", "ru": "Режим API:", "pt": "Modo API:"},
    "aichat_mode_deepseek": {"zh": "DeepSeek（付费，质量好）", "zh-tw": "DeepSeek（付費，質量好）", "en": "DeepSeek (paid, best quality)", "ja": "DeepSeek（有料、高品質）", "ko": "DeepSeek (유료, 최고 품질)", "fr": "DeepSeek (payant, meilleure qualité)", "de": "DeepSeek (kostenpflichtig, beste Qualität)", "es": "DeepSeek (pago, mejor calidad)", "ru": "DeepSeek (платно, лучшее качество)", "pt": "DeepSeek (pago, melhor qualidade)"},
    "aichat_mode_free": {"zh": "免费/自定义 API", "zh-tw": "免費/自訂 API", "en": "Free / Custom API", "ja": "無料/カスタムAPI", "ko": "무료/사용자 정의 API", "fr": "API gratuite / personnalisée", "de": "Kostenlose / benutzerdefinierte API", "es": "API gratuita / personalizada", "ru": "Бесплатный / свой API", "pt": "API grátis / personalizada"},
    "aichat_free_base": {"zh": "API 地址:", "zh-tw": "API 位址:", "en": "API URL:", "ja": "API URL:", "ko": "API 주소:", "fr": "URL API :", "de": "API-URL:", "es": "URL de API:", "ru": "URL API:", "pt": "URL da API:"},
    "aichat_free_model": {"zh": "模型名:", "zh-tw": "模型名:", "en": "Model name:", "ja": "モデル名:", "ko": "모델 이름:", "fr": "Nom du modèle :", "de": "Modellname:", "es": "Nombre del modelo:", "ru": "Имя модели:", "pt": "Nome do modelo:"},
    "aichat_free_key": {"zh": "API Key:", "zh-tw": "API Key:", "en": "API Key:", "ja": "APIキー:", "ko": "API 키:", "fr": "Clé API :", "de": "API-Schlüssel:", "es": "Clave API:", "ru": "API-ключ:", "pt": "Chave de API:"},
    "aichat_free_hint": {"zh": "提示：可使用 SiliconFlow 等兼容 OpenAI 格式的免费服务", "zh-tw": "提示：可使用 SiliconFlow 等相容 OpenAI 格式的免費服務", "en": "Tip: Use free OpenAI-compatible services like SiliconFlow", "ja": "ヒント：SiliconFlowなどのOpenAI互換無料サービスが利用可能", "ko": "팁: SiliconFlow 등 OpenAI 호환 무료 서비스 사용 가능", "fr": "Astuce : services gratuits compatibles OpenAI comme SiliconFlow", "de": "Tipp: Kostenlose OpenAI-kompatible Dienste wie SiliconFlow", "es": "Consejo: servicios gratuitos compatibles con OpenAI como SiliconFlow", "ru": "Подсказка: бесплатные OpenAI-совместимые сервисы, например SiliconFlow", "pt": "Dica: serviços gratuitos compatíveis com OpenAI como SiliconFlow"},
    "aichat_api_group": {"zh": "AI 提供商", "zh-tw": "AI 提供商", "en": "AI Provider", "ja": "AIプロバイダー", "ko": "AI 제공자", "fr": "Fournisseur IA", "de": "KI-Anbieter", "es": "Proveedor de IA", "ru": "AI-провайдер", "pt": "Provedor de IA"},
    "aichat_mode_inherit": {"zh": "继承全局设置", "zh-tw": "繼承全域設定", "en": "Inherit Global", "ja": "グローバル設定を継承", "ko": "전역 설정 상속", "fr": "Hériter des paramètres globaux", "de": "Globale Einstellungen übernehmen", "es": "Heredar configuración global", "ru": "Наследовать глобальные настройки", "pt": "Herdar configuração global"},
    "aichat_mode_openai": {"zh": "OpenAI (ChatGPT)", "zh-tw": "OpenAI (ChatGPT)", "en": "OpenAI (ChatGPT)", "ja": "OpenAI (ChatGPT)", "ko": "OpenAI (ChatGPT)", "fr": "OpenAI (ChatGPT)", "de": "OpenAI (ChatGPT)", "es": "OpenAI (ChatGPT)", "ru": "OpenAI (ChatGPT)", "pt": "OpenAI (ChatGPT)"},
    "aichat_mode_azure": {"zh": "Azure OpenAI (微软)", "zh-tw": "Azure OpenAI (微軟)", "en": "Azure OpenAI (Microsoft)", "ja": "Azure OpenAI (Microsoft)", "ko": "Azure OpenAI (Microsoft)", "fr": "Azure OpenAI (Microsoft)", "de": "Azure OpenAI (Microsoft)", "es": "Azure OpenAI (Microsoft)", "ru": "Azure OpenAI (Microsoft)", "pt": "Azure OpenAI (Microsoft)"},
    "aichat_mode_custom": {"zh": "自定义 (OpenAI 兼容)", "zh-tw": "自訂 (OpenAI 相容)", "en": "Custom (OpenAI compatible)", "ja": "カスタム (OpenAI互換)", "ko": "사용자 정의 (OpenAI 호환)", "fr": "Personnalisé (compatible OpenAI)", "de": "Benutzerdefiniert (OpenAI-kompatibel)", "es": "Personalizado (compatible con OpenAI)", "ru": "Свой (совместимый с OpenAI)", "pt": "Personalizado (compatível com OpenAI)"},
    "aichat_api_key": {"zh": "API Key:", "zh-tw": "API Key:", "en": "API Key:", "ja": "APIキー:", "ko": "API 키:", "fr": "Clé API :", "de": "API-Schlüssel:", "es": "Clave API:", "ru": "API-ключ:", "pt": "Chave de API:"},
    "aichat_api_base": {"zh": "API 地址:", "zh-tw": "API 位址:", "en": "API URL:", "ja": "API URL:", "ko": "API 주소:", "fr": "URL API :", "de": "API-URL:", "es": "URL de API:", "ru": "URL API:", "pt": "URL da API:"},
    "aichat_api_model": {"zh": "模型:", "zh-tw": "模型:", "en": "Model:", "ja": "モデル:", "ko": "모델:", "fr": "Modèle :", "de": "Modell:", "es": "Modelo:", "ru": "Модель:", "pt": "Modelo:"},
    "aichat_azure_endpoint": {"zh": "Azure 端点:", "zh-tw": "Azure 端點:", "en": "Azure Endpoint:", "ja": "Azure エンドポイント:", "ko": "Azure 엔드포인트:", "fr": "Point de terminaison Azure :", "de": "Azure-Endpunkt:", "es": "Punto de conexión Azure:", "ru": "Конечная точка Azure:", "pt": "Endpoint do Azure:"},
    "aichat_azure_deployment": {"zh": "部署名:", "zh-tw": "部署名:", "en": "Deployment:", "ja": "デプロイ名:", "ko": "배포 이름:", "fr": "Déploiement :", "de": "Bereitstellung:", "es": "Implementación:", "ru": "Развертывание:", "pt": "Implantação:"},
    "aichat_inherit_hint": {"zh": "当前使用全局 AI 配置：{provider}。如需独立配置，请在上方选择具体提供商。", "zh-tw": "當前使用全域 AI 設定：{provider}。如需獨立設定，請在上方選擇具體提供商。", "en": "Using global AI config: {provider}. To use separate config, select a provider above.", "ja": "グローバルAI設定を使用中：{provider}。個別設定する場合は上からプロバイダーを選択してください。", "ko": "전역 AI 설정 사용 중: {provider}. 별도 설정하려면 위에서 제공자를 선택하세요.", "fr": "Configuration IA globale utilisée : {provider}. Pour une config séparée, sélectionnez un fournisseur ci-dessus.", "de": "Globale KI-Konfiguration verwendet: {provider}. Für separate Einstellungen oben einen Anbieter wählen.", "es": "Usando configuración global de IA: {provider}. Para config separada, selecciona un proveedor arriba.", "ru": "Используется глобальная конфигурация ИИ: {provider}. Для отдельной настройки выберите провайдера выше.", "pt": "Usando configuração global de IA: {provider}. Para config separada, selecione um provedor acima."},
    "aichat_azure_hint": {"zh": "Azure OpenAI 需要在 Azure 门户创建部署后获取 Endpoint 和 Key", "zh-tw": "Azure OpenAI 需要在 Azure 入口網站建立部署後取得 Endpoint 和 Key", "en": "Azure OpenAI requires creating a deployment in Azure portal to get Endpoint and Key", "ja": "Azure OpenAIはAzureポータルでデプロイを作成し、EndpointとKeyを取得する必要があります", "ko": "Azure OpenAI는 Azure 포털에서 배포를 생성한 후 Endpoint와 Key를 얻어야 합니다", "fr": "Azure OpenAI nécessite de créer un déploiement dans le portail Azure pour obtenir l'Endpoint et la clé", "de": "Azure OpenAI erfordert die Erstellung einer Bereitstellung im Azure-Portal, um Endpunkt und Schlüssel zu erhalten", "es": "Azure OpenAI requiere crear una implementación en el portal de Azure para obtener Endpoint y Key", "ru": "Azure OpenAI требует создания развертывания на портале Azure для получения Endpoint и Key", "pt": "Azure OpenAI requer criar uma implantação no portal do Azure para obter Endpoint e Key"},

    # ===== 翻译引擎 =====
    "engine_ai": {"zh": "AI 翻译 (DeepSeek/OpenAI/Azure)", "zh-tw": "AI 翻譯 (DeepSeek/OpenAI/Azure)", "en": "AI Translate (DeepSeek/OpenAI/Azure)", "ja": "AI翻訳 (DeepSeek/OpenAI/Azure)", "ko": "AI 번역 (DeepSeek/OpenAI/Azure)", "fr": "Traduction IA (DeepSeek/OpenAI/Azure)", "de": "KI-Übersetzung (DeepSeek/OpenAI/Azure)", "es": "Traducción IA (DeepSeek/OpenAI/Azure)", "ru": "ИИ-перевод (DeepSeek/OpenAI/Azure)", "pt": "Tradução IA (DeepSeek/OpenAI/Azure)"},
    "engine_google": {"zh": "Google 翻译 (免费)", "zh-tw": "Google 翻譯 (免費)", "en": "Google Translate (Free)", "ja": "Google翻訳 (無料)", "ko": "Google 번역 (무료)", "fr": "Google Traduction (gratuit)", "de": "Google Übersetzer (kostenlos)", "es": "Google Traductor (gratis)", "ru": "Google Переводчик (бесплатно)", "pt": "Google Tradutor (grátis)"},
    "engine_baidu": {"zh": "百度翻译", "zh-tw": "百度翻譯", "en": "Baidu Translate", "ja": "Baidu翻訳", "ko": "Baidu 번역", "fr": "Baidu Traduction", "de": "Baidu Übersetzer", "es": "Baidu Traductor", "ru": "Baidu Переводчик", "pt": "Baidu Tradutor"},
    "ai_provider": {"zh": "AI 提供商", "zh-tw": "AI 提供商", "en": "AI Provider", "ja": "AIプロバイダー", "ko": "AI 제공자", "fr": "Fournisseur IA", "de": "KI-Anbieter", "es": "Proveedor de IA", "ru": "AI-провайдер", "pt": "Provedor de IA"},
    "azure_endpoint": {"zh": "Azure 端点:", "zh-tw": "Azure 端點:", "en": "Azure Endpoint:", "ja": "Azure エンドポイント:", "ko": "Azure 엔드포인트:", "fr": "Point de terminaison Azure :", "de": "Azure-Endpunkt:", "es": "Punto de conexión Azure:", "ru": "Конечная точка Azure:", "pt": "Endpoint do Azure:"},
    "azure_deployment": {"zh": "部署名:", "zh-tw": "部署名:", "en": "Deployment:", "ja": "デプロイ名:", "ko": "배포 이름:", "fr": "Déploiement :", "de": "Bereitstellung:", "es": "Implementación:", "ru": "Развертывание:", "pt": "Implantação:"},
    "translate_engine": {"zh": "翻译引擎", "zh-tw": "翻譯引擎", "en": "Translate Engine", "ja": "翻訳エンジン", "ko": "번역 엔진", "fr": "Moteur de traduction", "de": "Übersetzungs-Engine", "es": "Motor de traducción", "ru": "Движок перевода", "pt": "Motor de tradução"},
    "baidu_appid": {"zh": "百度 APP ID", "zh-tw": "百度 APP ID", "en": "Baidu App ID", "ja": "Baidu App ID", "ko": "Baidu App ID", "fr": "Baidu App ID", "de": "Baidu App ID", "es": "Baidu App ID", "ru": "Baidu App ID", "pt": "Baidu App ID"},
    "baidu_secret": {"zh": "百度密钥", "zh-tw": "百度密鑰", "en": "Baidu Secret Key", "ja": "Baidu シークレットキー", "ko": "Baidu 비밀키", "fr": "Clé secrète Baidu", "de": "Baidu Secret Key", "es": "Clave secreta Baidu", "ru": "Секретный ключ Baidu", "pt": "Chave secreta Baidu"},
    "baidu_hint": {"zh": "百度翻译需申请 API，每月免费 5 万字符。申请：fanyi-api.baidu.com", "zh-tw": "百度翻譯需申請 API，每月免費 5 萬字符。申請：fanyi-api.baidu.com", "en": "Baidu Translate requires API, 50k chars/month free. Apply: fanyi-api.baidu.com", "ja": "Baidu翻訳はAPI申請が必要、月5万文字まで無料。申請: fanyi-api.baidu.com", "ko": "Baidu 번역 API 필요, 월 5만자 무료. 신청: fanyi-api.baidu.com", "fr": "Baidu Traduction nécessite une API, 50k car/mois gratuit. Demande : fanyi-api.baidu.com", "de": "Baidu Übersetzung erfordert API, 50k Zeichen/Monat kostenlos. Beantragung: fanyi-api.baidu.com", "es": "Baidu Traductor requiere API, 50k caracteres/mes gratis. Solicitar: fanyi-api.baidu.com", "ru": "Baidu Переводчик требует API, 50к символов/мес бесплатно. Запрос: fanyi-api.baidu.com", "pt": "Baidu Tradutor requer API, 50k caracteres/mês grátis. Solicitar: fanyi-api.baidu.com"},
    # ===== 音频设备 =====
    "refresh_devices": {"zh": "刷新", "zh-tw": "重新整理", "en": "Refresh", "ja": "更新", "ko": "새로고침", "fr": "Actualiser", "de": "Aktualisieren", "es": "Actualizar", "ru": "Обновить", "pt": "Atualizar"},
    # ===== 文字效果 =====
    "text_effect_group": {"zh": "文字效果", "zh-tw": "文字效果", "en": "Text Effects", "ja": "文字効果", "ko": "텍스트 효과", "fr": "Effets de texte", "de": "Texteffekte", "es": "Efectos de texto", "ru": "Эффекты текста", "pt": "Efeitos de texto"},
    "text_stroke_enable": {"zh": "文字描边", "zh-tw": "文字描邊", "en": "Text Stroke", "ja": "文字の縁取り", "ko": "텍스트 외곽선", "fr": "Contour du texte", "de": "Textumrandung", "es": "Contorno de texto", "ru": "Обводка текста", "pt": "Contorno do texto"},
    "text_stroke_color": {"zh": "描边颜色", "zh-tw": "描邊顏色", "en": "Stroke Color", "ja": "縁取り色", "ko": "외곽선 색상", "fr": "Couleur du contour", "de": "Umrandungsfarbe", "es": "Color de contorno", "ru": "Цвет обводки", "pt": "Cor do contorno"},
    "text_stroke_width": {"zh": "描边宽度", "zh-tw": "描邊寬度", "en": "Stroke Width", "ja": "縁取り幅", "ko": "외곽선 두께", "fr": "Largeur du contour", "de": "Umrandungsbreite", "es": "Ancho de contorno", "ru": "Ширина обводки", "pt": "Largura do contorno"},
    "text_shadow_enable": {"zh": "文字阴影", "zh-tw": "文字陰影", "en": "Text Shadow", "ja": "文字の影", "ko": "텍스트 그림자", "fr": "Ombre du texte", "de": "Textschatten", "es": "Sombra de texto", "ru": "Тень текста", "pt": "Sombra do texto"},
    # ===== 其他 Tab =====
    "tab_other": {"zh": "其他", "zh-tw": "其他", "en": "Other", "ja": "その他", "ko": "기타", "fr": "Autre", "de": "Andere", "es": "Otro", "ru": "Другое", "pt": "Outro"},
    # ===== TTS =====
    "tts_group": {"zh": "语音朗读 (TTS)", "zh-tw": "語音朗讀 (TTS)", "en": "Text-to-Speech", "ja": "音声読み上げ (TTS)", "ko": "음성 읽기 (TTS)", "fr": "Synthèse vocale", "de": "Sprachausgabe (TTS)", "es": "Síntesis de voz", "ru": "Синтез речи", "pt": "Síntese de voz"},
    "tts_enable": {"zh": "启用语音朗读", "zh-tw": "啟用語音朗讀", "en": "Enable TTS", "ja": "音声読み上げを有効化", "ko": "TTS 활성화", "fr": "Activer la synthèse vocale", "de": "TTS aktivieren", "es": "Activar TTS", "ru": "Включить TTS", "pt": "Ativar TTS"},
    "tts_disable": {"zh": "禁用语音朗读", "zh-tw": "停用語音朗讀", "en": "Disable TTS", "ja": "音声読み上げを無効化", "ko": "TTS 비활성화", "fr": "Désactiver la synthèse vocale", "de": "TTS deaktivieren", "es": "Desactivar TTS", "ru": "Выключить TTS", "pt": "Desativar TTS"},
    "tts_read_original": {"zh": "朗读原文（否则朗读翻译）", "zh-tw": "朗讀原文（否則朗讀翻譯）", "en": "Read original (else read translation)", "ja": "原文を読む（否则は翻訳を読む）", "ko": "원문 읽기 (아니면 번역 읽기)", "fr": "Lire l'original (sinon la traduction)", "de": "Original vorlesen (sonst Übersetzung)", "es": "Leer original (si no, traducción)", "ru": "Читать оригинал (иначе перевод)", "pt": "Ler original (senão tradução)"},
    "tts_rate": {"zh": "语速", "zh-tw": "語速", "en": "Speech Rate", "ja": "話速", "ko": "말하기 속도", "fr": "Débit de parole", "de": "Sprechgeschwindigkeit", "es": "Velocidad de habla", "ru": "Скорость речи", "pt": "Velocidade da fala"},
    "tts_volume": {"zh": "音量", "zh-tw": "音量", "en": "Volume", "ja": "音量", "ko": "볼륨", "fr": "Volume", "de": "Lautstärke", "es": "Volumen", "ru": "Громкость", "pt": "Volume"},
    "tts_test": {"zh": "测试朗读", "zh-tw": "測試朗讀", "en": "Test Speech", "ja": "テスト音声", "ko": "테스트 음성", "fr": "Tester la voix", "de": "Sprachtest", "es": "Probar voz", "ru": "Тест речи", "pt": "Testar voz"},
    "tts_hint": {"zh": "需安装 pyttsx3：pip install pyttsx3，使用系统自带语音引擎", "zh-tw": "需安裝 pyttsx3：pip install pyttsx3，使用系統自帶語音引擎", "en": "Requires pyttsx3: pip install pyttsx3, uses system voice engine", "ja": "pyttsx3 が必要: pip install pyttsx3、システム音声エンジンを使用", "ko": "pyttsx3 필요: pip install pyttsx3, 시스템 음성 엔진 사용", "fr": "Nécessite pyttsx3 : pip install pyttsx3, utilise le moteur vocal système", "de": "Erfordert pyttsx3: pip install pyttsx3, nutzt System-Sprachengine", "es": "Requiere pyttsx3: pip install pyttsx3, usa motor de voz del sistema", "ru": "Требуется pyttsx3: pip install pyttsx3, использует системный движок", "pt": "Requer pyttsx3: pip install pyttsx3, usa mecanismo de voz do sistema"},
    "tts_enabled_msg": {"zh": "语音朗读已启用", "zh-tw": "語音朗讀已啟用", "en": "TTS enabled", "ja": "音声読み上げが有効になりました", "ko": "TTS가 활성화되었습니다", "fr": "Synthèse vocale activée", "de": "TTS aktiviert", "es": "TTS activado", "ru": "TTS включен", "pt": "TTS ativado"},
    # ===== 更新检查 =====
    "update_group": {"zh": "自动更新", "zh-tw": "自動更新", "en": "Auto Update", "ja": "自動更新", "ko": "자동 업데이트", "fr": "Mise à jour auto", "de": "Automatische Updates", "es": "Actualización automática", "ru": "Автообновление", "pt": "Atualização automática"},
    "check_update": {"zh": "检查更新", "zh-tw": "檢查更新", "en": "Check for Updates", "ja": "更新を確認", "ko": "업데이트 확인", "fr": "Vérifier les mises à jour", "de": "Nach Updates suchen", "es": "Buscar actualizaciones", "ru": "Проверить обновления", "pt": "Verificar atualizações"},
    "check_update_on_start": {"zh": "启动时自动检查更新", "zh-tw": "啟動時自動檢查更新", "en": "Check updates on startup", "ja": "起動時に更新を自動確認", "ko": "시작 시 자동 업데이트 확인", "fr": "Vérifier les MAJ au démarrage", "de": "Updates beim Start prüfen", "es": "Buscar actualizaciones al iniciar", "ru": "Проверять обновления при запуске", "pt": "Verificar atualizações ao iniciar"},
    "checking_update": {"zh": "正在检查更新...", "zh-tw": "正在檢查更新...", "en": "Checking for updates...", "ja": "更新を確認中...", "ko": "업데이트 확인 중...", "fr": "Vérification des mises à jour...", "de": "Suche nach Updates...", "es": "Buscando actualizaciones...", "ru": "Проверка обновлений...", "pt": "Verificando atualizações..."},
    "update_available": {"zh": "发现新版本", "zh-tw": "發現新版本", "en": "Update Available", "ja": "新しいバージョンがあります", "ko": "새 버전 발견", "fr": "Mise à jour disponible", "de": "Update verfügbar", "es": "Actualización disponible", "ru": "Доступно обновление", "pt": "Atualização disponível"},
    "update_latest": {"zh": "当前已是最新版本", "zh-tw": "目前已是最新版本", "en": "You are up to date", "ja": "最新バージョンです", "ko": "최신 버전입니다", "fr": "Vous êtes à jour", "de": "Sie sind auf dem neuesten Stand", "es": "Estás al día", "ru": "У вас последняя версия", "pt": "Você está atualizado"},
    "update_tip": {"zh": "点击托盘菜单→检查更新查看详情", "zh-tw": "點擊托盤選單→檢查更新查看詳情", "en": "Click tray menu → Check Updates for details", "ja": "トレイメニュー→更新を確認で詳細を表示", "ko": "트레이 메뉴→업데이트 확인에서 자세히 보기", "fr": "Cliquez sur menu plateau → Vérifier les MAJ pour les détails", "de": "Klicken Sie auf Tray-Menü → Nach Updates suchen für Details", "es": "Haz clic en menú de bandeja → Buscar actualizaciones para detalles", "ru": "Нажмите меню трея → Проверить обновления для подробностей", "pt": "Clique no menu da bandeja → Verificar atualizações para detalhes"},
    "current_version": {"zh": "当前版本", "zh-tw": "目前版本", "en": "Current Version", "ja": "現在のバージョン", "ko": "현재 버전", "fr": "Version actuelle", "de": "Aktuelle Version", "es": "Versión actual", "ru": "Текущая версия", "pt": "Versão atual"},
    # ===== 设置面板补充 =====
    "tts_enabled": {"zh": "启用语音朗读", "zh-tw": "啟用語音朗讀", "en": "Enable TTS", "ja": "音声読み上げを有効化", "ko": "TTS 활성화", "fr": "Activer la synthèse vocale", "de": "TTS aktivieren", "es": "Activar TTS", "ru": "Включить TTS", "pt": "Ativar TTS"},
    "other_font_group": {"zh": "其他窗口字体", "zh-tw": "其他視窗字型", "en": "Other Window Fonts", "ja": "他のウィンドウフォント", "ko": "다른 창 글꼴", "fr": "Polices des autres fenêtres", "de": "Schriftarten anderer Fenster", "es": "Fuentes de otras ventanas", "ru": "Шрифты других окон", "pt": "Fontes de outras janelas"},
    "history_font_size": {"zh": "历史记录字体:", "zh-tw": "歷史記錄字型:", "en": "History font:", "ja": "履歴フォント:", "ko": "기록 글꼴:", "fr": "Police de l'historique :", "de": "Verlaufsschrift:", "es": "Fuente del historial:", "ru": "Шрифт истории:", "pt": "Fonte do histórico:"},
    "ui_font_size": {"zh": "界面字体大小:", "zh-tw": "介面字型大小:", "en": "UI font size:", "ja": "UIフォントサイズ:", "ko": "UI 글꼴 크기:", "fr": "Taille de la police UI :", "de": "UI-Schriftgröße:", "es": "Tamaño de fuente UI:", "ru": "Размер шрифта интерфейса:", "pt": "Tamanho da fonte da UI:"},
    "system_default": {"zh": "系统默认", "zh-tw": "系統預設", "en": "System Default", "ja": "システム標準", "ko": "시스템 기본값", "fr": "Par défaut du système", "de": "Systemstandard", "es": "Predeterminado del sistema", "ru": "По умолчанию", "pt": "Padrão do sistema"},
    "ui_font_hint": {"zh": "提示：界面字体修改后需重启程序生效", "zh-tw": "提示：介面字型修改後需重啟程式生效", "en": "Tip: UI font changes require restart to take effect", "ja": "ヒント：UIフォントの変更は再起動後に有効になります", "ko": "팁: UI 글꼴 변경은 재시작 후 적용됩니다", "fr": "Astuce : les modifications de police UI nécessitent un redémarrage", "de": "Tipp: UI-Schriftänderungen erfordern einen Neustart", "es": "Consejo: los cambios de fuente UI requieren reinicio", "ru": "Подсказка: изменения шрифта интерфейса требуют перезапуска", "pt": "Dica: alterações de fonte da UI exigem reinício"},
    "log_group": {"zh": "日志", "zh-tw": "日誌", "en": "Logs", "ja": "ログ", "ko": "로그", "fr": "Journaux", "de": "Protokolle", "es": "Registros", "ru": "Журналы", "pt": "Registros"},
    "log_hint": {"zh": "运行日志自动保存到 %APPDATA%/vrc_trans/app.log，单文件最大 2MB，自动轮转。遇到问题时可查看此文件。", "zh-tw": "執行日誌自動儲存到 %APPDATA%/vrc_trans/app.log，單檔最大 2MB，自動輪轉。遇到問題時可查看此檔案。", "en": "Logs are saved to %APPDATA%/vrc_trans/app.log, max 2MB per file, auto rotated. Check this file when troubleshooting.", "ja": "ログは %APPDATA%/vrc_trans/app.log に自動保存、最大2MB、自動ローテーション。問題発生時はこのファイルを確認してください。", "ko": "로그는 %APPDATA%/vrc_trans/app.log에 자동 저장, 최대 2MB, 자동 회전. 문제 발생 시 이 파일을 확인하세요.", "fr": "Les journaux sont enregistrés dans %APPDATA%/vrc_trans/app.log, max 2Mo, rotation auto. Consultez ce fichier en cas de problème.", "de": "Protokolle werden in %APPDATA%/vrc_trans/app.log gespeichert, max 2MB, automatische Rotation. Bei Problemen diese Datei prüfen.", "es": "Los registros se guardan en %APPDATA%/vrc_trans/app.log, máx 2MB, rotación automática. Revisa este archivo si hay problemas.", "ru": "Журналы сохраняются в %APPDATA%/vrc_trans/app.log, макс 2МБ, авто-ротация. При проблемах проверьте этот файл.", "pt": "Os registros são salvos em %APPDATA%/vrc_trans/app.log, máx 2MB, rotação automática. Verifique este arquivo se houver problemas."},
    "text_stroke_enabled": {"zh": "文字描边", "zh-tw": "文字描邊", "en": "Text Stroke", "ja": "文字の縁取り", "ko": "텍스트 외곽선", "fr": "Contour du texte", "de": "Textumrandung", "es": "Contorno de texto", "ru": "Обводка текста", "pt": "Contorno do texto"},
    "text_shadow_enabled": {"zh": "文字阴影", "zh-tw": "文字陰影", "en": "Text Shadow", "ja": "文字の影", "ko": "텍스트 그림자", "fr": "Ombre du texte", "de": "Textschatten", "es": "Sombra de texto", "ru": "Тень текста", "pt": "Sombra do texto"},
}


class Locale:
    """语言管理单例"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._lang = "auto"
        return cls._instance

    def set_language(self, lang):
        """设置语言: auto / zh / zh-tw / en / ja / ko / fr / de / es / ru / pt"""
        self._lang = lang

    def get_language(self):
        return self._lang

    def _resolve_lang(self):
        """解析实际使用的语言代码"""
        if self._lang == "auto":
            sys_lang = QLocale.system().name()  # 如 "zh_CN", "zh_TW", "en_US", "ja_JP"
            # 繁体中文检测：zh_TW / zh_HK / zh_MO
            if sys_lang.startswith("zh_TW") or sys_lang.startswith("zh_HK") or sys_lang.startswith("zh_MO"):
                return "zh-tw"
            prefix = sys_lang.split("_")[0]
            supported = ["zh", "en", "ja", "ko", "fr", "de", "es", "ru", "pt"]
            if prefix in supported:
                return prefix
            return "en"
        return self._lang

    def tr(self, key):
        """获取翻译文本"""
        lang = self._resolve_lang()
        entry = TRANSLATIONS.get(key)
        if entry:
            return entry.get(lang, entry.get("en", key))
        return key


# 全局便捷函数
def tr(key):
    return Locale().tr(key)
