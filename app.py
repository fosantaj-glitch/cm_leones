import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import time

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Club de Leones Cumbayá-Ilaló", page_icon="🦁", layout="wide")

# --- 2. ESTILOS SOBRIOS Y ELEGANTES ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    [data-testid="stSidebar"] { background-color: #003366; }
    [data-testid="stSidebar"] * { color: white; }
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; background-color: #003366; color: white; border: 1px solid #d4af37; font-weight: bold; }
    .stButton>button:hover { background-color: #d4af37; color: #003366; }
    .card { background-color: white; padding: 25px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); border-top: 5px solid #d4af37; }
    h1, h2, h3 { color: #003366; font-family: 'Segoe UI', sans-serif; }
    .total-box { background-color: #003366; color: #d4af37; padding: 20px; border-radius: 10px; text-align: center; font-size: 24px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. BASE DE DATOS ---
def get_connection():
    return sqlite3.connect('club_leones_centro_medico.db', check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, cedula TEXT, bloque TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS profesionales (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, cedula TEXT)')
    c.execute('''CREATE TABLE IF NOT EXISTS consultas 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, forma_pago TEXT, medico TEXT, 
                  paciente TEXT, cedula TEXT, telefono TEXT, v_consulta REAL, v_proc REAL, 
                  v_inyec REAL, v_cert REAL, total REAL, observaciones TEXT)''')
    c.execute('CREATE TABLE IF NOT EXISTS agendamientos (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, medico TEXT, hora TEXT, paciente TEXT, telefono TEXT)')
    conn.commit()
    conn.close()

init_db()

# --- 4. GESTIÓN DE ESTADO ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.user_role = None
    st.session_state.user_name = None

# --- 5. LOGIN ---
def login():
    # Logo central
    c_l1, c_l2, c_l3 = st.columns([1, 0.8, 1])
    with c_l2:
        try: st.image("logo leones.jpg", use_container_width=True)
        except: pass

    st.markdown("<h1 style='text-align: center;'>CLUB DE LEONES CUMBAYA-ILALO</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #d4af37; font-size: 1.1em; letter-spacing: 2px;'>CENTRO MÉDICO</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("ACCESO AL SISTEMA")
        u_input = st.text_input("Usuario")
        p_input = st.text_input("Clave", type="password")
        
        if st.button("INGRESAR"):
            # Acceso Maestro
            if u_input == "CMLeones" and p_input == "2468":
                st.session_state.autenticado = True
                st.session_state.user_role = "ADMINISTRACION"
                st.session_state.user_name = "Administrador Maestro"
                st.rerun()
            else:
                conn = get_connection()
                res = conn.execute("SELECT nombre, bloque FROM usuarios WHERE nombre=? AND cedula=?", (u_input, p_input)).fetchone()
                conn.close()
                if res:
                    st.session_state.autenticado = True
                    st.session_state.user_name = res[0]
                    st.session_state.user_role = res[1]
                    st.rerun()
                else:
                    st.error("Acceso denegado. Verifique usuario y clave.")
        st.markdown("</div>", unsafe_allow_html=True)

# --- 6. BLOQUES DE LA APP ---
def bloque_administracion():
    st.title("⚙️ ADMINISTRACIÓN")
    menu = st.sidebar.selectbox("MENÚ", ["GESTIÓN DE PERMISOS", "GESTIÓN PROFESIONALES", "BASE DE DATOS PACIENTES", "LIQUIDACIÓN MENSUAL"])

    if menu == "GESTIÓN DE PERMISOS":
        st.header("🛂 Control de Permisos")
        with st.form("f_per", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            n = c1.text_input("Nombre de Usuario")
            c = c2.text_input("Cédula (Clave)")
            b = c3.selectbox("Asignar Bloque", ["RECEPCION", "CONTABILIDAD"])
            if st.form_submit_button("Guardar"):
                if n and c:
                    db = get_connection(); db.execute("INSERT INTO usuarios (nombre, cedula, bloque) VALUES (?,?,?)", (n, c, b)); db.commit(); db.close()
                    st.success("Permiso registrado"); st.rerun()
        
        df_u = pd.read_sql("SELECT id, nombre, cedula as Clave, bloque FROM usuarios", get_connection())
        st.dataframe(df_u, use_container_width=True, hide_index=True)

    elif menu == "GESTIÓN PROFESIONALES":
        st.header("👨‍⚕️ Especialistas")
        with st.form("f_prof", clear_on_submit=True):
            n_p = st.text_input("Nombre del Médico")
            c_p = st.text_input("Cédula")
            if st.form_submit_button("Registrar"):
                db = get_connection(); db.execute("INSERT INTO profesionales (nombre, cedula) VALUES (?,?)", (n_p, c_p)); db.commit(); db.close(); st.rerun()
        
        df_p = pd.read_sql("SELECT * FROM profesionales", get_connection())
        st.table(df_p)

def bloque_recepcion():
    st.title("🛎️ RECEPCIÓN")
    m = st.sidebar.radio("MENÚ", ["CAJA DIARIA", "AGENDAMIENTOS", "VISUALIZAR/EDITAR CONSULTAS"])
    
    conn = get_connection()
    profes = [p[0] for p in conn.execute("SELECT nombre FROM profesionales").fetchall()]
    conn.close()

    if m == "CAJA DIARIA":
        st.header("📝 Registro de Ingresos")
        with st.form("caja", clear_on_submit=True):
            c1, c2 = st.columns(2)
            f = c1.date_input("FECHA")
            fp = c2.selectbox("FORMA DE PAGO", ["Efectivo", "Transferencia", "Pago Plux", "Deuna", "DataFast"])
            med = c1.selectbox("MEDICO", ["Seleccione..."] + profes)
            vc = c2.number_input("VALOR CONSULTA", format="%.2f")
            pac = c1.text_input("PACIENTE")
            vp = c2.number_input("VALOR PROCEDIMIENTO", format="%.2f")
            ced = c1.text_input("CEDULA")
            vi = c2.number_input("VALOR INYECCIÓN", format="%.2f")
            tel = c1.text_input("TELÉFONO")
            vce = c2.number_input("VALOR CERTIFICADO", format="%.2f")
            obs = st.text_area("OBSERVACIONES")
            total = vc + vp + vi + vce
            st.markdown(f"<div class='total-box'>TOTAL A COBRAR: ${total:.2f}</div>", unsafe_allow_html=True)
            if st.form_submit_button("GUARDAR REGISTRO"):
                if med != "Seleccione..." and pac:
                    db = get_connection()
                    db.execute("INSERT INTO consultas (fecha, forma_pago, medico, paciente, cedula, telefono, v_consulta, v_proc, v_inyec, v_cert, total, observaciones) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (str(f), fp, med, pac, ced, tel, vc, vp, vi, vce, total, obs))
                    db.commit(); db.close(); st.success("✅ Guardado")

    elif m == "AGENDAMIENTOS":
        st.header("🗓️ Agendamientos")
        # Aquí iría el código de horarios (abreviado por espacio, mismo ADN anterior)
        st.info("Seleccione médico para ver horarios.")

# --- 7. NAVEGACIÓN ---
if not st.session_state.autenticado:
    login()
else:
    try: st.sidebar.image("logo leones.jpg", use_container_width=True)
    except: pass
    
    st.sidebar.markdown(f"**Usuario:** {st.session_state.user_name}")
    if st.sidebar.button("SALIR"):
        st.session_state.autenticado = False; st.rerun()

    if st.session_state.user_role == "ADMINISTRACION":
        bloque_administracion()
    elif st.session_state.user_role == "RECEPCION":
        bloque_recepcion()