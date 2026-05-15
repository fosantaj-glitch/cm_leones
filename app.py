import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import time

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Club de Leones Cumbayá-Ilaló", page_icon="🦁", layout="wide")

# --- ESTILOS SOBRIOS Y ELEGANTES (AZUL Y ORO) ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #003366; color: white; border: none; }
    .stButton>button:hover { background-color: #004080; border: 1px solid #d4af37; }
    .title-text { color: #003366; font-family: 'Helvetica Neue', sans-serif; font-weight: bold; }
    .gold-text { color: #d4af37; font-weight: bold; }
    .card { background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; border-left: 5px solid #d4af37; }
    div[data-testid="stMetricValue"] { color: #003366; font-size: 1.8rem; }
    </style>
    """, unsafe_allow_html=True)

# --- BASE DE DATOS ---
def get_connection():
    conn = sqlite3.connect('centro_medico_leones.db', check_same_thread=False)
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Tabla de Permisos (Usuarios del sistema)
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, cedula TEXT, bloque TEXT)''')
    # Tabla de Profesionales (Médicos)
    c.execute('''CREATE TABLE IF NOT EXISTS profesionales 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, cedula TEXT)''')
    # Tabla de Consultas/Caja
    c.execute('''CREATE TABLE IF NOT EXISTS consultas 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, forma_pago TEXT, medico TEXT, 
                  paciente TEXT, cedula TEXT, telefono TEXT, v_consulta REAL, v_proc REAL, 
                  v_inyec REAL, v_cert REAL, total REAL, observaciones TEXT)''')
    # Tabla de Agendamientos
    c.execute('''CREATE TABLE IF NOT EXISTS agendamientos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, medico TEXT, hora TEXT, 
                  paciente TEXT, telefono TEXT)''')
    
    # Usuario admin por defecto si no existe
    c.execute("SELECT * FROM usuarios WHERE cedula='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO usuarios (nombre, cedula, bloque) VALUES (?,?,?)", 
                  ('Administrador Maestro', 'admin', 'ADMINISTRACION'))
    conn.commit()
    conn.close()

init_db()

# --- LÓGICA DE LOGIN ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.user_role = None
    st.session_state.user_name = None

def login():
    st.markdown("<h1 style='text-align: center; color: #003366;'>🦁 CLUB DE LEONES CUMBAYA-ILALO</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #d4af37;'>Sistema de Gestión Médica</h3>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.container():
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.subheader("ACCESO AL SISTEMA")
            user_input = st.text_input("Usuario (Nombre registrado)")
            pass_input = st.text_input("Clave (Cédula)", type="password")
            
            if st.button("INGRESAR"):
                conn = get_connection()
                query = "SELECT nombre, bloque FROM usuarios WHERE nombre = ? AND cedula = ?"
                res = conn.execute(query, (user_input, pass_input)).fetchone()
                conn.close()
                
                if res:
                    st.session_state.autenticado = True
                    st.session_state.user_name = res[0]
                    st.session_state.user_role = res[1]
                    st.success(f"Bienvenido {res[0]}")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Usuario o Clave incorrectos")
            st.markdown("</div>", unsafe_allow_html=True)

# --- BLOQUE ADMINISTRACIÓN ---
def bloque_administracion():
    st.title("⚙️ PANEL DE ADMINISTRACIÓN")
    menu = st.sidebar.radio("Opciones", ["GESTIÓN DE PERMISOS", "GESTIÓN PROFESIONALES", "BASE DE DATOS PACIENTES", "CONTABILIDAD", "LIQUIDACIÓN MENSUAL"])
    
    if menu == "GESTIÓN DE PERMISOS":
        st.subheader("Control de Acceso (Usuarios Recepción/Contabilidad)")
        with st.form("form_permisos", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            n_nombre = col1.text_input("Nombre Completo")
            n_cedula = col2.text_input("Cédula (Será la clave)")
            n_bloque = col3.selectbox("Bloque Autorizado", ["RECEPCION", "CONTABILIDAD"])
            if st.form_submit_button("Guardar Permiso"):
                conn = get_connection()
                conn.execute("INSERT INTO usuarios (nombre, cedula, bloque) VALUES (?,?,?)", (n_nombre, n_cedula, n_bloque))
                conn.commit()
                st.success("Usuario registrado")
        
        # Lista de Usuarios
        df_u = pd.read_sql("SELECT id, nombre, cedula, bloque FROM usuarios WHERE cedula != 'admin'", get_connection())
        st.dataframe(df_u, use_container_width=True)
        
        eliminar = st.selectbox("Eliminar Usuario por ID", ["Seleccione..."] + list(df_u['id']))
        if st.button("Eliminar Seleccionado"):
            if eliminar != "Seleccione...":
                conn = get_connection()
                conn.execute("DELETE FROM usuarios WHERE id=?", (eliminar,))
                conn.commit()
                st.rerun()

    elif menu == "GESTIÓN PROFESIONALES":
        st.subheader("Gestión de Médicos/Especialistas")
        with st.form("form_medicos", clear_on_submit=True):
            col1, col2 = st.columns(2)
            m_nombre = col1.text_input("Nombre del Médico")
            m_cedula = col2.text_input("Cédula")
            if st.form_submit_button("Guardar Médico"):
                conn = get_connection()
                conn.execute("INSERT INTO profesionales (nombre, cedula) VALUES (?,?)", (m_nombre, m_cedula))
                conn.commit()
                st.success("Médico registrado")
        
        df_m = pd.read_sql("SELECT * FROM profesionales", get_connection())
        st.table(df_m)
        
        # Corregir/Eliminar
        col_ed1, col_ed2 = st.columns(2)
        with col_ed1:
            m_id = st.selectbox("Médico a corregir", ["Seleccione..."] + list(df_m['id']))
            nuevo_n = st.text_input("Escriba el nombre correcto")
            if st.button("Actualizar"):
                if m_id != "Seleccione...":
                    conn = get_connection()
                    conn.execute("UPDATE profesionales SET nombre=? WHERE id=?", (nuevo_n, m_id))
                    conn.commit()
                    st.rerun()
        with col_ed2:
            m_id_del = st.selectbox("Médico a eliminar", ["Seleccione..."] + list(df_m['id']))
            if st.button("Eliminar"):
                if m_id_del != "Seleccione...":
                    conn = get_connection()
                    conn.execute("DELETE FROM profesionales WHERE id=?", (m_id_del,))
                    conn.commit()
                    st.rerun()

    elif menu == "CONTABILIDAD":
        st.warning("Sección en desarrollo (Próxima etapa)")

# --- BLOQUE RECEPCIÓN ---
def bloque_recepcion():
    st.title("🛎️ RECEPCIÓN")
    menu = st.sidebar.radio("Menú", ["CAJA DIARIA", "AGENDAMIENTOS", "VISUALIZAR/EDITAR CONSULTAS"])
    
    # Obtener lista de médicos actualizada
    conn = get_connection()
    medicos = [m[0] for m in conn.execute("SELECT nombre FROM profesionales").fetchall()]
    conn.close()
    
    if menu == "CAJA DIARIA":
        st.markdown("<h2 class='title-text'>REGISTRO DE INGRESOS</h2>", unsafe_allow_html=True)
        with st.form("caja_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            f_fecha = c1.date_input("FECHA", datetime.now())
            f_pago = c2.selectbox("FORMA DE PAGO", ["Efectivo", "Transferencia", "Pago Plux", "Deuna", "DataFast"])
            
            c3, c4 = st.columns(2)
            f_medico = c3.selectbox("MEDICO/ESPECIALISTA", ["Seleccione Médico..."] + medicos)
            f_v_cons = c4.number_input("VALOR CONSULTA", min_value=0.0, step=0.5, format="%.2f")
            
            c5, c6 = st.columns(2)
            f_paciente = c5.text_input("NOMBRE DEL PACIENTE")
            f_v_proc = c6.number_input("VALOR PROCEDIMIENTO", min_value=0.0, step=0.5, format="%.2f")
            
            c7, c8 = st.columns(2)
            f_cedula = c7.text_input("CÉDULA DE IDENTIDAD (Opcional)")
            f_v_iny = c8.number_input("VALOR INYECCIÓN", min_value=0.0, step=0.5, format="%.2f")
            
            c9, c10 = st.columns(2)
            f_tel = c9.text_input("NÚMERO DE TELÉFONO")
            f_v_cert = c10.number_input("VALOR CERTIFICADO", min_value=0.0, step=0.5, format="%.2f")
            
            f_obs = st.text_area("OBSERVACIONES")
            
            total = f_v_cons + f_v_proc + f_v_iny + f_v_cert
            st.markdown(f"<h2 style='color: #003366;'>💰 TOTAL A COBRAR: ${total:.2f}</h2>", unsafe_allow_html=True)
            
            if st.form_submit_button("GUARDAR REGISTRO"):
                if f_medico == "Seleccione Médico..." or not f_paciente:
                    st.error("Por favor complete Médico y Paciente")
                else:
                    conn = get_connection()
                    conn.execute("""INSERT INTO consultas 
                        (fecha, forma_pago, medico, paciente, cedula, telefono, v_consulta, v_proc, v_inyec, v_cert, total, observaciones) 
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""", 
                        (str(f_fecha), f_pago, f_medico, f_paciente, f_cedula, f_tel, f_v_cons, f_v_proc, f_v_iny, f_v_cert, total, f_obs))
                    conn.commit()
                    conn.close()
                    st.success("Registro Guardado con éxito")

    elif menu == "AGENDAMIENTOS":
        st.subheader("🗓️ AGENDAMIENTO DE CONSULTAS")
        c1, c2 = st.columns(2)
        ag_fecha = c1.date_input("Fecha a Agendar", datetime.now())
        ag_medico = c2.selectbox("Profesional Médico", ["Seleccione..."] + medicos)
        
        if ag_medico != "Seleccione...":
            st.markdown(f"### Horarios Disponibles - {ag_fecha}")
            horas = ["08:00", "08:30", "09:00", "09:30", "10:00", "10:30", "11:00", "11:30", 
                     "12:00", "12:30", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30"]
            
            conn = get_connection()
            for h in horas:
                # Verificar si ya existe agendamiento
                existente = conn.execute("SELECT paciente, telefono FROM agendamientos WHERE fecha=? AND medico=? AND hora=?", 
                                         (str(ag_fecha), ag_medico, h)).fetchone()
                
                with st.container():
                    colh, colp, colt, colb = st.columns([1, 3, 2, 1])
                    colh.markdown(f"**{h}**")
                    if existente:
                        colp.text(f"✅ {existente[0]}")
                        colt.text(existente[1])
                        if colb.button("Borrar", key=f"del_{h}"):
                            conn.execute("DELETE FROM agendamientos WHERE fecha=? AND medico=? AND hora=?", (str(ag_fecha), ag_medico, h))
                            conn.commit()
                            st.rerun()
                    else:
                        p_nom = colp.text_input("Paciente", key=f"p_{h}", label_visibility="collapsed", placeholder="Nombre Paciente")
                        p_tel = colt.text_input("Teléfono", key=f"t_{h}", label_visibility="collapsed", placeholder="Teléfono")
                        if colb.button("💾", key=f"btn_{h}"):
                            if p_nom:
                                conn.execute("INSERT INTO agendamientos (fecha, medico, hora, paciente, telefono) VALUES (?,?,?,?,?)",
                                             (str(ag_fecha), ag_medico, h, p_nom, p_tel))
                                conn.commit()
                                st.rerun()
            conn.close()

    elif menu == "VISUALIZAR/EDITAR CONSULTAS":
        st.subheader("🔎 CONSULTAS REGISTRADAS")
        filtro_fecha = st.date_input("Filtrar por fecha", datetime.now())
        
        df_c = pd.read_sql(f"SELECT * FROM consultas WHERE fecha='{filtro_fecha}' ORDER BY medico", get_connection())
        
        if not df_c.empty:
            for med in df_c['medico'].unique():
                st.markdown(f"<div style='background-color: #003366; color: white; padding: 10px; border-radius: 5px;'>🩺 MÉDICO: {med}</div>", unsafe_allow_html=True)
                df_med = df_c[df_c['medico'] == med]
                
                for _, row in df_med.iterrows():
                    with st.expander(f"👤 Paciente: {row['paciente']} | Total: ${row['total']:.2f}"):
                        st.write(f"**Forma de Pago:** {row['forma_pago']}")
                        st.write(f"**Consulta:** ${row['v_consulta']} | **Proc:** ${row['v_proc']} | **Iny:** ${row['v_inyec']} | **Cert:** ${row['v_cert']}")
                        st.write(f"**Obs:** {row['observaciones']}")
                        if st.button("📝 Editar/Eliminar", key=f"edit_{row['id']}"):
                            st.session_state.edit_id = row['id']
                            st.info("Función de edición habilitada en Caja Diaria (use el ID)")
                
                total_medico = df_med['total'].sum()
                st.markdown(f"<p style='text-align: right; font-weight: bold;'>Subtotal {med}: ${total_medico:.2f}</p>", unsafe_allow_html=True)
        else:
            st.info("No hay consultas en esta fecha.")

# --- LÓGICA DE NAVEGACIÓN ---
if not st.session_state.autenticado:
    login()
else:
    st.sidebar.image("https://www.lionsclubs.org/themes/custom/lci/logo.svg", width=100) # Logo genérico Leones
    st.sidebar.markdown(f"**Usuario:** {st.session_state.user_name}")
    st.sidebar.markdown(f"**Rol:** {st.session_state.user_role}")
    
    if st.sidebar.button("SALIR"):
        st.session_state.autenticado = False
        st.rerun()
    
    # Acceso del Administrador Maestro
    if st.session_state.user_role == "ADMINISTRACION":
        bloque_administracion()
    elif st.session_state.user_role == "RECEPCION":
        bloque_recepcion()
    elif st.session_state.user_role == "CONTABILIDAD":
        st.title("💰 CONTABILIDAD")
        st.info("Sección en construcción para la siguiente etapa.")