import streamlit as st
from anthropic import Anthropic
from datetime import datetime, timedelta
import json

# Configuración de la página
st.set_page_config(
    page_title="S.AI - Asesor Farmacológico",
    page_icon="💊",
    layout="wide"
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
        "temas_disponibles": ["Dosificación", "Soluciones Porcentuales"],
        "expira": "2025-12-05",
        "usos_maximos": 500,
        "usos_actuales": 0
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
    st.session_state.conversacion = []  # Limpiar chat al día siguiente

# CSS personalizado
st.markdown("""
<style>
    /* Ocultar elementos de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Fondo */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .main .block-container {
        padding-top: 2rem;
        max-width: 900px;
    }
    
    /* Título */
    .main-header {
        text-align: center;
        color: white;
        font-size: 3em;
        font-weight: 900;
        margin-bottom: 0.2em;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .sub-header {
        text-align: center;
        color: rgba(255,255,255,0.95);
        font-size: 1.2em;
        margin-bottom: 2em;
        font-weight: 300;
    }
    
    /* Chat container */
    .chat-container {
        background: white;
        border-radius: 20px;
        padding: 1.5em;
        height: 500px;
        overflow-y: auto;
        margin-bottom: 1em;
        box-shadow: 0 8px 32px rgba(0,0,0,0.2);
    }
    
    /* Mensajes */
    .mensaje-usuario {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 12px 16px;
        border-radius: 18px 18px 4px 18px;
        margin: 8px 0;
        margin-left: auto;
        max-width: 70%;
        float: right;
        clear: both;
    }
    
    .mensaje-ai {
        background: #f0f0f0;
        color: #333;
        padding: 12px 16px;
        border-radius: 18px 18px 18px 4px;
        margin: 8px 0;
        max-width: 70%;
        float: left;
        clear: both;
    }
    
    /* Input de chat */
    .stTextInput > div > div > input {
        background: white;
        border: 2px solid #e0e0e0;
        border-radius: 25px;
        padding: 15px 20px;
        font-size: 1em;
    }
    
    /* Botón de enviar */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 12px 30px;
        font-weight: 600;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
    }
    
    /* Contador */
    .contador {
        background: white;
        padding: 1em;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 1em;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Función para consultar a Claude
def consultar_claude(mensaje_usuario, historial=[]):
    try:
        client = get_anthropic_client()
        
        # Construir historial de mensajes
        mensajes = []
        for msg in historial:
            mensajes.append({"role": msg["role"], "content": msg["content"]})
        
        # Agregar mensaje actual
        mensajes.append({"role": "user", "content": mensaje_usuario})
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            messages=mensajes
        )
        
        return response.content[0].text
    
    except Exception as e:
        return f"❌ Error: {str(e)}\n\nContacta soporte: +52 81 1009 4890"

# Pantalla de login
if not st.session_state.autenticado:
    st.markdown('<p class="main-header">💊 S.AI</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Tu Asesor de Farmacología 24/7</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style='background: white; padding: 2.5em; border-radius: 20px; box-shadow: 0 8px 32px rgba(0,0,0,0.2);'>
            <h2 style='color: #667eea; text-align: center; margin-bottom: 1em;'>🎓 ACCESO GRATIS</h2>
            <p style='text-align: center; font-size: 1.2em; color: #666; margin-bottom: 1.5em;'>
                <strong>Extraordinario 2025</strong>
            </p>
            <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1.5em; border-radius: 15px; margin-bottom: 1.5em;'>
                <p style='text-align: center; color: white; font-size: 2em; font-weight: bold; margin: 0;'>
                    EXTRA2025
                </p>
            </div>
            <div style='text-align: left; margin: 1.5em 0;'>
                <p style='color: #333; margin: 0.5em 0;'><span style='color: #667eea; font-size: 1.2em;'>✓</span> 5 conversaciones diarias</p>
                <p style='color: #333; margin: 0.5em 0;'><span style='color: #667eea; font-size: 1.2em;'>✓</span> Chat en vivo con IA especializada</p>
                <p style='color: #333; margin: 0.5em 0;'><span style='color: #667eea; font-size: 1.2em;'>✓</span> Válido hasta el 5 de diciembre 2025</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        codigo_input = st.text_input("", placeholder="Ingresa el código EXTRA2025", label_visibility="collapsed")
        
        if st.button("🚀 ACCEDER", use_container_width=True):
            if codigo_input in CODIGOS:
                codigo_data = CODIGOS[codigo_input]
                
                if datetime.strptime(codigo_data["expira"], "%Y-%m-%d") < datetime.now():
                    st.error("❌ Este código ha expirado")
                elif codigo_data["tipo"] == "gratis" and codigo_data["usos_actuales"] >= codigo_data["usos_maximos"]:
                    st.error("❌ Este código ha alcanzado el límite de usuarios")
                elif codigo_data.get("usado", False):
                    st.error("❌ Este código ya ha sido utilizado")
                else:
                    st.session_state.autenticado = True
                    st.session_state.codigo_actual = codigo_input
                    
                    if codigo_data["tipo"] == "gratis":
                        CODIGOS[codigo_input]["usos_actuales"] += 1
                    else:
                        CODIGOS[codigo_input]["usado"] = True
                    
                    st.rerun()
            else:
                st.error("❌ Código inválido")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div style='background: white; padding: 1.5em; border-radius: 15px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.1);'>
            <p style='color: #667eea; font-weight: 600; margin-bottom: 0.5em;'>🔓 ¿Necesitas más mensajes?</p>
            <p style='color: #333; margin: 0;'>WhatsApp: <strong style='color: #667eea;'>+52 81 1009 4890</strong></p>
        </div>
        """, unsafe_allow_html=True)

# Pantalla de chat
else:
    codigo_data = CODIGOS[st.session_state.codigo_actual]
    
    # Header con contador
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown('<p class="main-header">💊 S.AI Chat</p>', unsafe_allow_html=True)
    with col2:
        if st.button("🚪 Salir"):
            st.session_state.autenticado = False
            st.rerun()
    
    # Contador de mensajes
    limite = codigo_data["limite_diario"]
    restantes = limite - st.session_state.mensajes_hoy
    
    st.markdown(f"""
    <div class="contador">
        💬 <strong>{restantes}/{limite}</strong> conversaciones disponibles hoy
    </div>
    """, unsafe_allow_html=True)
    
    # Área de chat
    chat_container = st.container()
    
    with chat_container:
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        
        # Mensaje de bienvenida si no hay conversación
        if not st.session_state.conversacion:
            st.markdown("""
            <div class="mensaje-ai">
                ¡Hola! 👋 Soy S.AI, tu asesor de farmacología.
                
                Puedes preguntarme cualquier cosa sobre:
                • Dosificación clínica 💊
                • Soluciones porcentuales 🧪
                • Conversiones métricas 📊
                
                ¿En qué te puedo ayudar?
            </div>
            """, unsafe_allow_html=True)
        
        # Mostrar conversación
        for msg in st.session_state.conversacion:
            if msg["role"] == "user":
                st.markdown(f'<div class="mensaje-usuario">{msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="mensaje-ai">{msg["content"]}</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Input de mensaje
    if restantes > 0:
        col1, col2 = st.columns([5, 1])
        
        with col1:
            mensaje = st.text_input("", placeholder="Escribe tu mensaje o problema aquí...", label_visibility="collapsed", key="mensaje_input")
        
        with col2:
            enviar = st.button("📤", use_container_width=True)
        
        if enviar and mensaje.strip():
            # Agregar mensaje del usuario
            st.session_state.conversacion.append({
                "role": "user",
                "content": mensaje
            })
            
            # Obtener respuesta de Claude
            with st.spinner("💭 Pensando..."):
                respuesta = consultar_claude(
                    mensaje,
                    st.session_state.conversacion[:-1]  # Historial sin el último mensaje
                )
            
            # Agregar respuesta de Claude
            st.session_state.conversacion.append({
                "role": "assistant",
                "content": respuesta
            })
            
            # Incrementar contador
            st.session_state.mensajes_hoy += 1
            
            st.rerun()
    else:
        st.error("⚠️ Has alcanzado el límite diario. Regresa mañana o contacta para upgrade.")
        st.info("📱 WhatsApp: +52 81 1009 4890")
    
    # Botón para limpiar chat
    if st.session_state.conversacion:
        if st.button("🗑️ Limpiar chat"):
            st.session_state.conversacion = []
            st.rerun()
