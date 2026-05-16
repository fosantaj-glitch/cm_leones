import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import time

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Club de Leones Cumbayá-Ilaló", page_icon="🦁", layout="wide", initial_sidebar_state="collapsed")

# --- 2. ARQUITECTURA VISUAL ULTRA-COMPACTA Y DE ANCHO FIJO (UNA SOLA HOJA) ---
st.markdown(
    """
    <style>
    /* Forzar fondo blanco absoluto en toda la pantalla */
    .stApp, .block-container, [data-testid="stCanvasZone"], [data-testid="stWidgetFormView"] { 
        background-color: #ffffff !important; 
    }
    
    /* Eliminar márgenes y espacios muertos del tope de la página */
    .block-container { padding-top: 0.5rem; padding-bottom: 0rem; padding-left: 1rem; padding-right: 1rem; }
    
    /* Ocultar elementos decorativos por defecto de Streamlit que generan espacios fantasma */
    [data-testid="stHeader"] { display: none; }
    
    /* Barra Lateral Azul y Oro */
    [data-testid="stSidebar"] { background-color: #003366 !important; }
    [data-testid="stSidebar"] * { color: white !important; }

    /* Botón Estilo Profesional Leones */
    .stButton>button { 
        width: 100%; border-radius: 6px; height: 2.8em; 
        background-color: #003366; color: white; 
        border: 1px solid #d4af37; font-weight: bold; 
    }
    .stButton>button:hover { background-color: #d4af37; color: #003366; }

    /* CONTENEDOR MAESTRO DE ANCHO FIJO: Evita que el logo y los campos crezcan de lado a lado */
    .login-wrapper {
        max-width: 360px;
        margin: 0 auto; /* Centrado absoluto horizontal */
        padding-top: 10px;
        text-align: center;
    }

    /* Tarjeta Compacta Fina */
    .card-login { 
        background-color: #ffffff; 
        padding: 20px; 
        border-radius: 12px; 
        box-shadow: 0 4px 20px rgba(0,0,0,0.06); 
        border-top: 5px solid #d4af37;
        text-align: left; /* Alineación interna de los campos */
        margin-top: 10px;
    }

    /* Tipografía Fina y Ajustada */
    .main-title { color: #003366; font-family: 'Segoe UI', sans-serif; font-weight: bold; font-size: 1.6em; margin-bottom: 2px; text-align: center; }
    .subtitle { color: #d4af37; font-weight: bold; letter-spacing: 2px; font-size: 0.95em; margin-bottom: 12px; text-align: center; }

    /* Ajuste estricto de inputs */
    .stTextInput>div, .stSelectbox>div { margin-bottom: 2px; }
    .total-box { background-color: #f8f9fa; color: #003366; padding: 10px; border-radius: 8px; border: 1px solid #dee2e6; font-size: 1.1em; font-weight: bold; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True
)

# --- 3. BASE DE DATOS MÓDULO INTEGRADO ---
DB_NAME = 'centro_medico_club_leones.db'

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_connection(); c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, cedula TEXT, bloque TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS profesionales (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, cedula TEXT)')
    c.execute('''CREATE TABLE IF NOT EXISTS consultas 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, forma_pago TEXT, medico TEXT, 
                  paciente TEXT, cedula TEXT, telefono TEXT, v_consulta REAL, v_proc REAL, 
                  v_inyec REAL, v_cert REAL, total REAL, observaciones TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS agendamientos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, medico TEXT, hora TEXT, 
                  paciente TEXT, telefono TEXT)''')
    conn.commit(); conn.close()

init_db()

# --- 4. GESTIÓN DE ESTADO DE SESIÓN ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.user_role = None
    st.session_state.user_name = None

# --- 5. LOGIN VERTICAL CONTROLADO (ANCHO DE 360PX EXACTO) ---
def login():
    # Todo el bloque se encierra en el contenedor de ancho fijo para que no se desparrame por la pantalla
    st.markdown("<div class='login-wrapper'>", unsafe_allow_html=True)
    
    try: 
        # Al estar dentro de un bloque de 360px, la imagen se escala automáticamente de forma perfecta
        st.image("logo leones.jpg", use_container_width=True)
    except: 
        st.write("🦁")
            
    st.markdown("<div class='main-title'>CLUB DE LEONES CUMBAYA-ILALO</div>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>SISTEMA MÉDICO INTEGRAL</p>", unsafe_allow_html=True)
    
    # Tarjeta con los campos estilizados y finos
    st.markdown("<div class='card-login'>", unsafe_allow_html=True)
    
    b_destino = st.selectbox("Elija el bloque al que desea ingresar", ["RECEPCION", "ADMINISTRACION", "MEDICOS", "CONTABILIDAD"])
    u_nombre = st.text_input("USUARIO")
    p_clave = st.text_input("CLAVE", type="password")
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("INGRESAR AL SISTEMA"):
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
                st.error("⚠️ Datos incorrectos.")
                
    st.markdown("</div>", unsafe_allow_html=True) # Cierre card-login
    st.markdown("</div>", unsafe_allow_html=True) # Cierre login-wrapper

# --- 6. BLOQUE ADMINISTRACIÓN ---
def bloque_administracion():
    st.title("⚙️ ADMINISTRACIÓN GENERAL")
    menu = st.sidebar.selectbox("MENÚ", ["GESTIÓN DE PERMISOS", "GESTIÓN PROFESIONALES", "BASE DE DATOS PACIENTES", "LIQUIDACIÓN MENSUAL"])

    if menu == "GESTIÓN DE PERMISOS":
        st.header("🛂 Control de Permisos")
        with st.form("f_per", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            n, c = c1.text_input("Nombre completo"), c2.text_input("Cédula (clave)")
            b = c3.selectbox("Asignar bloque", ["RECEPCION", "CONTABILIDAD", "MEDICOS"])
            if st.form_submit_button("Autorizar Acceso"):
                if n and c:
                    db = get_connection(); db.execute("INSERT INTO usuarios (nombre, cedula, bloque) VALUES (?,?,?)", (n, c, b)); db.commit(); db.close()
                    st.success(f"✅ Guardado"); st.rerun()
        df_u = pd.read_sql("SELECT id, nombre, cedula as Clave, bloque as Sección FROM usuarios", get_connection())
        st.dataframe(df_u, use_container_width=True, hide_index=True)

    elif menu == "GESTIÓN PROFESIONALES":
        st.header("👨‍⚕️ Control de Profesionales")
        df_p = pd.read_sql("SELECT * FROM profesionales", get_connection())
        st.table(df_p[['id', 'nombre']].rename(columns={'id': 'N°', 'nombre': 'Profesional'}))
        
        with st.container():
            col1, col2, col3 = st.columns(3)
            with col1:
                with st.form("add_doc", clear_on_submit=True):
                    st.write("**Agregar Nuevo Médico**")
                    n_doc = st.text_input("Nombre")
                    c_doc = st.text_input("Cédula")
                    if st.form_submit_button("Guardar"):
                        if n_doc:
                            db = get_connection(); db.execute("INSERT INTO profesionales (nombre, cedula) VALUES (?,?)", (n_doc, c_doc)); db.commit(); db.close(); st.rerun()
            with col2:
                with st.form("edit_doc"):
                    st.write("**Médico a corregir**")
                    sel_id = st.selectbox("Elegir ID", ["Seleccione..."] + list(df_p['id']))
                    n_curr = st.text_input("Escriba el nombre correcto")
                    if st.form_submit_button("Actualizar"):
                        if sel_id != "Seleccione..." and n_curr:
                            db = get_connection(); db.execute("UPDATE profesionales SET nombre=? WHERE id=?", (n_curr, sel_id)); db.commit(); db.close(); st.rerun()
            with col3:
                with st.form("del_doc"):
                    st.write("**Médico a eliminar**")
                    del_id = st.selectbox("Elegir ID para borrar", ["Seleccione..."] + list(df_p['id']))
                    if st.form_submit_button("Eliminar"):
                        if del_id != "Seleccione...":
                            db = get_connection(); db.execute("DELETE FROM profesionales WHERE id=?", (del_id,)); db.commit(); db.close(); st.rerun()

# --- 7. BLOQUE RECEPCIÓN ---
def bloque_recepcion():
    st.title("🛎️ RECEPCIÓN")
    m = st.sidebar.radio("MENÚ", ["CAJA DIARIA", "AGENDAMIENTOS", "VISUALIZAR/EDITAR CONSULTAS"])
    conn = get_connection(); profes = [p[0] for p in conn.execute("SELECT nombre FROM profesionales").fetchall()]; conn.close()

    if m == "CAJA DIARIA":
        st.markdown("### 📝 REGISTRO DE INGRESOS")
        c1, c2 = st.columns(2)
        f_f, f_p = c1.date_input("FECHA"), c2.selectbox("FORMA DE PAGO", ["Efectivo", "Transferencia", "Pago Plux", "Deuna", "DataFast"])
        med = c1.selectbox("Médico/Especialista", ["Seleccione Médico..."] + profes)
        vc = c2.number_input("Valor Consulta", value=0.0)
        pac = c1.text_input("Nombre del Paciente")
        vp = c2.number_input("Valor Procedimiento", value=0.0)
        ced = c1.text_input("Cédula (Opcional)")
        vi = c2.number_input("Valor Inyección", value=0.0)
        tel = c1.text_input("Teléfono (Opcional)")
        vce = c2.number_input("Valor Certificado", value=0.0)
        obs = st.text_area("Observaciones")
        total = vc + vp + vi + vce
        st.markdown(f"<div class='total-box'>💰 Total a cobrar: ${total:.2f}</div>", unsafe_allow_html=True)
        if st.button("GUARDAR REGISTRO", type="primary"):
            if med != "Seleccione Médico..." and pac:
                db = get_connection(); db.execute("INSERT INTO consultas (fecha, forma_pago, medico, paciente, cedula, telefono, v_consulta, v_proc, v_inyec, v_cert, total, observaciones) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (str(f_f), f_p, med, pac, ced, tel, vc, vp, vi, vce, total, obs)); db.commit(); db.close(); st.success("✅ Guardado"); time.sleep(1); st.rerun()

    elif m == "AGENDAMIENTOS":
        st.markdown("### 🗓️ Agendamiento de Consultas")
        c1, c2 = st.columns(2)
        ag_f, ag_m = c1.date_input("Fecha a Agendar"), c2.selectbox("Profesional Médico", ["Seleccione..."] + profes)
        if ag_m != "Seleccione...":
            st.markdown(f"#### Horarios Disponibles - {ag_f}")
            horas = [f"{h:02d}:{m:02d}" for h in range(8, 18) for m in (0, 30)]
            for h in horas:
                db = get_connection(); res = db.execute("SELECT paciente, telefono FROM agendamientos WHERE fecha=? AND medico=? AND hora=?", (str(ag_f), ag_m, h)).fetchone(); db.close()
                col_h, col_p, col_t, col_b = st.columns([1, 3, 2, 1])
                col_h.write(f"🕒 {h}")
                if res:
                    col_p.info(f"{res[0]}"); col_t.write(res[1])
                    if col_b.button("Borrar", key=f"d_{h}"): 
                        db = get_connection(); db.execute("DELETE FROM agendamientos WHERE fecha=? AND medico=? AND hora=?", (str(ag_f), ag_m, h)); db.commit(); db.close(); st.rerun()
                else:
                    pn = col_p.text_input("Paciente", key=f"p_{h}", label_visibility="collapsed", placeholder="Nombre...")
                    pt = col_t.text_input("Teléfono", key=f"t_{h}", label_visibility="collapsed", placeholder="Teléfono...")
                    if col_b.button("💾", key=f"s_{h}"):
                        if pn: db = get_connection(); db.execute("INSERT INTO agendamientos (fecha, medico, hora, paciente, telefono) VALUES (?,?,?,?,?)", (str(ag_f), ag_m, h, pn, pt)); db.commit(); db.close(); st.rerun()

    elif m == "VISUALIZAR/EDITAR CONSULTAS":
        st.markdown("### 🔎 CONSULTAS")
        f_v = st.date_input("Filtrar por fecha")
        df = pd.read_sql(f"SELECT * FROM consultas WHERE fecha='{str(f_v)}' ORDER BY medico", get_connection())
        if not df.empty:
            for med in df['medico'].unique():
                st.markdown(f"#### 🩺 {med}")
                sub = df[df['medico'] == med]
                for _, r in sub.iterrows():
                    with st.expander(f"👤 {r['paciente']} | Total: ${r['total']:.2f}"):
                        st.write(f"Forma de Pago: {r['forma_pago']} | Cédula: {r['cedula']}")
                        st.table(pd.DataFrame({"Concepto": ["Consulta", "Proc.", "Inyec.", "Certif."], "Valor": [f"${r['v_consulta']}", f"${r['v_proc']}", f"${r['v_inyec']}", f"${r['v_cert']}"]}))
                        
                        with st.form(f"edit_form_{r['id']}"):
                            st.write("*Formulario de Modificación de Datos*")
                            new_p = st.selectbox("Nueva Forma de Pago", ["Efectivo", "Transferencia", "Pago Plux", "Deuna", "DataFast"], index=["Efectivo", "Transferencia", "Pago Plux", "Deuna", "DataFast"].index(r['forma_pago']))
                            new_vc = st.number_input("Consulta", value=r['v_consulta'])
                            new_vp = st.number_input("Procedimiento", value=r['v_proc'])
                            new_vi = st.number_input("Inyección", value=r['v_inyec'])
                            new_vce = st.number_input("Certificado", value=r['v_cert'])
                            new_obs = st.text_area("Observaciones", value=r['observaciones'])
                            new_tot = new_vc + new_vp + new_vi + new_vce
                            
                            c_b1, c_b2 = st.columns(2)
                            if c_b1.form_submit_button("ACTUALIZAR DATOS"):
                                db = get_connection(); db.execute("UPDATE consultas SET forma_pago=?, v_consulta=?, v_proc=?, v_inyec=?, v_cert=?, total=?, observaciones=? WHERE id=?", (new_p, new_vc, new_vp, new_vi, new_vce, new_tot, new_obs, r['id'])); db.commit(); db.close(); st.success("Actualizado"); time.sleep(0.5); st.rerun()
                            if c_b2