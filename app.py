import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import time

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Club de Leones Cumbayá-Ilaló", page_icon="🦁", layout="wide")

# --- 2. ESTILOS DE CLASE MUNDIAL (HORIZONTAL Y COMPACTO) ---
st.markdown("""
    <style>
    /* Reset de márgenes para visualización en una sola página */
    .block-container { padding-top: 2rem; padding-bottom: 0rem; }
    
    [data-testid="stSidebar"] { background-color: #003366; }
    [data-testid="stSidebar"] * { color: white; }
    
    /* Botón Estilo Leones */
    .stButton>button { 
        width: 100%; border-radius: 8px; height: 3.5em; 
        background-color: #003366; color: white; 
        border: 1px solid #d4af37; font-weight: bold; 
    }
    .stButton>button:hover { background-color: #d4af37; color: #003366; }
    
    /* Tarjeta de Acceso */
    .card { 
        background-color: white; padding: 30px; 
        border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); 
        border-right: 8px solid #d4af37;
        margin-top: 10px;
    }
    
    /* Tipografía Sobria */
    h1 { color: #003366; font-family: 'Segoe UI', sans-serif; font-weight: 800; margin-bottom: 0px; line-height: 1.1; }
    .subtitle { color: #d4af37; font-weight: bold; letter-spacing: 3px; font-size: 1.2em; margin-bottom: 20px; }
    
    /* Optimización de Logo Lateral */
    .logo-side {
        display: block;
        margin-left: auto;
        margin-right: auto;
        width: 100%;
        max-width: 350px;
        filter: drop-shadow(0px 5px 5px rgba(0,0,0,0.1));
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. BASE DE DATOS ---
def get_connection():
    return sqlite3.connect('club_leones_centro_medico.db', check_same_thread=False)

def init_db():
    conn = get_connection(); c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, cedula TEXT, bloque TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS profesionales (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, cedula TEXT)')
    c.execute('''CREATE TABLE IF NOT EXISTS consultas 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, forma_pago TEXT, medico TEXT, 
                  paciente TEXT, cedula TEXT, telefono TEXT, v_consulta REAL, v_proc REAL, 
                  v_inyec REAL, v_cert REAL, total REAL, observaciones TEXT)''')
    c.execute('CREATE TABLE IF NOT EXISTS agendamientos (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, medico TEXT, hora TEXT, paciente TEXT, telefono TEXT)')
    conn.commit(); conn.close()

init_db()

# --- 4. GESTIÓN DE ESTADO ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.user_role = None
    st.session_state.user_name = None

# --- 5. LOGIN HORIZONTAL (NUEVA ARQUITECTURA) ---
def login():
    # División en dos columnas principales para evitar cortes
    col_logo, col_login = st.columns([1.2, 1])
    
    with col_logo:
        st.markdown("<br>", unsafe_allow_html=True)
        try:
            # Ubicación lateral izquierda para que no se corte
            st.image("logo leones.jpg", use_container_width=True)
        except:
            st.error("No se encontró 'logo leones.jpg'")

    with col_login:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<h1>CLUB DE LEONES</h1>", unsafe_allow_html=True)
        st.markdown("<h1>CUMBAYA-ILALO</h1>", unsafe_allow_html=True)
        st.markdown("<p class='subtitle'>CENTRO MÉDICO</p>", unsafe_allow_html=True)
        
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("ACCESO AL SISTEMA")
        
        # Selección interactiva y campos
        b_destino = st.selectbox("BLOQUE DE ACCESO", ["RECEPCION", "MEDICOS", "CONTABILIDAD", "ADMINISTRACION"])
        u_nombre = st.text_input("NOMBRE DE USUARIO")
        p_clave = st.text_input("CLAVE DE SEGURIDAD (Cédula)", type="password")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("INGRESAR"):
            if u_nombre == "CMLeones" and p_clave == "2468":
                st.session_state.autenticado = True
                st.session_state.user_role = b_destino
                st.session_state.user_name = "Administrador Maestro"
                st.rerun()
            else:
                conn = get_connection()
                res = conn.execute("SELECT nombre, bloque FROM usuarios WHERE nombre=? AND cedula=? AND bloque=?", 
                                   (u_nombre, p_clave, b_destino)).fetchone()
                conn.close()
                if res:
                    st.session_state.autenticado = True
                    st.session_state.user_name = res[0]
                    st.session_state.user_role = res[1]
                    st.rerun()
                else:
                    st.error("⚠️ Acceso denegado para el bloque seleccionado.")
        st.markdown("</div>", unsafe_allow_html=True)

# --- 6. BLOQUES (SIN CAMBIOS EN LÓGICA) ---
def bloque_administracion():
    st.title("⚙️ ADMINISTRACIÓN")
    menu = st.sidebar.selectbox("MENÚ", ["GESTIÓN DE PERMISOS", "GESTIÓN PROFESIONALES", "BASE DE DATOS PACIENTES", "LIQUIDACIÓN MENSUAL"])
    if menu == "GESTIÓN DE PERMISOS":
        st.header("🛂 Gestión de Permisos")
        with st.form("f_per", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            n, c = c1.text_input("Nombre"), c2.text_input("Cédula")
            b = c3.selectbox("Bloque", ["RECEPCION", "CONTABILIDAD", "MEDICOS"])
            if st.form_submit_button("Autorizar"):
                db = get_connection(); db.execute("INSERT INTO usuarios (nombre, cedula, bloque) VALUES (?,?,?)", (n, c, b)); db.commit(); db.close(); st.rerun()
        df_u = pd.read_sql("SELECT id, nombre, cedula as Clave, bloque as Sección FROM usuarios", get_connection())
        st.dataframe(df_u, use_container_width=True, hide_index=True)
    elif menu == "GESTIÓN PROFESIONALES":
        st.header("👨‍⚕️ Registro de Médicos")
        with st.form("f_prof", clear_on_submit=True):
            n_p, c_p = st.text_input("Nombre del Médico"), st.text_input("Cédula")
            if st.form_submit_button("Guardar"):
                db = get_connection(); db.execute("INSERT INTO profesionales (nombre, cedula) VALUES (?,?)", (n_p, c_p)); db.commit(); db.close(); st.rerun()
        st.table(pd.read_sql("SELECT * FROM profesionales", get_connection()))

def bloque_recepcion():
    st.title("🛎️ RECEPCIÓN")
    m = st.sidebar.radio("MENÚ", ["CAJA DIARIA", "AGENDAMIENTOS", "VISUALIZAR/EDITAR CONSULTAS"])
    conn = get_connection(); profes = [p[0] for p in conn.execute("SELECT nombre FROM profesionales").fetchall()]; conn.close()
    if m == "CAJA DIARIA":
        st.markdown("### 📝 REGISTRO DE INGRESOS")
        c1, c2 = st.columns(2)
        f_f, f_p = c1.date_input("FECHA"), c2.selectbox("FORMA DE PAGO", ["Efectivo", "Transferencia", "Pago Plux", "Deuna", "DataFast"])
        med, vc = c1.selectbox("Médico", ["Seleccione..."] + profes), c2.number_input("Valor Consulta", value=0.0)
        pac, vp = c1.text_input("Paciente"), c2.number_input("Valor Procedimiento", value=0.0)
        ced, vi = c1.text_input("Cédula"), c2.number_input("Valor Inyección", value=0.0)
        tel, vce = c1.text_input("Teléfono"), c2.number_input("Valor Certificado", value=0.0)
        total = vc + vp + vi + vce
        st.markdown(f"### Total: ${total:.2f}")
        if st.button("GUARDAR"):
            db = get_connection(); db.execute("INSERT INTO consultas (fecha, forma_pago, medico, paciente, cedula, telefono, v_consulta, v_proc, v_inyec, v_cert, total) VALUES (?,?,?,?,?,?,?,?,?,?,?)", (str(f_f), f_p, med, pac, ced, tel, vc, vp, vi, vce, total)); db.commit(); db.close(); st.success("✅ Guardado"); time.sleep(1); st.rerun()

# --- 7. NAVEGACIÓN ---
if not st.session_state.autenticado:
    login()
else:
    try: st.sidebar.image("logo leones.jpg", width=120)
    except: pass
    st.sidebar.markdown(f"👤 **{st.session_state.user_name}**")
    if st.sidebar.button("SALIR"):
        st.session_state.autenticado = False; st.rerun()

    if st.session_state.user_role == "ADMINISTRACION":
        bloque_administracion()
    elif st.session_state.user_role == "RECEPCION":
        bloque_recepcion()