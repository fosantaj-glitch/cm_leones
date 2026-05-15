import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import time

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Club de Leones Cumbayá-Ilaló", page_icon="🦁", layout="wide")

# --- 2. ESTILOS SOBRIOS Y OPTIMIZACIÓN VISUAL ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    [data-testid="stSidebar"] { background-color: #003366; }
    [data-testid="stSidebar"] * { color: white; }
    
    /* Botón Principal Azul y Oro */
    .stButton>button { 
        width: 100%; border-radius: 8px; height: 3em; 
        background-color: #003366; color: white; 
        border: 1px solid #d4af37; font-weight: bold; 
    }
    .stButton>button:hover { background-color: #d4af37; color: #003366; }
    
    /* Tarjeta de Login */
    .card { 
        background-color: white; padding: 20px; 
        border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); 
        border-top: 5px solid #d4af37; 
    }
    
    /* Títulos Sobrios */
    h1, h2, h3 { color: #003366; font-family: 'Segoe UI', sans-serif; font-weight: bold; margin-bottom: 0px; }
    
    /* Logo optimizado (Efecto nitidez) */
    .logo-img {
        image-rendering: -webkit-optimize-contrast;
        display: block;
        margin-left: auto;
        margin-right: auto;
        width: 180px; /* Tamaño reducido para evitar pixelado */
    }
    
    .total-box { 
        background-color: #f1f3f5; color: #003366; 
        padding: 10px; border-radius: 8px; 
        border: 1px solid #d4af37; font-size: 20px; font-weight: bold; 
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

# --- 5. LOGIN MODERNO Y COMPACTO ---
def login():
    # Logo reducido y centrado
    c_l1, c_l2, c_l3 = st.columns([1.2, 0.6, 1.2])
    with c_l2:
        try:
            st.markdown('<img src="https://i.ibb.co/vz0XzXn/logo-leones.jpg" class="logo-img">', unsafe_allow_html=True) 
            # Si el archivo local existe, descomenta la línea de abajo y comenta la de arriba:
            st.image("logo leones.jpg", width=180) 
        except:
            pass

    st.markdown("<h2 style='text-align: center; margin-top: 10px;'>CLUB DE LEONES CUMBAYA-ILALO</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #d4af37; font-weight: bold; margin-bottom: 20px;'>SISTEMA MÉDICO INTEGRAL</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1.1, 1, 1.1])
    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        # SELECTOR DE BLOQUE (Tu solicitud)
        bloque_destino = st.selectbox("BLOQUE DE ACCESO", ["RECEPCION", "MEDICOS", "CONTABILIDAD", "ADMINISTRACION"])
        u_nombre = st.text_input("USUARIO (Nombre)")
        p_clave = st.text_input("CLAVE (Cédula)", type="password")
        
        if st.button("ACCEDER AL SISTEMA"):
            # Validación Clave Maestra
            if u_nombre == "CMLeones" and p_clave == "2468":
                st.session_state.autenticado = True
                st.session_state.user_role = bloque_destino # Permite ir a donde elija el Admin
                st.session_state.user_name = "Administrador Maestro"
                st.rerun()
            else:
                # Validación de usuarios registrados
                conn = get_connection()
                res = conn.execute("SELECT nombre, bloque FROM usuarios WHERE nombre=? AND cedula=? AND bloque=?", 
                                   (u_nombre, p_clave, bloque_destino)).fetchone()
                conn.close()
                if res:
                    st.session_state.autenticado = True
                    st.session_state.user_name = res[0]
                    st.session_state.user_role = res[1]
                    st.rerun()
                else:
                    st.error("⚠️ Acceso no autorizado para este bloque.")
        st.markdown("</div>", unsafe_allow_html=True)

# --- 6. BLOQUES DE LA APP ---
def bloque_administracion():
    st.title("⚙️ ADMINISTRACIÓN")
    menu = st.sidebar.selectbox("MENÚ", ["GESTIÓN DE PERMISOS", "GESTIÓN PROFESIONALES", "BASE DE DATOS PACIENTES", "LIQUIDACIÓN MENSUAL"])

    if menu == "GESTIÓN DE PERMISOS":
        st.header("🛂 Gestión de Permisos")
        with st.form("f_per", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            n = c1.text_input("Nombre completo")
            c = c2.text_input("Cédula (será la clave)")
            b = c3.selectbox("Asignar bloque", ["RECEPCION", "CONTABILIDAD", "MEDICOS"])
            if st.form_submit_button("Autorizar Acceso"):
                if n and c:
                    db = get_connection(); db.execute("INSERT INTO usuarios (nombre, cedula, bloque) VALUES (?,?,?)", (n, c, b)); db.commit(); db.close()
                    st.success(f"✅ {n} autorizado para {b}"); st.rerun()
        
        df_u = pd.read_sql("SELECT id, nombre, cedula as Clave, bloque FROM usuarios", get_connection())
        st.dataframe(df_u, use_container_width=True, hide_index=True)

    elif menu == "GESTIÓN PROFESIONALES":
        st.header("👨‍⚕️ Registro de Médicos")
        with st.form("f_prof", clear_on_submit=True):
            col1, col2 = st.columns(2)
            n_p = col1.text_input("Nombre del Médico")
            c_p = col2.text_input("Cédula")
            if st.form_submit_button("Guardar Médico"):
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
        st.markdown("### 📝 REGISTRO DE INGRESOS")
        with st.container():
            c1, c2 = st.columns(2)
            f_f = c1.date_input("FECHA")
            f_p = c2.selectbox("FORMA DE PAGO", ["Efectivo", "Transferencia", "Pago Plux", "Deuna", "DataFast"])
            med = c1.selectbox("Médico/Especialista", ["Seleccione..."] + profes)
            vc = c2.number_input("Valor Consulta", value=0.0)
            pac = c1.text_input("Nombre del Paciente")
            vp = c2.number_input("Valor Procedimiento", value=0.0)
            ced = c1.text_input("Cédula")
            vi = c2.number_input("Valor Inyección", value=0.0)
            tel = c1.text_input("Teléfono")
            vce = c2.number_input("Valor Certificado", value=0.0)
            obs = st.text_area("Observaciones")
            total = vc + vp + vi + vce
            st.markdown(f"<div class='total-box'>💰 Total a cobrar: ${total:.2f}</div>", unsafe_allow_html=True)
            if st.button("GUARDAR REGISTRO"):
                if med != "Seleccione..." and pac:
                    db = get_connection(); db.execute("INSERT INTO consultas (fecha, forma_pago, medico, paciente, cedula, telefono, v_consulta, v_proc, v_inyec, v_cert, total, observaciones) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (str(f_f), f_p, med, pac, ced, tel, vc, vp, vi, vce, total, obs)); db.commit(); db.close(); st.success("✅ Guardado correctamente"); time.sleep(1); st.rerun()

    elif m == "AGENDAMIENTOS":
        st.markdown("### 🗓️ Agendamiento de Consultas")
        c1, c2 = st.columns(2)
        ag_f, ag_m = c1.date_input("Fecha"), c2.selectbox("Médico", ["Seleccione..."] + profes)
        if ag_m != "Seleccione...":
            horas = [f"{h:02d}:{m:02d}" for h in range(8, 18) for m in (0, 30)]
            for h in horas:
                db = get_connection(); res = db.execute("SELECT paciente, telefono FROM agendamientos WHERE fecha=? AND medico=? AND hora=?", (str(ag_f), ag_m, h)).fetchone(); db.close()
                col_h, col_p, col_t, col_b = st.columns([1, 3, 2, 1])
                col_h.write(f"🕒 {h}")
                if res:
                    col_p.info(f"{res[0]}"); col_t.write(res[1])
                    if col_b.button("🗑️", key=f"d_{h}"): 
                        db = get_connection(); db.execute("DELETE FROM agendamientos WHERE fecha=? AND medico=? AND hora=?", (str(ag_f), ag_m, h)); db.commit(); db.close(); st.rerun()
                else:
                    pn = col_p.text_input("Paciente", key=f"p_{h}", label_visibility="collapsed")
                    pt = col_t.text_input("Teléfono", key=f"t_{h}", label_visibility="collapsed")
                    if col_b.button("💾", key=f"s_{h}"):
                        if pn: db = get_connection(); db.execute("INSERT INTO agendamientos (fecha, medico, hora, paciente, telefono) VALUES (?,?,?,?,?)", (str(ag_f), ag_m, h, pn, pt)); db.commit(); db.close(); st.rerun()

    elif m == "VISUALIZAR/EDITAR CONSULTAS":
        st.markdown("### 🔎 VISUALIZACIÓN DE CONSULTAS")
        f_v = st.date_input("Fecha")
        df = pd.read_sql(f"SELECT * FROM consultas WHERE fecha='{str(f_v)}' ORDER BY medico", get_connection())
        if not df.empty:
            for med in df['medico'].unique():
                st.markdown(f"#### 🩺 {med}")
                sub = df[df['medico'] == med]
                for _, r in sub.iterrows():
                    with st.expander(f"👤 {r['paciente']} | Total: ${r['total']:.2f}"):
                        st.write(f"Pago: {r['forma_pago']} | Cédula: {r['cedula']}")
                        if st.button("🗑️ Eliminar", key=f"dc_{r['id']}"): 
                            db = get_connection(); db.execute("DELETE FROM consultas WHERE id=?", (r['id'],)); db.commit(); db.close(); st.rerun()
                st.markdown(f"**Total {med}: ${sub['total'].sum():.2f}**")

# --- 7. NAVEGACIÓN ---
if not st.session_state.autenticado:
    login()
else:
    # Sidebar con logo pequeño
    try: st.sidebar.image("logo leones.jpg", width=120)
    except: pass
    st.sidebar.markdown(f"👤 **{st.session_state.user_name}**")
    if st.sidebar.button("SALIR"):
        st.session_state.autenticado = False; st.rerun()

    if st.session_state.user_role == "ADMINISTRACION":
        bloque_administracion()
    elif st.session_state.user_role == "RECEPCION":
        bloque_recepcion()