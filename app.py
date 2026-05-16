import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import time

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Club de Leones Cumbayá-Ilaló", page_icon="logo leones.jpg", layout="wide", initial_sidebar_state="collapsed")

# --- 2. DISEÑO VISUAL SOBRIO Y FUSIONADO EN BLANCO ---
st.markdown(
    """
    <style>
    /* Forzar fondo blanco absoluto en toda la aplicación para fusionar el logo */
    .stApp { background-color: #ffffff; }
    .block-container { padding-top: 1rem; padding-bottom: 0rem; }
    
    /* Barra Lateral Azul y Oro */
    [data-testid="stSidebar"] { background-color: #003366 !important; }
    [data-testid="stSidebar"] * { color: white !important; }

    /* Botón Estilo Profesional Leones */
    .stButton>button { 
        width: 100%; border-radius: 6px; height: 3em; 
        background-color: #003366; color: white; 
        border: 1px solid #d4af37; font-weight: bold; 
    }
    .stButton>button:hover { background-color: #d4af37; color: #003366; }

    /* Tarjeta de Login Vertical Fina y Centrada */
    .card-login { 
        background-color: white; padding: 25px; 
        border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); 
        border-top: 5px solid #d4af37;
    }

    /* Tipografía Limpia */
    h2 { color: #003366; font-family: 'Segoe UI', sans-serif; font-weight: bold; margin-bottom: 5px; }
    .subtitle { color: #d4af37; font-weight: bold; letter-spacing: 2px; font-size: 1.1em; margin-bottom: 15px; text-align: center; }

    /* Forzar alineación de inputs */
    .stTextInput>div, .stSelectbox>div { margin-bottom: -15px; }
    .total-box { background-color: #f1f3f5; color: #003366; padding: 10px; border-radius: 8px; border: 1px solid #dee2e6; font-size: 1.1em; font-weight: bold; margin-top: 10px; }
    
    /* Contenedor estético para la Hoja Modelo de Historia Clínica */
    .hoja-clinica {
        background-color: #f8f9fa;
        padding: 25px;
        border-radius: 8px;
        border: 1px solid #e9ecef;
        margin-top: 15px;
    }
    .seccion-clinica {
        color: #003366;
        font-weight: bold;
        border-bottom: 2px solid #d4af37;
        margin-top: 15px;
        margin-bottom: 10px;
        font-size: 1.1em;
    }
    </style>
    """, unsafe_allow_html=True
)

# --- 3. BASE DE DATOS MÓDULO INTEGRADO ---
DB_NAME = 'club_leones_centro_medico.db'

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
    # Tabla estructurada con las nuevas columnas de contacto telefónico y de emergencia
    c.execute('''CREATE TABLE IF NOT EXISTS historias_clinicas 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha_registro TEXT, medico TEXT, 
                  paciente_nombre TEXT, paciente_cedula TEXT, paciente_telefono TEXT,
                  contacto_emergencia_nombre TEXT, contacto_emergencia_telefono TEXT,
                  motivo_consulta TEXT, signos_vitales TEXT, antecedentes TEXT, 
                  examen_fisico TEXT, diagnostico TEXT, evolucion TEXT)''')
    conn.commit(); conn.close()

init_db()

# --- 4. GESTIÓN DE ESTADO DE SESIÓN ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = None

if 'med_acceso_concedido' not in st.session_state:
    st.session_state.med_acceso_concedido = False
if 'med_nombre_guardado' not in st.session_state:
    st.session_state.med_nombre_guardado = ""

# --- 5. LOGIN VERTICAL ---
def login():
    st.markdown("<br>", unsafe_allow_html=True)
    col_izq, col_centro, col_der = st.columns([1.2, 1, 1.2])
    
    with col_centro:
        st.markdown("<div class='card-login'>", unsafe_allow_html=True)
        try: st.image("logo leones.jpg", use_container_width=True)
        except: pass
            
        st.markdown("<h2 style='text-align: center;'>CLUB DE LEONES CUMBAYA-ILALO</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #d4af37; font-weight: bold; margin-bottom: 20px;'>SISTEMA MÉDICO INTEGRAL</p>", unsafe_allow_html=True)
        st.markdown("<hr style='margin-top:0px; margin-bottom:15px; border-top: 1px solid #dee2e6;'>", unsafe_allow_html=True)
        
        b_destino = st.selectbox("Elija el bloque al que desea ingresar", ["RECEPCION", "ADMINISTRACION", "MEDICOS", "CONTABILIDAD"])
        u_nombre = st.text_input("USUARIO")
        p_clave = st.text_input("CLAVE", type="password", autocomplete="new-password")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("INGRESAR AL SISTEMA"):
            if u_nombre == "CMLeones" and p_clave == "2468":
                st.session_state.user_role = b_destino
                st.session_state.user_name = "Administrador Maestro"
                st.session_state.autenticado = True
                st.rerun()
            else:
                conn = get_connection()
                res = conn.execute("SELECT nombre, bloque FROM usuarios WHERE nombre=? AND cedula=? AND bloque=?", 
                                   (u_nombre, p_clave, b_destino)).fetchone()
                conn.close()
                if res:
                    st.session_state.user_role = res[1]
                    st.session_state.user_name = res[0]
                    st.session_state.autenticado = True
                    st.rerun()
                else:
                    st.error("⚠️ Credenciales incorrectas para este bloque.")
        st.markdown("</div>", unsafe_allow_html=True)

# --- 6. BLOQUE ADMINISTRACIÓN ---
def bloque_administracion():
    st.title("⚙️ ADMINISTRACIÓN GENERAL")
    menu = st.sidebar.radio("MENÚ", ["GESTIÓN DE PERMISOS", "GESTIÓN PROFESIONALES", "BASE DE DATOS PACIENTES", "LIQUIDACIÓN MENSUAL"])

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

    elif menu == "BASE DE DATOS PACIENTES":
        st.header("🗄️ Base de Datos Pacientes")
        try:
            df_hist_global = pd.read_sql("SELECT fecha_registro as 'Fecha Registro', paciente_nombre as 'Paciente', paciente_cedula as 'Cédula', paciente_telefono as 'Teléfono', medico as 'Médico', diagnostico as 'Diagnóstico CIE-10' FROM historias_clinicas ORDER BY fecha_registro DESC", get_connection())
            if not df_hist_global.empty:
                st.dataframe(df_hist_global, use_container_width=True, hide_index=True)
            else:
                st.info("No hay pacientes registrados en el historial clínico aún.")
        except:
            st.info("La base de datos de pacientes se poblará al guardar la primera historia clínica.")

    elif menu == "LIQUIDACIÓN MENSUAL":
        st.header("📊 Liquidación Mensual")
        st.info("Espacio destinado para reportes y cierres financieros.")

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
                            if c_b2.form_submit_button("ELIMINAR REGISTRO"):
                                db = get_connection(); db.execute("DELETE FROM consultas WHERE id=?", (r['id'],)); db.commit(); db.close(); st.warning("Eliminado"); time.sleep(0.5); st.rerun()
                st.markdown(f"**Total {med}: ${sub['total'].sum():.2f}**")
        else: st.info("No hay registros en la fecha seleccionada.")

# --- 8. CALLBACK DE INGRESO MÉDICO (LIMPIEZA DE ENTRADAS) ---
def ejecutar_ingreso_medico(usr, ced):
    if usr != "Seleccione Médico..." and ced:
        conn = sqlite3.connect('club_leones_centro_medico.db')
        es_valido = conn.execute("SELECT nombre FROM profesionales WHERE nombre=? AND cedula=?", (usr, ced)).fetchone()
        conn.close()
        
        if es_valido or (usr == "CMLeones" and ced == "2468"):
            st.session_state.med_acceso_concedido = True
            st.session_state.med_nombre_guardado = usr
            
            # Limpieza instantánea de los campos de firma al presionar INGRESO
            st.session_state["val_usuario"] = "Seleccione Médico..."
            st.session_state["val_cedula"] = ""
        else:
            st.session_state.med_acceso_concedido = False
            st.sidebar.error("❌ Credenciales inválidas.")

# --- 9. BLOQUE MÉDICOS ---
def bloque_medicos():
    st.markdown("## 🥼 INTERFAZ DE HISTORIAS CLÍNICAS")
    st.markdown("### 🔑 Validación de Firma Profesional")
    
    conn = get_connection()
    medicos_registrados = [p[0] for p in conn.execute("SELECT nombre FROM profesionales").fetchall()]
    conn.close()
    
    opciones_medicos = ["Seleccione Médico..."] + ["CMLeones"] + medicos_registrados
    
    c_m1, c_m2 = st.columns(2)
    doc_usuario = c_m1.selectbox("SELECCIONE SU NOMBRE DE PROFESIONAL MÉDICO", opciones_medicos, key="val_usuario")
    doc_cedula = c_m2.text_input("DIGITE SU NÚMERO DE CÉDULA MÉDICA", type="password", autocomplete="new-password", key="val_cedula")
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.button("INGRESO", on_click=ejecutar_ingreso_medico, args=(doc_usuario, doc_cedula))
    
    if st.session_state.med_acceso_concedido:
        medico_activo = st.session_state.med_nombre_guardado
        st.info(f"👨‍⚕️ Profesional Activo: {medico_activo}")
        st.divider()
        
        # --- HOJA MODELO DE HISTORIA CLÍNICA (SIEMPRE VISIBLE Y VACÍA PARA LLENADO) ---
        st.markdown("<div class='hoja-clinica'>", unsafe_allow_html=True)
        st.subheader("📝 HOJA MODELO DE HISTORIA CLÍNICA (ESTÁNDAR)")
        
        with st.form("nuevo_registro_clinico", clear_on_submit=False):
            
            st.markdown("<div class='seccion-clinica'>1. IDENTIFICACIÓN EXCLUSIVA DEL PACIENTE</div>", unsafe_allow_html=True)
            col_id1, col_id2, col_id3 = st.columns(3)
            p_nombre_input = col_id1.text_input("NOMBRE COMPLETO DEL PACIENTE")
            p_cedula_input = col_id2.text_input("NÚMERO DE CÉDULA DEL PACIENTE")
            p_telefono_input = col_id3.text_input("NÚMERO TELEFÓNICO DEL PACIENTE")
            
            st.markdown("<div class='seccion-clinica'>2. CONTACTO DE EMERGENCIA DEL PACIENTE</div>", unsafe_allow_html=True)
            col_em1, col_em2 = st.columns(2)
            p_contacto_nombre = col_em1.text_input("NOMBRE DE CONTACTO DE EMERGENCIA")
            p_contacto_tel = col_em2.text_input("NÚMERO TELEFÓNICO DE EMERGENCIA")
            
            st.markdown("<div class='seccion-clinica'>3. MOTIVO DE CONSULTA Y ANAMNESIS</div>", unsafe_allow_html=True)
            motivo_act = st.text_input("Motivo de la Consulta Actual")
            
            st.markdown("<div class='seccion-clinica'>4. SIGNOS VITALES</div>", unsafe_allow_html=True)
            col_sv1, col_sv2, col_sv3, col_sv4 = st.columns(4)
            pa = col_sv1.text_input("P. Arterial (mmHg)", placeholder="120/80")
            fc = col_sv2.text_input("Frec. Cardíaca (lpm)", placeholder="72")
            fr = col_sv3.text_input("Frec. Respiratoria (rpm)", placeholder="16")
            temp = col_sv4.text_input("Temperatura (°C)", placeholder="36.5")
            
            st.markdown("<div class='seccion-clinica'>5. ANTECEDENTES PATOLÓGICOS</div>", unsafe_allow_html=True)
            ant_personales = st.text_area("Antecedentes Personales (Clínicos, Quirúrgicos, Alergias)", placeholder="Ninguno / Diabetes / Hipertensión...")
            ant_familiares = st.text_area("Antecedentes Familiares", placeholder="Cardiopatías, Cáncer, etc...")
            
            st.markdown("<div class='seccion-clinica'>6. EXAMEN FÍSICO COMENTADO</div>", unsafe_allow_html=True)
            examen_fisico_txt = st.text_area("Descripción del examen físico y exploración del paciente")
            
            st.markdown("<div class='seccion-clinica'>7. DIAGNÓSTICO PRESUNTIVO O DEFINITIVO (CIE-10)</div>", unsafe_allow_html=True)
            diag_act = st.text_area("Impresión Diagnóstica / Códigos CIE-10")
            
            st.markdown("<div class='seccion-clinica'>8. PLAN DE TRATAMIENTO Y EVOLUCIÓN</div>", unsafe_allow_html=True)
            evol_act = st.text_area("Prescripción de medicamentos, indicaciones y plan terapéutico")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.form_submit_button("GUARDAR"):
                if p_nombre_input and p_cedula_input and diag_act and evol_act:
                    signos_vitales_compuesto = f"PA: {pa} | FC: {fc} | FR: {fr} | Temp: {temp}"
                    antecedentes_compuesto = f"Personales: {ant_personales} \nFamiliares: {ant_familiares}"
                    
                    conn = get_connection()
                    # CONTROL ANTI-DUPLICADOS LÓGICO
                    ultimo_guardado = conn.execute(
                        "SELECT motivo_consulta, diagnostico, evolucion FROM historias_clinicas WHERE paciente_cedula=? ORDER BY id DESC LIMIT 1", 
                        (p_cedula_input,)
                    ).fetchone()
                    
                    if ultimo_guardado and (ultimo_guardado[0] == motivo_act and ultimo_guardado[1] == diag_act and ultimo_guardado[2] == evol_act):
                        st.warning("⚠️ El registro clínico ya se encuentra guardado en la base de datos para este paciente. No se duplicaron datos.")
                        conn.close()
                    else:
                        f_reg = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        conn.execute(
                            """INSERT INTO historias_clinicas 
                               (fecha_registro, medico, paciente_nombre, paciente_cedula, paciente_telefono, contacto_emergencia_nombre, contacto_emergencia_telefono, motivo_consulta, signos_vitales, antecedentes, examen_fisico, diagnostico, evolucion) 
                               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                            (f_reg, medico_activo, p_nombre_input, p_cedula_input, p_telefono_input, p_contacto_nombre, p_contacto_tel, motivo_act, signos_vitales_compuesto, antecedentes_compuesto, examen_fisico_txt, diag_act, evol_act)
                        )
                        conn.commit()
                        conn.close()
                        st.success(f"✅ Historia clínica de {p_nombre_input.upper()} almacenada correctamente en la base de datos de pacientes.")
                        time.sleep(1)
                        st.rerun()
                else:
                    st.error("❌ Complete los campos obligatorios antes de guardar (Nombre, Cédula, Diagnóstico y Tratamiento).")
        st.markdown("</div>", unsafe_allow_html=True)

# --- 10. EJECUCIÓN NAVEGACIÓN GENERAL ---
if not st.session_state.autenticado:
    login()
else:
    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    try: st.sidebar.image("logo leones.jpg", width=120)
    except: pass
    st.sidebar.markdown(f"👤 **{st.session_state.user_name}**")
    if st.sidebar.button("SALIR DEL SISTEMA"):
        st.session_state.autenticado = False
        st.session_state.user_role = None
        st.session_state.user_name = None
        st.session_state.med_acceso_concedido = False
        st.session_state.med_nombre_guardado = ""
        st.rerun()

    st.sidebar.divider()
    if st.session_state.user_role == "ADMINISTRACION":
        bloque_administracion()
    elif st.session_state.user_role == "RECEPCION":
        bloque_recepcion()
    elif st.session_state.user_role == "MEDICOS":
        bloque_medicos()
    elif st.session_state.user_role == "CONTABILIDAD":
        st.title("💰 BLOQUE CONTABILIDAD")
        st.info("Bloque en construcción.")