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
    h1, h2, h3 { color: #003366; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    .total-box { background-color: #003366; color: #d4af37; padding: 20px; border-radius: 10px; text-align: center; font-size: 24px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. BASE DE DATOS ---
def get_connection():
    return sqlite3.connect('club_leones_centro_medico.db', check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Usuarios/Permisos
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, cedula TEXT, bloque TEXT)''')
    # Profesionales
    c.execute('''CREATE TABLE IF NOT EXISTS profesionales 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, cedula TEXT)''')
    # Caja Diaria
    c.execute('''CREATE TABLE IF NOT EXISTS consultas 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, forma_pago TEXT, medico TEXT, 
                  paciente TEXT, cedula TEXT, telefono TEXT, v_consulta REAL, v_proc REAL, 
                  v_inyec REAL, v_cert REAL, total REAL, observaciones TEXT)''')
    # Agendamientos
    c.execute('''CREATE TABLE IF NOT EXISTS agendamientos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, medico TEXT, hora TEXT, 
                  paciente TEXT, telefono TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- 4. GESTIÓN DE ESTADO (ADN ANTERIOR) ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.user_role = None
    st.session_state.user_name = None

# --- 5. LOGIN ---
def login():
    st.markdown("<h1 style='text-align: center;'>🦁 CLUB DE LEONES CUMBAYA-ILALO</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #d4af37; font-size: 1.2em;'>Centro Médico de Especialidades</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("🔑 ACCESO AL SISTEMA")
        u_input = st.text_input("Usuario")
        p_input = st.text_input("Clave (Número de Cédula)", type="password")
        
        if st.button("INGRESAR"):
            # Validación Maestro (Solicitado por el usuario)
            if u_input == "CMLeones" and p_input == "2468":
                st.session_state.autenticado = True
                st.session_state.user_role = "ADMINISTRACION"
                st.session_state.user_name = "Administrador Maestro"
                st.rerun()
            else:
                # Validación por Base de Datos de Permisos
                conn = get_connection()
                res = conn.execute("SELECT nombre, bloque FROM usuarios WHERE nombre=? AND cedula=?", (u_input, p_input)).fetchone()
                conn.close()
                if res:
                    st.session_state.autenticado = True
                    st.session_state.user_name = res[0]
                    st.session_state.user_role = res[1]
                    st.rerun()
                else:
                    st.error("Credenciales no autorizadas")
        st.markdown("</div>", unsafe_allow_html=True)

# --- 6. BLOQUE ADMINISTRACIÓN ---
def bloque_administracion():
    st.title("⚙️ ADMINISTRACIÓN GENERAL")
    menu = st.sidebar.selectbox("MENÚ ADMIN", ["GESTIÓN DE PERMISOS", "GESTIÓN PROFESIONALES", "BASE DE DATOS PACIENTES", "LIQUIDACIÓN MENSUAL"])

    if menu == "GESTIÓN DE PERMISOS":
        st.header("🛂 Control de Permisos")
        with st.form("f_permisos", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            nom = c1.text_input("Nombre del Usuario")
            ced = c2.text_input("Cédula (Clave)")
            bloq = c3.selectbox("Asignar a Bloque", ["RECEPCION", "CONTABILIDAD"])
            if st.form_submit_button("Guardar Autorización"):
                if nom and ced:
                    conn = get_connection()
                    conn.execute("INSERT INTO usuarios (nombre, cedula, bloque) VALUES (?,?,?)", (nom, ced, bloq))
                    conn.commit(); conn.close()
                    st.success(f"Permiso otorgado a {nom}")
                    st.rerun()

        st.subheader("Usuarios Autorizados")
        df_u = pd.read_sql("SELECT id, nombre, cedula as Clave, bloque as Sección FROM usuarios", get_connection())
        st.dataframe(df_u, use_container_width=True, hide_index=True)
        
        id_del = st.number_input("ID a eliminar", step=1, min_value=0)
        if st.button("Eliminar Usuario"):
            conn = get_connection()
            conn.execute("DELETE FROM usuarios WHERE id=?", (id_del,))
            conn.commit(); conn.close(); st.rerun()

    elif menu == "GESTIÓN PROFESIONALES":
        st.header("👨‍⚕️ Gestión de Especialistas")
        with st.form("f_prof", clear_on_submit=True):
            c1, c2 = st.columns(2)
            n_p = c1.text_input("Nombre del Profesional")
            c_p = c2.text_input("Cédula Profesional")
            if st.form_submit_button("Registrar Profesional"):
                if n_p:
                    conn = get_connection()
                    conn.execute("INSERT INTO profesionales (nombre, cedula) VALUES (?,?)", (n_p, c_p))
                    conn.commit(); conn.close(); st.rerun()

        df_p = pd.read_sql("SELECT * FROM profesionales", get_connection())
        st.table(df_p)
        
        st.subheader("Editar/Borrar Profesional")
        c1, c2, c3 = st.columns([1,2,1])
        id_ed = c1.selectbox("ID Prof.", ["-"] + list(df_p['id']))
        n_new = c2.text_input("Nuevo Nombre")
        if c3.button("Actualizar"):
            if id_ed != "-":
                conn = get_connection()
                conn.execute("UPDATE profesionales SET nombre=? WHERE id=?", (n_new, id_ed))
                conn.commit(); conn.close(); st.rerun()
        if st.button("Borrar Profesional Seleccionado"):
            if id_ed != "-":
                conn = get_connection(); conn.execute("DELETE FROM profesionales WHERE id=?", (id_ed,))
                conn.commit(); conn.close(); st.rerun()

# --- 7. BLOQUE RECEPCIÓN ---
def bloque_recepcion():
    st.title("🛎️ BLOQUE DE RECEPCIÓN")
    menu = st.sidebar.radio("MENÚ RECEPCIÓN", ["CAJA DIARIA", "AGENDAMIENTOS", "VISUALIZAR/EDITAR CONSULTAS"])
    
    conn = get_connection()
    profesionales = [p[0] for p in conn.execute("SELECT nombre FROM profesionales").fetchall()]
    conn.close()

    if menu == "CAJA DIARIA":
        st.header("📝 Registro de Ingresos")
        with st.form("caja_form", clear_on_submit=True):
            col_l, col_r = st.columns(2)
            fecha = col_l.date_input("FECHA", datetime.now())
            fpago = col_r.selectbox("FORMA DE PAGO", ["Efectivo", "Transferencia", "Pago Plux", "Deuna", "DataFast"])
            
            medico = col_l.selectbox("MEDICO/ESPECIALISTA", ["Seleccione..."] + profesionales)
            v_cons = col_r.number_input("VALOR CONSULTA", min_value=0.0, step=0.01, format="%.2f")
            
            paciente = col_l.text_input("NOMBRE DEL PACIENTE")
            v_proc = col_r.number_input("VALOR PROCEDIMIENTO", min_value=0.0, step=0.01, format="%.2f")
            
            cedula = col_l.text_input("CEDULA DE IDENTIDAD")
            v_iny = col_r.number_input("VALOR INYECCION", min_value=0.0, step=0.01, format="%.2f")
            
            tel = col_l.text_input("NUMERO DE TELEFONO")
            v_cert = col_r.number_input("VALOR CERTIFICADO", min_value=0.0, step=0.01, format="%.2f")
            
            obs = st.text_area("OBSERVACIONES")
            
            total = v_cons + v_proc + v_iny + v_cert
            st.markdown(f"<div class='total-box'>TOTAL A COBRAR: ${total:.2f}</div>", unsafe_allow_html=True)
            
            if st.form_submit_button("GUARDAR REGISTRO"):
                if medico != "Seleccione..." and paciente:
                    conn = get_connection()
                    conn.execute("""INSERT INTO consultas 
                        (fecha, forma_pago, medico, paciente, cedula, telefono, v_consulta, v_proc, v_inyec, v_cert, total, observaciones) 
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""", 
                        (str(fecha), fpago, medico, paciente, cedula, tel, v_cons, v_proc, v_iny, v_cert, total, obs))
                    conn.commit(); conn.close()
                    st.success("¡Registro grabado exitosamente!")
                else:
                    st.error("Campos Médico y Paciente son obligatorios.")

    elif menu == "AGENDAMIENTOS":
        st.header("🗓️ Agendamiento de Consultas")
        c1, c2 = st.columns(2)
        f_ag = c1.date_input("Fecha", datetime.now())
        p_ag = c2.selectbox("Profesional", ["Seleccione..."] + profesionales)
        
        if p_ag != "Seleccione...":
            st.subheader(f"Horarios Disponibles: {p_ag}")
            horas = [f"{h:02d}:{m:02d}" for h in range(8, 18) for m in (0, 30)]
            for h in horas:
                # ADN: Verificar si ya existe el agendamiento para no duplicar
                conn = get_connection()
                existente = conn.execute("SELECT paciente, telefono FROM agendamientos WHERE fecha=? AND medico=? AND hora=?", (str(f_ag), p_ag, h)).fetchone()
                conn.close()
                
                colh, colp, colt, colb = st.columns([1, 3, 2, 1])
                colh.write(f"**{h}**")
                if existente:
                    colp.info(f"👤 {existente[0]}")
                    colt.write(existente[1])
                    if colb.button("Borrar", key=f"del_{h}"):
                        c = get_connection(); c.execute("DELETE FROM agendamientos WHERE fecha=? AND medico=? AND hora=?", (str(f_ag), p_ag, h))
                        c.commit(); c.close(); st.rerun()
                else:
                    nom_p = colp.text_input("Paciente", key=f"n_{h}", label_visibility="collapsed")
                    tel_p = colt.text_input("Teléfono", key=f"t_{h}", label_visibility="collapsed")
                    if colb.button("💾", key=f"s_{h}"):
                        if nom_p:
                            c = get_connection()
                            c.execute("INSERT INTO agendamientos (fecha, medico, hora, paciente, telefono) VALUES (?,?,?,?,?)", (str(f_ag), p_ag, h, nom_p, tel_p))
                            c.commit(); c.close(); st.rerun()

    elif menu == "VISUALIZAR/EDITAR CONSULTAS":
        st.header("🔍 Consultas")
        f_ver = st.date_input("Elija la fecha a visualizar", datetime.now())
        df = pd.read_sql(f"SELECT * FROM consultas WHERE fecha='{str(f_ver)}' ORDER BY medico", get_connection())
        
        if not df.empty:
            for m in df['medico'].unique():
                st.markdown(f"<h3 style='background:#003366; color:white; padding:10px; border-radius:5px;'>Médico: {m}</h3>", unsafe_allow_html=True)
                sub_df = df[df['medico'] == m]
                for _, r in sub_df.iterrows():
                    with st.expander(f"Paciente: {r['paciente']} | Total: ${r['total']:.2f}"):
                        st.write(f"**Pago:** {r['forma_pago']} | **Cédula:** {r['cedula']}")
                        st.write(f"**Desglose:** Consulta: ${r['v_consulta']} | Proc: ${r['v_proc']} | Iny: ${r['v_inyec']} | Cert: ${r['v_cert']}")
                        if st.button("🗑️ Eliminar Registro", key=f"del_c_{r['id']}"):
                            cx = get_connection(); cx.execute("DELETE FROM consultas WHERE id=?", (r['id'],))
                            cx.commit(); cx.close(); st.rerun()
                st.write(f"**Subtotal {m}:** ${sub_df['total'].sum():.2f}")
        else:
            st.info("No hay registros para esta fecha.")

# --- 8. LÓGICA DE NAVEGACIÓN ---
if not st.session_state.autenticado:
    login()
else:
    # Sidebar común
    st.sidebar.markdown(f"### 👤 {st.session_state.user_name}")
    st.sidebar.write(f"**Sección:** {st.session_state.user_role}")
    if st.sidebar.button("SALIR"):
        st.session_state.autenticado = False
        st.rerun()

    if st.session_state.user_role == "ADMINISTRACION":
        bloque_administracion()
    elif st.session_state.user_role == "RECEPCION":
        bloque_recepcion()
    elif st.session_state.user_role == "CONTABILIDAD":
        st.title("💰 CONTABILIDAD")
        st.info("Bloque en construcción - Siguiente etapa.")