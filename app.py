import streamlit as st
from anthropic import Anthropic
from datetime import datetime, timedelta
import json

# Configuración de la página
st.set_page_config(
    page_title="S.AI - Asesor Farmacológico",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Inicializar cliente de Anthropic
@st.cache_resource
def get_anthropic_client():
    return Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

# Sistema de códigos y límites
CODIGOS = {
    "EXTRA2025": {
        "tipo": "gratis",
        "limite_diario": 5,
        "temas_disponibles": ["Dosificación", "Soluciones Porcentuales", "Conversiones Métricas"],
        "expira": "2025-12-05",
        "usos_maximos": 500,
        "usos_actuales": 0,
        "nombre_plan": "Plan Gratuito"
    }
}

# Prompt del sistema para S.AI
SYSTEM_PROMPT = """Eres S.AI, un Asesor Farmacológico Especializado entrenado específicamente para resolver problemas de laboratorio de Farmacología y Toxicología de la UANL.

IMPORTANTE: Eres un TUTOR conversacional. Los estudiantes te escriben como si estuvieras en WhatsApp.

## ESTILO DE COMUNICACIÓN
- Responde de forma natural y conversacional
- Sé amigable pero profesional
- Usa emojis ocasionalmente (💊 🧪 📊)
- Si el estudiante saluda, salúdalo de vuelta
- Si pregunta algo general, responde brevemente
- Si te da un problema, resuélvelo paso a paso

## REGLAS CRÍTICAS PARA PROBLEMAS

### Precisión Técnica
1. **Densidad del etanol**: SIEMPRE 0.79 g/mL
2. **Decimales**: SIEMPRE exactamente 2 decimales en procedimientos y respuesta final
3. **Conversiones estándar**:
   - 20 gotas = 1 mL
   - 60 microgotas = 1 mL
   - 1000 mg = 1 g
   - 1000 mL = 1 L

### Distinción Crítica
- **"Aforar"**: Diluir HASTA completar el volumen final
- **"Diluir"**: AGREGAR volumen

### Pesos Moleculares Fijos
- CaCl₂ = 111 g/mol
- NaCl = 58.5 g/mol
- KCl = 74.5 g/mol

## CUANDO TE DEN UN PROBLEMA

Usa este formato:

**🔍 Análisis**
Tipo: [Dosificación/Porcentaje/etc.]
Datos: [lista breve]

**⚙️ Solución**
Paso 1: [nombre]
Cálculo: [fórmula]
Resultado: XX.XX [unidades]

Paso 2: [nombre]
Cálculo: [fórmula]
Resultado: XX.XX [unidades]

**✅ Respuesta: XX.XX [unidades]**

**💡 Concepto:** [1-2 líneas explicando por qué importa]

---

SIEMPRE usa exactamente 2 decimales."""

# Inicializar session state
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
if 'codigo_actual' not in st.session_state:
    st.session_state.codigo_actual = None
if 'mensajes_hoy' not in st.session_state:
    st.session_state.mensajes_hoy = 0
if 'ultima_fecha' not in st.session_state:
    st.session_state.ultima_fecha = datetime.now().strftime("%Y-%m-%d")
if 'conversacion' not in st.session_state:
    st.session_state.conversacion = []

# Resetear contador diario
fecha_hoy = datetime.now().strftime("%Y-%m-%d")
if st.session_state.ultima_fecha != fecha_hoy:
    st.session_state.mensajes_hoy = 0
    st.session_state.ultima_fecha = fecha_hoy

# CSS estilo ChatGPT - Ultra minimalista
st.markdown("""
<style>
    /* Import Inter font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Ocultar elementos de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* Reset general */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    
    /* Fondo blanco puro estilo ChatGPT */
    .stApp {
        background: #ffffff;
    }
    
    /* Container principal */
    .main .block-container {
        padding: 0;
        max-width: 100%;
    }
    
    /* Header estilo ChatGPT */
    .chat-header {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        height: 64px;
        background: #ffffff;
        border-bottom: 1px solid #e5e7eb;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 24px;
        z-index: 1000;
    }
    
    .chat-logo {
        font-family: 'Inter', sans-serif;
        font-size: 16px;
        font-weight: 600;
        color: #111827;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .chat-actions {
        display: flex;
        gap: 12px;
        align-items: center;
    }
    
    /* Mensajes container estilo ChatGPT */
    .messages-container {
        margin-top: 64px;
        margin-bottom: 180px;
        padding: 24px 0;
    }
    
    .message-wrapper {
        width: 100%;
        display: flex;
        justify-content: center;
        padding: 24px 16px;
    }
    
    .message-wrapper.user {
        background: #ffffff;
    }
    
    .message-wrapper.assistant {
        background: #f7f7f8;
    }
    
    .message-content {
        max-width: 720px;
        width: 100%;
    }
    
    .message-text {
        font-family: 'Inter', sans-serif;
        font-size: 16px;
        font-weight: 400;
        line-height: 150%;
        color: #374151;
        word-wrap: break-word;
    }
    
    .message-text strong {
        font-weight: 600;
        color: #111827;
    }
    
    /* Input container estilo ChatGPT */
    .input-container {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: linear-gradient(to top, #ffffff 0%, rgba(255,255,255,0.95) 100%);
        padding: 24px 0 32px 0;
        z-index: 1000;
    }
    
    .input-wrapper {
        max-width: 720px;
        margin: 0 auto;
        padding: 0 16px;
    }
    
    /* Input field estilo ChatGPT */
    .stTextInput > div > div > input {
        font-family: 'Inter', sans-serif;
        font-size: 16px;
        font-weight: 400;
        line-height: 150%;
        color: #111827;
        background: #ffffff;
        border: 1px solid #d1d5db;
        border-radius: 12px;
        padding: 16px 48px 16px 16px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        transition: all 0.2s ease;
    }
    
    .stTextInput > div > div > input:focus {
        outline: none;
        border-color: #10a37f;
        box-shadow: 0 0 0 3px rgba(16,163,127,0.1);
    }
    
    .stTextInput > div > div > input::placeholder {
        color: #9ca3af;
        opacity: 1;
    }
    
    /* Botones estilo ChatGPT */
    .stButton > button {
        font-family: 'Inter', sans-serif;
        font-size: 14px;
        font-weight: 500;
        line-height: 120%;
        color: #ffffff;
        background: #10a37f;
        border: none;
        border-radius: 8px;
        padding: 10px 16px;
        transition: all 0.2s ease;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    
    .stButton > button:hover {
        background: #0e906f;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .stButton > button:active {
        transform: scale(0.98);
    }
    
    /* Botón secundario */
    .btn-secondary {
        font-family: 'Inter', sans-serif;
        font-size: 14px;
        font-weight: 500;
        color: #374151;
        background: #ffffff;
        border: 1px solid #d1d5db;
        border-radius: 8px;
        padding: 8px 14px;
        transition: all 0.2s ease;
    }
    
    .btn-secondary:hover {
        background: #f9fafb;
        border-color: #9ca3af;
    }
    
    /* Welcome screen estilo ChatGPT */
    .welcome-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: calc(100vh - 240px);
        padding: 48px 24px;
        text-align: center;
    }
    
    .welcome-title {
        font-family: 'Inter', sans-serif;
        font-size: 28px;
        font-weight: 600;
        line-height: 130%;
        color: #111827;
        margin-bottom: 16px;
    }
    
    .welcome-subtitle {
        font-family: 'Inter', sans-serif;
        font-size: 16px;
        font-weight: 400;
        line-height: 150%;
        color: #6b7280;
        margin-bottom: 48px;
        max-width: 560px;
    }
    
    /* Suggestion cards estilo ChatGPT */
    .suggestion-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
        gap: 12px;
        max-width: 720px;
        width: 100%;
        margin-bottom: 32px;
    }
    
    .suggestion-card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 16px;
        text-align: left;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .suggestion-card:hover {
        background: #f9fafb;
        border-color: #d1d5db;
    }
    
    .suggestion-emoji {
        font-size: 20px;
        margin-bottom: 8px;
    }
    
    .suggestion-title {
        font-family: 'Inter', sans-serif;
        font-size: 14px;
        font-weight: 500;
        line-height: 140%;
        color: #111827;
        margin-bottom: 4px;
    }
    
    .suggestion-desc {
        font-family: 'Inter', sans-serif;
        font-size: 12px;
        font-weight: 400;
        line-height: 140%;
        color: #6b7280;
        opacity: 0.7;
    }
    
    /* Status bar */
    .status-bar {
        position: fixed;
        top: 64px;
        left: 0;
        right: 0;
        background: #f9fafb;
        border-bottom: 1px solid #e5e7eb;
        padding: 12px 24px;
        z-index: 999;
    }
    
    .status-content {
        max-width: 720px;
        margin: 0 auto;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .status-text {
        font-family: 'Inter', sans-serif;
        font-size: 13px;
        font-weight: 500;
        line-height: 120%;
        color: #6b7280;
    }
    
    .status-count {
        font-weight: 600;
        color: #10a37f;
    }
    
    /* Login screen estilo ChatGPT */
    .login-container {
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 100vh;
        background: #ffffff;
    }
    
    .login-card {
        max-width: 440px;
        width: 100%;
        padding: 48px 40px;
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    
    .login-header {
        text-align: center;
        margin-bottom: 32px;
    }
    
    .login-logo {
        font-family: 'Inter', sans-serif;
        font-size: 32px;
        font-weight: 700;
        color: #111827;
        margin-bottom: 8px;
    }
    
    .login-tagline {
        font-family: 'Inter', sans-serif;
        font-size: 16px;
        font-weight: 400;
        line-height: 150%;
        color: #6b7280;
    }
    
    .code-box {
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 24px;
        text-align: center;
        margin: 24px 0;
    }
    
    .code-label {
        font-family: 'Inter', sans-serif;
        font-size: 13px;
        font-weight: 500;
        color: #6b7280;
        margin-bottom: 8px;
    }
    
    .code-value {
        font-family: 'Inter', monospace;
        font-size: 24px;
        font-weight: 600;
        color: #10a37f;
        letter-spacing: 2px;
    }
    
    .feature-list {
        margin: 24px 0;
    }
    
    .feature-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px 0;
        font-family: 'Inter', sans-serif;
        font-size: 14px;
        font-weight: 400;
        line-height: 150%;
        color: #374151;
    }
    
    .feature-check {
        color: #10a37f;
        font-size: 18px;
    }
    
    .contact-box {
        margin-top: 32px;
        padding-top: 32px;
        border-top: 1px solid #e5e7eb;
        text-align: center;
    }
    
    .contact-title {
        font-family: 'Inter', sans-serif;
        font-size: 13px;
        font-weight: 500;
        color: #6b7280;
        margin-bottom: 8px;
    }
    
    .contact-value {
        font-family: 'Inter', sans-serif;
        font-size: 14px;
        font-weight: 600;
        color: #10a37f;
    }
    
    /* Disclaimer */
    .disclaimer {
        font-family: 'Inter', sans-serif;
        font-size: 12px;
        font-weight: 400;
        line-height: 140%;
        color: #9ca3af;
        text-align: center;
        margin-top: 24px;
    }
    
    /* Limit reached */
    .limit-box {
        max-width: 560px;
        margin: 48px auto;
        padding: 32px;
        background: #fef2f2;
        border: 1px solid #fee2e2;
        border-radius: 12px;
        text-align: center;
    }
    
    .limit-title {
        font-family: 'Inter', sans-serif;
        font-size: 20px;
        font-weight: 500;
        color: #991b1b;
        margin-bottom: 12px;
    }
    
    .limit-text {
        font-family: 'Inter', sans-serif;
        font-size: 14px;
        font-weight: 400;
        line-height: 150%;
        color: #7f1d1d;
        margin-bottom: 24px;
    }
    
    /* Spinner */
    .spinner {
        display: inline-block;
        width: 16px;
        height: 16px;
        border: 2px solid #e5e7eb;
        border-top-color: #10a37f;
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
    }
    
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .chat-header {
            padding: 0 16px;
        }
        
        .welcome-title {
            font-size: 24px;
        }
        
        .suggestion-grid {
            grid-template-columns: 1fr;
        }
        
        .login-card {
            margin: 16px;
            padding: 32px 24px;
        }
    }
</style>
""", unsafe_allow_html=True)

# Función para consultar a Claude
def consultar_claude(mensaje_usuario, historial=[]):
    try:
        client = get_anthropic_client()
        
        mensajes = []
        for msg in historial:
            mensajes.append({"role": msg["role"], "content": msg["content"]})
        
        mensajes.append({"role": "user", "content": mensaje_usuario})
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            messages=mensajes
        )
        
        return response.content[0].text
    
    except Exception as e:
        return f"Error al procesar tu solicitud. Por favor intenta de nuevo.\n\nSi el problema persiste, contacta soporte: +52 81 1009 4890"

# ============================
# PANTALLA DE LOGIN
# ============================
if not st.session_state.autenticado:
    st.markdown("""
    <div class="login-container">
        <div class="login-card">
            <div class="login-header">
                <div class="login-logo">S.AI</div>
                <div class="login-tagline">Asesor Farmacológico UANL</div>
            </div>
            
            <div class="code-box">
                <div class="code-label">Código de Acceso Gratuito</div>
                <div class="code-value">EXTRA2025</div>
            </div>
            
            <div class="feature-list">
                <div class="feature-item">
                    <span class="feature-check">✓</span>
                    <span>5 conversaciones diarias con IA especializada</span>
                </div>
                <div class="feature-item">
                    <span class="feature-check">✓</span>
                    <span>Disponible 24/7 hasta el 5 de diciembre</span>
                </div>
                <div class="feature-item">
                    <span class="feature-check">✓</span>
                    <span>Algoritmos paso a paso</span>
                </div>
                <div class="feature-item">
                    <span class="feature-check">✓</span>
                    <span>Casos clínicos reales</span>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Input container
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        codigo_input = st.text_input("", placeholder="Ingresa tu código", label_visibility="collapsed", key="codigo_login")
        
        if st.button("Acceder", use_container_width=True):
            if codigo_input in CODIGOS:
                codigo_data = CODIGOS[codigo_input]
                
                if datetime.strptime(codigo_data["expira"], "%Y-%m-%d") < datetime.now():
                    st.error("Este código ha expirado")
                elif codigo_data["tipo"] == "gratis" and codigo_data["usos_actuales"] >= codigo_data["usos_maximos"]:
                    st.error("Este código ha alcanzado el límite de usuarios")
                elif codigo_data.get("usado", False):
                    st.error("Este código ya ha sido utilizado")
                else:
                    st.session_state.autenticado = True
                    st.session_state.codigo_actual = codigo_input
                    
                    if codigo_data["tipo"] == "gratis":
                        CODIGOS[codigo_input]["usos_actuales"] += 1
                    else:
                        CODIGOS[codigo_input]["usado"] = True
                    
                    st.rerun()
            else:
                st.error("Código inválido")
        
        st.markdown("""
        <div class="contact-box">
            <div class="contact-title">¿Necesitas más conversaciones?</div>
            <div class="contact-value">WhatsApp: +52 81 1009 4890</div>
            <div style="margin-top: 8px; font-size: 12px; color: #9ca3af;">@sairammg</div>
        </div>
        """, unsafe_allow_html=True)

# ============================
# PANTALLA DE CHAT
# ============================
else:
    codigo_data = CODIGOS[st.session_state.codigo_actual]
    limite = codigo_data["limite_diario"]
    restantes = limite - st.session_state.mensajes_hoy
    
    # Header
    st.markdown(f"""
    <div class="chat-header">
        <div class="chat-logo">
            <span>💊</span>
            <span>S.AI</span>
        </div>
        <div class="chat-actions">
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Status bar
    if restantes <= 3:
        color = "#ef4444" if restantes <= 1 else "#f59e0b"
        st.markdown(f"""
        <div class="status-bar">
            <div class="status-content">
                <span class="status-text">
                    <span class="status-count" style="color: {color};">{restantes} / {limite}</span> conversaciones restantes hoy
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        messages_top_margin = 112  # 64px header + 48px status
    else:
        messages_top_margin = 64  # solo header
    
    # Messages container
    if not st.session_state.conversacion:
        # Welcome screen
        st.markdown(f"""
        <div style="margin-top: {messages_top_margin}px;">
            <div class="welcome-container">
                <div class="welcome-title">¿En qué te puedo ayudar?</div>
                <div class="welcome-subtitle">
                    Especializado en Farmacología UANL. Pregunta sobre dosificación, 
                    soluciones porcentuales, conversiones métricas y más.
                </div>
                <div class="suggestion-grid">
                    <div class="suggestion-card">
                        <div class="suggestion-emoji">💊</div>
                        <div class="suggestion-title">Dosificación</div>
                        <div class="suggestion-desc">Cálculos clínicos paso a paso</div>
                    </div>
                    <div class="suggestion-card">
                        <div class="suggestion-emoji">🧪</div>
                        <div class="suggestion-title">Soluciones</div>
                        <div class="suggestion-desc">Porcentuales y concentraciones</div>
                    </div>
                    <div class="suggestion-card">
                        <div class="suggestion-emoji">📊</div>
                        <div class="suggestion-title">Conversiones</div>
                        <div class="suggestion-desc">Métricas y unidades</div>
                    </div>
                    <div class="suggestion-card">
                        <div class="suggestion-emoji">⚗️</div>
                        <div class="suggestion-title">Molaridad</div>
                        <div class="suggestion-desc">Y normalidad química</div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Messages
        st.markdown(f'<div class="messages-container" style="margin-top: {messages_top_margin}px;">', unsafe_allow_html=True)
        
        for msg in st.session_state.conversacion:
            role_class = "user" if msg["role"] == "user" else "assistant"
            content = msg["content"].replace("\n", "<br>")
            
            st.markdown(f"""
            <div class="message-wrapper {role_class}">
                <div class="message-content">
                    <div class="message-text">{content}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Input container (fixed at bottom)
    st.markdown('<div class="input-container">', unsafe_allow_html=True)
    
    if restantes > 0:
        col1, col2, col3 = st.columns([1, 6, 1])
        
        with col1:
            if st.button("Nuevo", key="nuevo_chat"):
                st.session_state.conversacion = []
                st.rerun()
        
        with col2:
            mensaje = st.text_input(
                "", 
                placeholder="Escribe tu pregunta o problema...", 
                label_visibility="collapsed", 
                key="mensaje_input"
            )
        
        with col3:
            if st.button("Salir", key="salir"):
                st.session_state.autenticado = False
                st.session_state.conversacion = []
                st.rerun()
        
        if mensaje and mensaje.strip():
            # Agregar mensaje del usuario
            st.session_state.conversacion.append({
                "role": "user",
                "content": mensaje
            })
            
            # Obtener respuesta de Claude
            with st.spinner(""):
                respuesta = consultar_claude(
                    mensaje,
                    st.session_state.conversacion[:-1]
                )
            
            # Agregar respuesta
            st.session_state.conversacion.append({
                "role": "assistant",
                "content": respuesta
            })
            
            # Incrementar contador
            st.session_state.mensajes_hoy += 1
            
            st.rerun()
    else:
        # Límite alcanzado
        col1, col2, col3 = st.columns([1, 6, 1])
        
        with col2:
            st.markdown("""
            <div class="limit-box">
                <div class="limit-title">Límite diario alcanzado</div>
                <div class="limit-text">
                    Has usado todas tus conversaciones de hoy. Regresa mañana para 5 nuevas 
                    conversaciones o actualiza a premium para acceso ilimitado.
                </div>
                <div class="contact-value">WhatsApp: +52 81 1009 4890</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            if st.button("Salir", key="salir_limite"):
                st.session_state.autenticado = False
                st.session_state.conversacion = []
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Disclaimer
    st.markdown("""
    <div class="disclaimer">
        S.AI puede cometer errores. Verifica información importante.
    </div>
    """, unsafe_allow_html=True)
