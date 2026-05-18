import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import time

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Club de Leones Cumbayá-Ilaló", page_icon="logo leones.jpg", layout="wide", initial_sidebar_state="collapsed")

# --- 2. DISEÑO VISUAL SOBRIO, FUSIONADO EN BLANCO Y MÁXIMA PROTECCIÓN ---
st.markdown(
    """
    <style>
    /* Forzar fondo blanco absoluto en toda la aplicación para fusionar el logo */
    .stApp { background-color: #ffffff; }
    .block-container { padding-top: 1rem; padding-bottom: 0rem; }
    
    /* SEGURIDAD VISUAL: Oculta por completo la barra superior derecha de GitHub / Streamlit (Share, Star, Edit, etc.) */
    .stAppToolbar { display: none !important; }
    
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
    
    /* Contenedor estético para la Hoja Modelo de Historia Clínica y Contabilidad */
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
    c.execute('''CREATE TABLE IF NOT EXISTS historias_clinicas 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha_registro TEXT, medico TEXT, 
                  paciente_nombre TEXT, paciente_cedula TEXT, paciente_telefono TEXT,
                  contacto_emergencia_nombre TEXT, contacto_emergencia_telefono TEXT,
                  motivo_consulta TEXT, signos_vitales TEXT, antecedentes TEXT, 
                  examen_fisico TEXT, diagnostico TEXT, evolucion TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS plan_cuentas 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, codigo TEXT UNIQUE, nombre TEXT, tipo TEXT)''')
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

if 'selector_control' not in st.session_state:
    st.session_state.selector_control = 0

# --- 5. LOGIN VERTICAL ---
def login():
    st.markdown("<br>", unsafe_allow_html=True)
    col_izq, col_centro, col_der = st.columns([1.2, 1, 1.2])
    
    with col_centro:
        st.markdown("<div class='card-login'>", unsafe_allow_html=True)
        try: 
            st.image("logo leones.jpg", use_container_width=True)
        except: 
            pass
            
        st.markdown("<h2 style='text-align: center;'>CLUB DE LEONES CUMBAYA-ILALO</h2>", unsafe_allow_html=True)
        st.markdown("<p class='subtitle' style='text-align: center;'>SISTEMA MÉDICO INTEGRAL</p>", unsafe_allow_html=True)
        st.markdown("<hr style='margin-top:0px; margin-bottom:15px; border-top: 1px solid #dee2e6;'>", unsafe_allow_html=True)
        
        servicios_disponibles = [" ", "RECEPCION", "ADMINISTRACION", "MEDICOS", "CONTABILIDAD"]
        b_destino = st.selectbox(
            "Elija el servicio al que desea ingresar", 
            servicios_disponibles, 
            index=0,
            key=f"widget_servicio_{st.session_state.selector_control}"
        )
        
        if b_destino == " ":
            st.info("Por favor, seleccione un servicio arriba para desplegar los campos de acceso.")
            u_nombre, p_clave = "", ""
        else:
            u_nombre = st.text_input("USUARIO", value="", autocomplete="new-password", key=f"usr_real_{st.session_state.selector_control}")
            p_clave = st.text_input("CLAVE", value="", type="password", autocomplete="new-password", key=f"pwd_real_{st.session_state.selector_control}")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("INGRESAR AL SISTEMA"):
            if b_destino == " " or not u_nombre or not p_clave:
                st.error("⚠️ Complete todos los campos personales de acceso manual.")
            elif u_nombre == "CMLeones" and p_clave == "2468":
                st.session_state.autenticado = True
                st.session_state.user_role = b_destino
                st.session_state.user_name = "Administrador Maestro"
                st.rerun()
            else:
                conn = get_connection()
                res = conn.execute("SELECT nombre, cedula, bloque FROM usuarios WHERE nombre=? AND cedula=? AND bloque=?", 
                                   (u_nombre, p_clave, b_destino)).fetchone()
                conn.close()
                if res:
                    st.session_state.autenticado = True
                    st.session_state.user_name = res[0]
                    st.session_state.user_role = res[2]
                    st.rerun()
                else:
                    st.error("⚠️ Credenciales incorrectas para este servicio.")
                    
        st.markdown("</div>", unsafe_allow_html=True)

# --- 6. BLOQUE ADMINISTRACIÓN ---
def bloque_administracion():
    st.title("⚙️ ADMINISTRACIÓN GENERAL")
    menu = st.sidebar.radio("MENÚ", ["GESTIÓN DE PERMISOS", "GESTIÓN PROFESIONALES", "BASE DE DATOS PACIENTES", "LIQUIDACIÓN MENSUAL"])

    if menu == "GESTIÓN DE PERMISOS":
        st.header("🛂 Control de Permisos")
        with st.form("f_per", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            n, c = c1.text_input("Nombre completo"), c2.text_input("Cédula (clave)", type="password")
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
                    c_doc = st.text_input("Cédula", type="password")
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
        st.header("🗄️ Fichas e Historias Clínicas de Pacientes")
        st.markdown("---")
        
        conn = get_connection()
        medicos_db = [r[0] for r in conn.execute("SELECT nombre FROM profesionales ORDER BY nombre").fetchall()]
        opciones_medicos_auditoria = ["CMLeones"] + medicos_db
        
        medico_sel = st.selectbox("🩺 Seleccione el Médico Especialista para ver sus pacientes:", ["Seleccione Médico..."] + opciones_medicos_auditoria)
        
        if medico_sel != "Seleccione Médico...":
            pacientes_db = [r[0] for r in conn.execute("SELECT DISTINCT paciente_nombre FROM historias_clinicas WHERE medico=? ORDER BY paciente_nombre", (medico_sel,)).fetchall()]
            
            if not pacientes_db:
                st.warning(f"ℹ️ El profesional '{medico_sel}' está registrado, pero no posee historias clínicas almacenadas en la base de datos actualmente.")
            else:
                paciente_sel = st.selectbox("👤 Seleccione el Paciente:", ["Seleccione Paciente..."] + pacientes_db)
                
                if paciente_sel != "Seleccione Paciente...":
                    fechas_db = [r[0] for r in conn.execute("SELECT fecha_registro FROM historias_clinicas WHERE medico=? AND paciente_nombre=? ORDER BY fecha_registro DESC", (medico_sel, paciente_sel)).fetchall()]
                    
                    fechas_sel = st.multiselect("📅 Seleccione la o las Fechas de Atención a consultar:", fechas_db)
                    
                    if fechas_sel:
                        st.markdown("### 📄 Expedientes Clínicos Seleccionados")
                        
                        texto_completo_documento = f"CLUB DE LEONES CUMBAYÁ-ILALÓ\nREPORTE DE AUDITORÍA CLÍNICA\n"
                        texto_completo_documento += f"MÉDICO: {medico_sel.upper()} | PACIENTE: {paciente_sel.upper()}\n"
                        texto_completo_documento += "="*60 + "\n\n"
                        
                        for f in fechas_sel:
                            datos_clinicos = conn.execute(
                                """SELECT paciente_cedula, paciente_telefono, contacto_emergencia_nombre, 
                                          contacto_emergencia_telefono, motivo_consulta, signos_vitales, 
                                          antecedentes, examen_fisico, diagnostico, evolucion 
                                   FROM historias_clinicas WHERE medico=? AND paciente_nombre=? AND fecha_registro=?""",
                                (medico_sel, paciente_sel, f)
                            ).fetchone()
                            
                            if datos_clinicos:
                                with st.container():
                                    st.markdown(f"<div class='hoja-clinica'>", unsafe_allow_html=True)
                                    st.markdown(f"#### ⏱️ Atención Registrada: {f}")
                                    st.write(f"**Cédula Paciente:** {datos_clinicos[0]} | **Teléfono:** {datos_clinicos[1]}")
                                    st.write(f"**Contacto de Emergencia:** {datos_clinicos[2]} ({datos_clinicos[3]})")
                                    st.markdown("<div class='seccion-clinica'>Motivo de Consulta y Anamnesis</div>", unsafe_allow_html=True)
                                    st.write(datos_clinicos[4])
                                    st.markdown("<div class='seccion-clinica'>Signos Vitales</div>", unsafe_allow_html=True)
                                    st.write(datos_clinicos[5])
                                    st.markdown("<div class='seccion-clinica'>Antecedentes Patológicos</div>", unsafe_allow_html=True)
                                    st.write(datos_clinicos[6])
                                    st.markdown("<div class='seccion-clinica'>Examen Físico</div>", unsafe_allow_html=True)
                                    st.write(datos_clinicos[7])
                                    st.markdown("<div class='seccion-clinica'>Diagnóstico (CIE-10)</div>", unsafe_allow_html=True)
                                    st.write(datos_clinicos[8])
                                    st.markdown("<div class='seccion-clinica'>Plan de Tratamiento y Evolución</div>", unsafe_allow_html=True)
                                    st.write(datos_clinicos[9])
                                    st.markdown("</div>", unsafe_allow_html=True)
                                    st.write("<br>", unsafe_allow_html=True)
                                
                                texto_completo_documento += f"FECHA REGISTRO: {f}\n"
                                texto_completo_documento += f"Cédula: {datos_clinicos[0]} | Teléfono: {datos_clinicos[1]}\n"
                                texto_completo_documento += f"Contacto Emergencia: {datos_clinicos[2]} - Tel: {datos_clinicos[3]}\n"
                                texto_completo_documento += f"- MOTIVO: {datos_clinicos[4]}\n"
                                texto_completo_documento += f"- SIGNOS VITALES: {datos_clinicos[5]}\n"
                                texto_completo_documento += f"- ANTECEDENTES: {datos_clinicos[6]}\n"
                                texto_completo_documento += f"- EXAMEN FÍSICO: {datos_clinicos[7]}\n"
                                texto_completo_documento += f"- DIAGNÓSTICO: {datos_clinicos[8]}\n"
                                texto_completo_documento += f"- TRATAMIENTO: {datos_clinicos[9]}\n"
                                texto_completo_documento += "-"*50 + "\n\n"
                        
                        st.markdown("### 🖨️ Acciones de Reporte")
                        col_print, col_download = st.columns(2)
                        
                        if col_print.button("🖨️ IMPRIMIR SELECCIONADAS"):
                            st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
                        
                        nombre_archivo_salida = f"Ficha_{paciente_sel.replace(' ', '_')}.txt"
                        col_download.download_button(
                            label="💾 DESCARGAR SELECCIONADAS (.TXT)",
                            data=texto_completo_documento,
                            file_name=nombre_archivo_salida,
                            mime="text/plain"
                        )
        conn.close()

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

# --- 8. CALLBACK DE INGRESO MÉDICO ---
def ejecutar_ingreso_medico(usr, ced):
    if usr != "Seleccione Médico..." and ced:
        conn = sqlite3.connect('club_leones_centro_medico.db')
        es_valido = conn.execute("SELECT nombre FROM profesionales WHERE nombre=? AND cedula=?", (usr, ced)).fetchone()
        conn.close()
        
        if es_valido or (usr == "CMLeones" and ced == "2468"):
            st.session_state.med_acceso_concedido = True
            st.session_state.med_nombre_guardado = usr
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
    
    col_med_pass, col_med_ojo = st.columns([6, 1])
    ver_med_clave = col_med_ojo.checkbox("👁️", key="ojo_medicos", help="Mostrar/Ocultar Clave")
    tipo_med_input = "default" if ver_med_clave else "password"
    
    doc_cedula = col_med_pass.text_input("DIGITE SU NÚMERO DE CÉDULA MÉDICA", type=tipo_med_input, autocomplete="new-password", key="val_cedula")
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.button("INGRESO", on_click=ejecutar_ingreso_medico, args=(doc_usuario, doc_cedula))
    
    if st.session_state.med_acceso_concedido:
        medico_activo = st.session_state.med_nombre_guardado
        st.info(f"👨‍⚕️ Profesional Activo: {medico_activo}")
        st.divider()
        
        st.markdown("### 🔍 CONSULTAR ANTECEDENTES")
        buscar_cedula = st.text_input("INGRESE LA CÉDULA DEL PACIENTE PARA CARGAR HISTORIAS CLÍNICAS ANTERIORES")
        
        df_anteriores = pd.DataFrame()
        if buscar_cedula:
            conn = get_connection()
            df_anteriores = pd.read_sql(f"SELECT fecha_registro, medico, motivo_consulta, signos_vitales, antecedentes, examen_fisico, diagnostico, evolucion FROM historias_clinicas WHERE paciente_cedula='{buscar_cedula}' ORDER BY fecha_registro DESC", conn)
            conn.close()

        st.markdown("<div class='hoja-clinica'>", unsafe_allow_html=True)
        st.subheader("📝 HOJA MODELO DE HISTORIA CLÍNICA (ESTÁNDAR)")
        
        if not df_anteriores.empty:
            fechas_disponibles = list(df_anteriores['fecha_registro'])
            fecha_sel = st.selectbox("📅 SELECCIONE LA FECHA DE LA HISTORIA CLÍNICA ANTERIOR PARA REVISAR DATOS:", ["Elija una fecha pasará a cargar los datos..."] + fechas_disponibles)
            
            if fecha_sel != "Elija un fecha pasará a cargar los datos...":
                registro_pasado = df_anteriores[df_anteriores['fecha_registro'] == fecha_sel].iloc[0]
                
                st.info(f"""
                ⏱️ **HISTORIAL CLÍNICO DEL {fecha_sel}** (Atendido por: {registro_pasado['medico']})
                * **Motivo de Consulta:** {registro_pasado['motivo_consulta']}
                * **Signos Vitales:** {registro_pasado['signos_vitales']}
                * **Antecedentes:** {registro_pasado['antecedentes']}
                * **Examen Físico:** {registro_pasado['examen_fisico']}
                * **Diagnóstico (CIE-10):** {registro_pasado['diagnostico']}
                * **Plan de Tratamiento / Evolución:** {registro_pasado['evolucion']}
                """)
        else:
            if buscar_cedula:
                st.caption("ℹ️ No se encontraron antecedentes médicos previos para el número de cédula ingresado.")

        with st.form("nuevo_registro_clinico", clear_on_submit=False):
            
            st.markdown("<div class='seccion-clinica'>1. IDENTIFICACIÓN EXCLUSIVA DEL PACIENTE</div>", unsafe_allow_html=True)
            col_id1, col_id2, col_id3 = st.columns(3)
            p_nombre_input = col_id1.text_input("NOMBRE COMPLETO DEL PACIENTE", autocomplete="off")
            p_cedula_input = col_id2.text_input("NÚMERO DE CÉDULA DEL PACIENTE", value=buscar_cedula, autocomplete="off")
            p_telefono_input = col_id3.text_input("NÚMERO TELEFÓNICO DEL PACIENTE", autocomplete="off")
            
            st.markdown("<div class='seccion-clinica'>2. CONTACTO DE EMERGENCIA DEL PACIENTE</div>", unsafe_allow_html=True)
            col_em1, col_em2 = st.columns(2)
            p_contacto_nombre = col_em1.text_input("NOMBRE DE CONTACTO DE EMERGENCIA", autocomplete="off")
            p_contacto_tel = col_em2.text_input("NÚMERO TELEFÓNICO DE EMERGENCIA", autocomplete="off")
            
            st.markdown("<div class='seccion-clinica'>3. MOTIVO DE CONSULTA Y ANAMNESIS</div>", unsafe_allow_html=True)
            motivo_act = st.text_input("Motivo de la Consulta Actual", autocomplete="off")
            
            st.markdown("<div class='seccion-clinica'>4. SIGNOS VITALES</div>", unsafe_allow_html=True)
            col_sv1, col_sv2, col_sv3, col_sv4 = st.columns(4)
            pa = col_sv1.text_input("P. Arterial (mmHg)", placeholder="120/80", autocomplete="off")
            fc = col_sv2.text_input("Frec. Cardíaca (lpm)", placeholder="72", autocomplete="off")
            fr = col_sv3.text_input("Frec. Respiratoria (rpm)", placeholder="16", autocomplete="off")
            temp = col_sv4.text_input("Temperatura (°C)", placeholder="36.5", autocomplete="off")
            
            st.markdown("<div class='seccion-clinica'>5. ANANTECEDENTES PATOLÓGICOS</div>", unsafe_allow_html=True)
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

# --- 10. BLOQUE CONTABILIDAD ---
def bloque_contabilidad():
    st.title("📊 SISTEMA CONTABLE INTEGRADO")
    
    opcion_contable = st.sidebar.radio(
        "MÓDULO CONTABLE", 
        ["CUADRE DE CAJA DIARIA", "PLAN DE CUENTAS", "LIBRO DIARIO", "LIBRO MAYOR", "RESUMEN DE ATENCIONES"]
    )
    
    conn = get_connection()
    
    if opcion_contable == "CUADRE DE CAJA DIARIA":
        st.header("💰 Control de Arqueo y Cuadre de Caja")
        col_f1, col_f2 = st.columns(2)
        f_inicio = col_f1.date_input("Fecha Inicio Consulta", datetime.today())
        f_fin = col_f2.date_input("Fecha Fin Consulta", datetime.today())
        
        df_caja = pd.read_sql(
            f"SELECT fecha, forma_pago, medico, paciente, total FROM consultas WHERE fecha BETWEEN '{f_inicio}' AND '{f_fin}'", 
            conn
        )
        
        if not df_caja.empty:
            st.markdown(f"#### Movimientos registrados desde {f_inicio} hasta {f_fin}")
            st.dataframe(df_caja, use_container_width=True, hide_index=True)
            
            total_recaudado = df_caja['total'].sum()
            st.markdown(f"<div class='total-box'>💵 TOTAL GENERAL RECAUDADO EN CAJA: ${total_recaudado:.2f}</div>", unsafe_allow_html=True)
            
            st.markdown("##### Resumen por Forma de Pago")
            df_resumen_pago = df_caja.groupby('forma_pago')['total'].sum().reset_index()
            st.table(df_resumen_pago.rename(columns={'forma_pago': 'Forma de Pago', 'total': 'Total ($)'}))
        else:
            st.info("No se registran movimientos de ingresos en el rango de fechas seleccionado.")
            
    elif opcion_contable == "PLAN DE CUENTAS":
        st.header("🗂️ Configuración del Plan de Cuentas Contables")
        
        with st.form("crear_cuenta_contable", clear_on_submit=True):
            st.write("**Añadir Cuenta Contable al Catálogo (Principios de Contabilidad)**")
            c1, c2, c3 = st.columns(3)
            cod_c = c1.text_input("Código de la Cuenta (Ej: 1.1.01)", autocomplete="off")
            nom_c = c2.text_input("Nombre de la Cuenta (Ej: Caja General)", autocomplete="off")
            tipo_c = c3.selectbox("Tipo de Cuenta", ["Activo", "Pasivo", "Patrimonio", "Ingreso", "Gasto"])
            
            if st.form_submit_button("Registrar Cuenta"):
                if cod_c and nom_c:
                    try:
                        conn.execute("INSERT INTO plan_cuentas (codigo, nombre, tipo) VALUES (?,?,?)", (cod_c, nom_c, tipo_c))
                        conn.commit()
                        st.success("✅ Cuenta contable añadida exitosamente.")
                    except:
                        st.error("❌ El código de cuenta ya existe en los registros.")
                        
        df_cuentas = pd.read_sql("SELECT codigo as 'Código', nombre as 'Cuenta Contable', tipo as 'Naturaleza' FROM plan_cuentas ORDER BY codigo", conn)
        st.markdown("### Catálogo de Cuentas Vigente")
        st.dataframe(df_cuentas, use_container_width=True, hide_index=True)
        
    elif opcion_contable == "LIBRO DIARIO":
        st.header("📖 Libro Diario de Asientos")
        f_diario = st.date_input("Seleccione Fecha de Operación", datetime.today())
        
        df_diario = pd.read_sql(
            f"SELECT id as 'N° Asiento', fecha as 'Fecha', paciente as 'Concepto/Paciente', 'Ingreso por Consulta' as 'Detalle', total as 'Debe (Ingreso)', 0.0 as 'Haber' FROM consultas WHERE fecha='{f_diario}'", 
            conn
        )
        
        if not df_diario.empty:
            st.dataframe(df_diario, use_container_width=True, hide_index=True)
            st.markdown(f"**Total Débitos del día:** ${df_diario['Debe (Ingreso)'].sum():.2f} | **Total Créditos del día:** $0.00")
        else:
            st.info("No se registran asientos de diario automáticos para la fecha elegida.")
            
    elif opcion_contable == "LIBRO MAYOR":
        st.header("🗄️ Libro Mayor Auxiliar Mensual")
        mes_sel = st.selectbox("Seleccione Mes de Ejercicio Contable", ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"])
        anio_sel = st.selectbox("Seleccione Año de Ejercicio Contable", ["2026", "2025", "2027"])
        
        df_mayor = pd.read_sql(
            f"SELECT fecha, medico, paciente, total FROM consultas WHERE fecha LIKE '{anio_sel}-{mes_sel}-%'", 
            conn
        )
        
        if not df_mayor.empty:
            st.markdown(f"### Movimientos Mayorizados para el periodo {mes_sel}/{anio_sel}")
            st.dataframe(df_mayor.rename(columns={'fecha': 'Fecha', 'medico': 'Referencia', 'paciente': 'Detalle', 'total': 'Saldo Debito ($)'}), use_container_width=True, hide_index=True)
            st.markdown(f"<div class='total-box'>💰 Saldo Acumulado en el Periodo: ${df_mayor['total'].sum():.2f}</div>", unsafe_allow_html=True)
        else:
            st.info("No se registran movimientos mayorizados en el periodo seleccionado.")
            
    elif opcion_contable == "RESUMEN DE ATENCIONES":
        st.header("📈 Resúmenes Estadísticos Contables y de Atenciones")
        
        # --- PRIMERA SECCIÓN: FILTRO DINÁMICO POR FECHA Y MÉDICO ---
        st.markdown("### Resumen de Facturación y Atenciones por Médico")
        
        medicos_db = [r[0] for r in conn.execute("SELECT nombre FROM profesionales ORDER BY nombre").fetchall()]
        opciones_medicos_filtro = ["CMLeones"] + medicos_db
        
        col_filtro_f1, col_filtro_f2, col_filtro_med = st.columns([1, 1, 1.5])
        f_desde = col_filtro_f1.date_input("Fecha Desde (Médico):", datetime.today(), key="filtro_fecha_desde")
        f_hasta = col_filtro_f2.date_input("Fecha Hasta (Médico):", datetime.today(), key="filtro_fecha_hasta")
        medico_seleccionado = col_filtro_med.selectbox("Seleccione el Médico Profesional:", opciones_medicos_filtro, key="filtro_medico_atenciones")
        
        df_atenciones_filtrado = pd.read_sql(
            f"""SELECT fecha, total FROM consultas 
                WHERE medico = '{medico_seleccionado}' 
                AND fecha BETWEEN '{f_desde}' AND '{f_hasta}'
                ORDER BY fecha ASC""", 
            conn
        )
        
        if not df_atenciones_filtrado.empty:
            df_atenciones_filtrado.insert(0, 'Número', range(1, len(df_atenciones_filtrado) + 1))
            df_atenciones_filtrado = df_atenciones_filtrado.rename(columns={'fecha': 'Fecha', 'total': 'Valor Cobrado ($)'})
            st.markdown(f"**Reporte de atenciones para {medico_seleccionado} (Desde: {f_desde} | Hasta: {f_hasta})**")
            st.dataframe(df_atenciones_filtrado, use_container_width=True, hide_index=True)
            suma_cobrada = df_atenciones_filtrado['Valor Cobrado ($)'].sum()
            st.markdown(f"<div class='total-box'>💰 TOTAL COBRADO POR EL MÉDICO EN ESTE RANGO: ${suma_cobrada:.2f}</div>", unsafe_allow_html=True)
        else:
            st.info(f"No se encontraron registros de atenciones para el médico '{medico_seleccionado}' en el rango de fechas seleccionado.")
            
        st.markdown("<br><hr>", unsafe_allow_html=True)
        
        # --- SEGUNDA SECCIÓN MODIFICADA: FILTRO DINÁMICO POR FECHA Y TIPO DE PAGO ---
        st.markdown("### Resumen de Atenciones por Tipo de Pago")
        
        # Opciones fijas de formas de pago utilizadas en el bloque de Recepción
        opciones_pagos_filtro = ["Efectivo", "Transferencia", "Pago Plux", "Deuna", "DataFast"]
        
        # Estructura de campos de filtro lado a lado
        col_pago_f1, col_pago_f2, col_pago_sel = st.columns([1, 1, 1.5])
        f_pago_desde = col_pago_f1.date_input("Fecha Desde (Pago):", datetime.today(), key="filtro_pago_desde")
        f_pago_hasta = col_pago_f2.date_input("Fecha Hasta (Pago):", datetime.today(), key="filtro_pago_hasta")
        pago_seleccionado = col_pago_sel.selectbox("Seleccione el Tipo de Pago:", opciones_pagos_filtro, key="filtro_tipo_pago_atenciones")
        
        # Ejecutar consulta filtrando rango de fechas y la forma de pago seleccionada
        df_pagos_filtrado = pd.read_sql(
            f"""SELECT fecha, total FROM consultas 
                WHERE forma_pago = '{pago_seleccionado}' 
                AND fecha BETWEEN '{f_pago_desde}' AND '{f_pago_hasta}'
                ORDER BY fecha ASC""", 
            conn
        )
        
        if not df_pagos_filtrado.empty:
            # Crear columna numérica secuencial desde 1
            df_pagos_filtrado.insert(0, 'Número', range(1, len(df_pagos_filtrado) + 1))
            
            # Renombrar columnas exactamente como se solicitó
            df_pagos_filtrado = df_pagos_filtrado.rename(columns={
                'fecha': 'Fecha',
                'total': 'Valor Cobrado ($)'
            })
            
            st.markdown(f"**Reporte de transacciones en {pago_seleccionado} (Desde: {f_pago_desde} | Hasta: {f_pago_hasta})**")
            st.dataframe(df_pagos_filtrado, use_container_width=True, hide_index=True)
            
            # Sumatoria total del dinero recaudado por este método de pago
            suma_pagos = df_pagos_filtrado['Valor Cobrado ($)'].sum()
            st.markdown(f"<div class='total-box'>💰 TOTAL GENERAL RECAUDADO EN {pago_seleccionado.upper()}: ${suma_pagos:.2f}</div>", unsafe_allow_html=True)
        else:
            st.info(f"No se encontraron registros de transacciones para la forma de pago '{pago_seleccionado}' en el rango de fechas seleccionado.")
            
    conn.close()

# --- 11. EJECUCIÓN NAVEGACIÓN GENERAL ---
if not st.session_state.autenticado:
    login()
else:
    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    try: 
        st.sidebar.image("logo leones.jpg", width=120)
    except: 
        pass
    st.sidebar.markdown(f"👤 **{st.session_state.user_name}**")
    
    if st.sidebar.button("SALIR DEL SISTEMA"):
        st.session_state.autenticado = False
        st.session_state.user_role = None
        st.session_state.user_name = None
        st.session_state.med_acceso_concedido = False
        st.session_state.med_nombre_guardado = ""
        
        if "usr_real_input" in st.session_state:
            st.session_state["usr_real_input"] = ""
        if "pwd_real_input" in st.session_state:
            st.session_state["pwd_real_input"] = ""
            
        st.session_state.selector_control += 1
        st.rerun()

    st.sidebar.divider()
    if st.session_state.user_role == "ADMINISTRACION":
        bloque_administracion()
    elif st.session_state.user_role == "RECEPCION":
        bloque_recepcion()
    elif st.session_state.user_role == "MEDICOS":
        bloque_medicos()
    elif st.session_state.user_role == "CONTABILIDAD":
        bloque_contabilidad()