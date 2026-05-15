import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import time

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Club de Leones Cumbayá-Ilaló", page_icon="🦁", layout="wide")

# --- 2. ESTILOS SOBRIOS (AZUL Y ORO) ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    [data-testid="stSidebar"] { background-color: #003366; }
    [data-testid="stSidebar"] * { color: white; }
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; background-color: #003366; color: white; border: 1px solid #d4af37; font-weight: bold; }
    .stButton>button:hover { background-color: #d4af37; color: #003366; }
    .card { background-color: white; padding: 25px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); border-top: 5px solid #d4af37; }
    h1, h2, h3 { color: #003366; font-family: 'Segoe UI', sans-serif; font-weight: bold; }
    .total-box { background-color: #f8f9fa; color: #003366; padding: 15px; border-radius: 10px; border: 1px solid #dee2e6; font-size: 22px; font-weight: bold; display: flex; align-items: center; }
    .stTable { border: none !important; }
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

# --- 5. LOGIN (ADN SOBRIO) ---
def login():
    c1, c2, c3 = st.columns([1, 0.8, 1])
    with c2:
        try: st.image("logo leones.jpg", use_container_width=True)
        except: pass
    st.markdown("<h1 style='text-align: center;'>CLUB DE LEONES CUMBAYA-ILALO</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #d4af37; font-size: 1.1em; letter-spacing: 2px;'>CENTRO MÉDICO</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("ACCESO AL SISTEMA")
        u_input = st.text_input("Nombre de Usuario", placeholder="Ej: CMLeones")
        p_input = st.text_input("Clave de Acceso", type="password", placeholder="Número de cédula")
        
        if st.button("INGRESAR AL SISTEMA"):
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
                else: st.error("Acceso denegado. Verifique sus credenciales.")
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
            b = c3.selectbox("Asignar bloque", ["RECEPCION", "CONTABILIDAD"])
            if st.form_submit_button("Guardar Usuario"):
                if n and c:
                    db = get_connection(); db.execute("INSERT INTO usuarios (nombre, cedula, bloque) VALUES (?,?,?)", (n, c, b)); db.commit(); db.close()
                    st.success(f"✅ Usuario {n} autorizado para {b}"); st.rerun()
        
        df_u = pd.read_sql("SELECT id, nombre, cedula as Clave, bloque FROM usuarios", get_connection())
        st.dataframe(df_u, use_container_width=True, hide_index=True)

    elif menu == "GESTIÓN PROFESIONALES":
        st.header("👨‍⚕️ Gestión de Profesionales")
        # Diseño exacto de FOTO 6
        with st.form("f_prof", clear_on_submit=True):
            col1, col2 = st.columns(2)
            n_p = col1.text_input("Nombre del Médico / Especialista")
            c_p = col2.text_input("Cédula del Profesional")
            if st.form_submit_button("Guardar Nuevo Profesional"):
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
            f_fecha = c1.date_input("FECHA")
            f_pago = c2.selectbox("FORMA DE PAGO", ["Efectivo", "Transferencia", "Pago Plux", "Deuna", "DataFast"])
            
            # Diseño de FOTO 1
            med = c1.selectbox("Médico/Especialista", ["Seleccione Médico..."] + profes)
            vc = c2.number_input("Valor Consulta", value=0.0, step=1.0)
            
            pac = c1.text_input("Nombre del Paciente")
            vp = c2.number_input("Valor Procedimiento", value=0.0, step=1.0)
            
            ced = c1.text_input("Cédula (Opcional)")
            vi = c2.number_input("Valor Inyección", value=0.0, step=1.0)
            
            tel = c1.text_input("Teléfono (Opcional)")
            vce = c2.number_input("Valor Certificado", value=0.0, step=1.0)
            
            obs = st.text_area("Observaciones")
            
            total = vc + vp + vi + vce
            st.markdown(f"<div class='total-box'>💰 Total a cobrar: ${total:.2f}</div>", unsafe_allow_html=True)
            
            if st.button("GUARDAR REGISTRO", type="primary"):
                if med != "Seleccione Médico..." and pac:
                    db = get_connection()
                    db.execute("INSERT INTO consultas (fecha, forma_pago, medico, paciente, cedula, telefono, v_consulta, v_proc, v_inyec, v_cert, total, observaciones) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (str(f_fecha), f_pago, med, pac, ced, tel, vc, vp, vi, vce, total, obs))
                    db.commit(); db.close()
                    st.success("✅ Registro almacenado correctamente"); time.sleep(1); st.rerun()

    elif m == "AGENDAMIENTOS":
        st.markdown("### 🗓️ Agendamiento de Consultas")
        # Diseño exacto de FOTO 2
        c1, c2 = st.columns(2)
        ag_f = c1.date_input("Fecha a Agendar")
        ag_m = c2.selectbox("Profesional Médico", ["Seleccione..."] + profes)
        
        if ag_m != "Seleccione...":
            st.markdown(f"#### Horarios Disponibles - {ag_f}")
            horas = [f"{h:02d}:{m:02d}" for h in range(8, 18) for m in (0, 30)]
            for h in horas:
                db = get_connection()
                res = db.execute("SELECT paciente, telefono FROM agendamientos WHERE fecha=? AND medico=? AND hora=?", (str(ag_f), ag_m, h)).fetchone()
                db.close()
                
                col_h, col_p, col_t, col_b = st.columns([1, 3, 2, 1])
                col_h.write(f"🕒 {h}")
                if res:
                    col_p.write(f"**{res[0]}**")
                    col_t.write(res[1])
                    if col_b.button("🗑️", key=f"del_{h}"):
                        db = get_connection(); db.execute("DELETE FROM agendamientos WHERE fecha=? AND medico=? AND hora=?", (str(ag_f), ag_m, h)); db.commit(); db.close(); st.rerun()
                else:
                    p_nom = col_p.text_input("Nombre...", key=f"p_{h}", label_visibility="collapsed")
                    p_tel = col_t.text_input("Teléfono...", key=f"t_{h}", label_visibility="collapsed")
                    if col_b.button("💾", key=f"s_{h}"):
                        if p_nom:
                            db = get_connection(); db.execute("INSERT INTO agendamientos (fecha, medico, hora, paciente, telefono) VALUES (?,?,?,?,?)", (str(ag_f), ag_m, h, p_nom, p_tel)); db.commit(); db.close(); st.rerun()

    elif m == "VISUALIZAR/EDITAR CONSULTAS":
        st.markdown("### 🔎 CONSULTAS")
        f_ver = st.date_input("Filtrar por fecha")
        df = pd.read_sql(f"SELECT * FROM consultas WHERE fecha='{str(f_ver)}'", get_connection())
        
        if not df.empty:
            for m in df['medico'].unique():
                st.markdown(f"#### 🩺 {m}")
                sub_df = df[df['medico'] == m]
                # Estructura visual de FOTO 3
                for _, r in sub_df.iterrows():
                    with st.expander(f"👤 {r['paciente']} | Pago: {r['forma_pago']} | Total: ${r['total']:.2f}"):
                        st.write(f"**Cédula:** {r['cedula']} | **Tel:** {r['telefono']}")
                        st.table(pd.DataFrame({
                            "Concepto": ["Consulta", "Proc.", "Inyec.", "Certif."],
                            "Valor": [f"${r['v_consulta']}", f"${r['v_proc']}", f"${r['v_inyec']}", f"${r['v_cert']}"]
                        }))
                        if st.button("🗑️ Eliminar Registro", key=f"del_c_{r['id']}"):
                            db = get_connection(); db.execute("DELETE FROM consultas WHERE id=?", (r['id'],)); db.commit(); db.close(); st.rerun()
                st.markdown(f"**Total {m}: ${sub_df['total'].sum():.2f}**")
        else: st.info("No hay consultas en la fecha seleccionada.")

# --- 7. NAVEGACIÓN PRINCIPAL ---
if not st.session_state.autenticado:
    login()
else:
    try: st.sidebar.image("logo leones.jpg", use_container_width=True)
    except: pass
    st.sidebar.markdown(f"👤 **{st.session_state.user_name}**")
    if st.sidebar.button("SALIR"):
        st.session_state.autenticado = False; st.rerun()

    if st.session_state.user_role == "ADMINISTRACION":
        bloque_administracion()
    elif st.session_state.user_role == "RECEPCION":
        bloque_recepcion()