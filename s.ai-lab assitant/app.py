import streamlit as st
import json
from datetime import datetime, timedelta
import os

# Configuración de la página
st.set_page_config(
    page_title="S.AI - Asesor Farmacológico",
    page_icon="💊",
    layout="wide"
)

# Sistema de códigos y límites
CODIGOS = {
    "EXTRA2024": {
        "tipo": "gratis",
        "limite_diario": 5,
        "temas_disponibles": ["Dosificación", "Soluciones Porcentuales"],
        "expira": "2024-12-08",
        "usos_maximos": 500,
        "usos_actuales": 0
    }
}

# Función para generar códigos premium (se llamará después del pago)
def generar_codigo_premium(precio):
    codigo = f"PREMIUM{datetime.now().strftime('%Y%m%d%H%M%S')}"
    CODIGOS[codigo] = {
        "tipo": "premium" if precio == 399 else "basico",
        "limite_diario": 999 if precio == 399 else 20,
        "temas_disponibles": ["Dosificación", "Soluciones Porcentuales", "Conversiones Métricas", 
                             "Normalidad", "Molaridad", "Farmacocinética"],
        "expira": (datetime.now() + timedelta(days=90 if precio == 399 else 10)).strftime("%Y-%m-%d"),
        "usado": False
    }
    return codigo

# Inicializar session state
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
if 'codigo_actual' not in st.session_state:
    st.session_state.codigo_actual = None
if 'problemas_hoy' not in st.session_state:
    st.session_state.problemas_hoy = 0
if 'ultima_fecha' not in st.session_state:
    st.session_state.ultima_fecha = datetime.now().strftime("%Y-%m-%d")

# Resetear contador diario
fecha_hoy = datetime.now().strftime("%Y-%m-%d")
if st.session_state.ultima_fecha != fecha_hoy:
    st.session_state.problemas_hoy = 0
    st.session_state.ultima_fecha = fecha_hoy

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1E88E5;
        font-size: 3em;
        font-weight: bold;
        margin-bottom: 0.5em;
    }
    .sub-header {
        text-align: center;
        color: #666;
        font-size: 1.2em;
        margin-bottom: 2em;
    }
    .upgrade-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2em;
        border-radius: 10px;
        color: white;
        margin: 2em 0;
    }
    .precio {
        font-size: 2.5em;
        font-weight: bold;
        color: #FFD700;
    }
    .contador {
        background: #f0f0f0;
        padding: 1em;
        border-radius: 5px;
        text-align: center;
        font-size: 1.2em;
        margin: 1em 0;
    }
</style>
""", unsafe_allow_html=True)

# Pantalla de login
if not st.session_state.autenticado:
    st.markdown('<p class="main-header">💊 S.AI</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Asesor Farmacológico Especializado</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.info("🎓 **ACCESO GRATIS PARA EL EXTRAORDINARIO**\n\nCódigo: **EXTRA2024**\n\n✅ 5 problemas diarios\n✅ Dosificación y Porcentajes\n✅ Válido hasta el 8 de diciembre")
        
        codigo_input = st.text_input("Ingresa tu código de acceso:", placeholder="EXTRA2024")
        
        if st.button("🚀 ACCEDER", use_container_width=True):
            if codigo_input in CODIGOS:
                codigo_data = CODIGOS[codigo_input]
                
                # Verificar si el código ha expirado
                if datetime.strptime(codigo_data["expira"], "%Y-%m-%d") < datetime.now():
                    st.error("❌ Este código ha expirado")
                # Verificar usos máximos (solo para códigos gratuitos)
                elif codigo_data["tipo"] == "gratis" and codigo_data["usos_actuales"] >= codigo_data["usos_maximos"]:
                    st.error("❌ Este código ha alcanzado el límite de usuarios")
                # Verificar si código premium ya fue usado
                elif codigo_data.get("usado", False):
                    st.error("❌ Este código ya ha sido utilizado")
                else:
                    # Autenticar
                    st.session_state.autenticado = True
                    st.session_state.codigo_actual = codigo_input
                    
                    # Incrementar contador de usos para códigos gratuitos
                    if codigo_data["tipo"] == "gratis":
                        CODIGOS[codigo_input]["usos_actuales"] += 1
                    else:
                        CODIGOS[codigo_input]["usado"] = True
                    
                    st.rerun()
            else:
                st.error("❌ Código inválido")
        
        st.markdown("---")
        st.markdown("### 🔓 ¿Necesitas acceso completo?")
        st.markdown("Contáctanos vía WhatsApp: **+52 81 1009 4890**")

# Pantalla principal (después de autenticarse)
else:
    codigo_data = CODIGOS[st.session_state.codigo_actual]
    
    # Header
    col1, col2, col3 = st.columns([2, 3, 2])
    with col1:
        st.markdown(f"### 👤 Usuario {st.session_state.codigo_actual[:8]}...")
        st.caption(f"Plan: **{codigo_data['tipo'].upper()}**")
    with col3:
        if st.button("🚪 Cerrar Sesión"):
            st.session_state.autenticado = False
            st.rerun()
    
    # Contador de problemas
    limite = codigo_data["limite_diario"]
    restantes = limite - st.session_state.problemas_hoy
    
    if restantes > 0:
        st.markdown(f'<div class="contador">📊 Problemas disponibles hoy: <strong>{restantes}/{limite}</strong></div>', 
                   unsafe_allow_html=True)
    else:
        st.error(f"⚠️ Has alcanzado el límite diario de {limite} problemas. Regresa mañana o actualiza tu plan.")
    
    # Mostrar upgrade si es usuario gratuito
    if codigo_data["tipo"] == "gratis":
        st.markdown("""
        <div class="upgrade-box">
            <h2>🔓 DESBLOQUEA TODO EL POTENCIAL</h2>
            <p>Ya resolviste algunos problemas con S.AI. Pero tu extraordinario cubre 6 temas, no solo 2.</p>
            <br>
            <h3>📦 PLAN BÁSICO</h3>
            <p class="precio">$199 MXN</p>
            <ul>
                <li>✅ 20 problemas diarios</li>
                <li>✅ TODOS los 6 temas</li>
                <li>✅ Acceso hasta después del extra (10 días)</li>
            </ul>
            <br>
            <h3>💎 PLAN PREMIUM</h3>
            <p class="precio">$399 MXN</p>
            <ul>
                <li>✅ Problemas ILIMITADOS</li>
                <li>✅ TODOS los 6 temas</li>
                <li>✅ Acceso permanente (90 días)</li>
                <li>✅ Soporte prioritario</li>
            </ul>
            <br>
            <p><strong>💳 TRANSFERENCIA BANCARIA</strong></p>
            <p>BBVA: 1234567890</p>
            <p>CLABE: 012345678901234567</p>
            <br>
            <p>📱 Envía tu comprobante a WhatsApp: <strong>+52 81 1009 4890</strong></p>
            <p>⚡ Activación en menos de 1 hora</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Sección de resolución de problemas
    if restantes > 0:
        st.markdown("---")
        st.markdown("## 🧪 Resolver Problema")
        
        # Selector de tema
        tema = st.selectbox(
            "Selecciona el tema:",
            codigo_data["temas_disponibles"]
        )
        
        # Input del problema
        problema = st.text_area(
            "Describe tu problema o pregunta:",
            placeholder="Ejemplo: Paciente de 25kg necesita Amoxicilina 50mg/kg/día cada 8 horas. La presentación es al 5%. ¿Cuántos mL por dosis?",
            height=150
        )
        
        if st.button("✨ Resolver Problema", use_container_width=True, type="primary"):
            if problema.strip():
                # Aquí irá la integración con la API (Claude o OpenAI)
                st.session_state.problemas_hoy += 1
                
                with st.spinner("🔬 Analizando tu problema..."):
                    # PLACEHOLDER - Aquí conectaremos la API
                    st.success("✅ Problema procesado")
                    
                    st.markdown("### 📋 Análisis del Problema")
                    st.info("""
                    **NOTA TEMPORAL:** La conexión con la IA se activará en el siguiente paso.
                    
                    Por ahora, este es el flujo:
                    1. Identificación del tipo de problema
                    2. Extracción de datos clave
                    3. Aplicación del algoritmo correcto
                    4. Solución paso a paso
                    5. Respuesta final con 2 decimales
                    """)
                    
                    # Mostrar problemas restantes
                    nuevos_restantes = limite - st.session_state.problemas_hoy
                    st.caption(f"Te quedan {nuevos_restantes} problemas hoy")
            else:
                st.warning("⚠️ Por favor describe tu problema")
    
    # Footer
    st.markdown("---")
    st.caption("Desarrollado por @sairammg | WhatsApp: +52 81 1009 4890")
