import streamlit as st
import pandas as pd
import plotly.express as px

# Función para formatear moneda a estilo argentino (punto para miles, coma para decimales)
def formato_arg(valor, es_moneda=True):
    if es_moneda:
        texto = f"${valor:,.2f}"
    else:
        texto = f"{valor:,.0f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")

st.set_page_config(page_title="Dashboard Alta Gerencia - ObSBA", layout="wide")
st.title("📊 Panel de Control Directivo - Autorizaciones ObSBA")

st.sidebar.header("Carga de Base de Datos")
st.sidebar.markdown("Subí el Excel del cuatrimestre.")
uploaded_file = st.sidebar.file_uploader("Archivo Excel", type=["xlsx", "xls"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    
    col_fecha = 'fecha'
    col_cant = 'cantidad'
    col_precio_u = 'monto_unitario'
    col_precio_t = 'precio_total'
    col_nomen_cod = 'nomen_cod'
    col_nomen_des = 'nomen_des'
    col_clasif = 'clasificacion'
    col_razon_social = 'razonsocia'
    col_num_afiliado = 'afiliado'
    col_nom_afiliado = 'nombre'
    col_zona = 'zona'
    col_sede = 'sedes'
    
    # Diccionario para nombres formales en las tablas visuales
    nombres_formales = {
        col_fecha: 'Fecha',
        col_nomen_cod: 'Código',
        col_nomen_des: 'Práctica / Insumo',
        col_clasif: 'Clasificación',
        col_cant: 'Cantidad',
        col_precio_u: 'Precio Unitario',
        col_precio_t: 'Precio Total',
        col_razon_social: 'Centro Proveedor',
        col_num_afiliado: 'Nº Afiliado',
        col_nom_afiliado: 'Nombre Afiliado',
        col_zona: 'Zona',
        col_sede: 'Centro Autorizador'
    }

    df[col_fecha] = pd.to_datetime(df[col_fecha], errors='coerce')
    df['Mes_Num'] = df[col_fecha].dt.month
    meses_map = {5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto'}
    df['Mes'] = df['Mes_Num'].map(meses_map)
    orden_meses = ['Mayo', 'Junio', 'Julio', 'Agosto']
    df['Mes'] = pd.Categorical(df['Mes'], categories=orden_meses, ordered=True)

    df['afiliado_display'] = df[col_num_afiliado].astype(str) + " - " + df[col_nom_afiliado].astype(str)

    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 1. Resumen Ejecutivo (Macro)", 
        "🏥 2. Costos y Prestadores", 
        "👤 3. Auditoría de Afiliados",
        "🏢 4. Análisis de Sedes y Calidad"
    ])

    # ----------------------------------------
    # TAB 1: RESUMEN EJECUTIVO
    # ----------------------------------------
    with tab1:
        st.header("Visión General del Cuatrimestre")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Facturación Total", formato_arg(df[col_precio_t].sum()))
        col2.metric("Volumen Total (Cantidades)", formato_arg(df[col_cant].sum(), False))
        col3.metric("Afiliados Atendidos", formato_arg(df[col_num_afiliado].nunique(), False))
        col4.metric("Total de Prestadores", formato_arg(df[col_razon_social].nunique(), False))
        
        st.markdown("---")
        col_t1, col_t2 = st.columns(2)
        
        with col_t1:
            st.subheader("Evolución de Facturación Mensual")
            df_mes_fact = df.groupby('Mes', observed=False)[col_precio_t].sum().reset_index()
            fig_fact = px.line(df_mes_fact, x='Mes', y=col_precio_t, markers=True, text=col_precio_t)
            fig_fact.update_traces(texttemplate='$%{text:,.2f}', textposition='top center', textfont_size=14,
                                   hovertemplate='Gasto: $%{y:,.2f}<extra></extra>', cliponaxis=False)
            fig_fact.update_layout(separators=".,", yaxis_tickformat='$,.2f')
            st.plotly_chart(fig_fact, use_container_width=True)
            
        with col_t2:
            st.subheader("Volumen de Autorizaciones por Clasificación")
            # Ordenado de mayor a menor y limitando nombres largos
            df_clasif = df.groupby(col_clasif)[col_cant].sum().reset_index().sort_values(col_cant, ascending=True)
            fig_clasif = px.bar(df_clasif, x=col_cant, y=col_clasif, orientation='h', text=col_cant)
            fig_clasif.update_traces(texttemplate='%{text:,.0f}', textposition='outside', textfont_size=14,
                                     hovertemplate='Cantidad: %{x:,.0f}<extra></extra>', cliponaxis=False)
            fig_clasif.update_layout(separators=".,", xaxis=dict(range=[0, df_clasif[col_cant].max() * 1.25]))
            st.plotly_chart(fig_clasif, use_container_width=True)

        st.subheader("Desglose Mensual por Clasificación")
        df_clasif_mes = df.groupby(['Mes', col_clasif], observed=False)[col_cant].sum().reset_index()
        fig_clasif_mes = px.bar(df_clasif_mes, x='Mes', y=col_cant, color=col_clasif, barmode='group', text=col_cant)
        fig_clasif_mes.update_traces(texttemplate='%{text:,.0f}', textposition='outside', textfont_size=12, textangle=-90,
                                     hovertemplate='Cantidad: %{y:,.0f}<extra></extra>', cliponaxis=False)
        fig_clasif_mes.update_layout(separators=".,", yaxis=dict(range=[0, df_clasif_mes[col_cant].max() * 1.3]))
        st.plotly_chart(fig_clasif_mes, use_container_width=True)

    # ----------------------------------------
    # TAB 2: COSTOS Y PRESTADORES
    # ----------------------------------------
    with tab2:
        st.header("Análisis de Costos y Proveedores")
        
        st.subheader("Top 10 Prácticas que más presupuesto consumen")
        df_top_costos = df.groupby(col_nomen_des)[col_precio_t].sum().reset_index().sort_values(col_precio_t, ascending=True).tail(10)
        fig_top_costos = px.bar(df_top_costos, x=col_precio_t, y=col_nomen_des, orientation='h', text=col_precio_t)
        fig_top_costos.update_traces(texttemplate='$%{text:,.2f}', textposition='outside', textfont_size=14,
                                     hovertemplate='Gasto: $%{x:,.2f}<extra></extra>', cliponaxis=False)
        fig_top_costos.update_layout(separators=".,", xaxis=dict(range=[0, df_top_costos[col_precio_t].max() * 1.3]))
        st.plotly_chart(fig_top_costos, use_container_width=True)

        st.markdown("---")
        st.subheader("🔍 Consulta Rápida: Precio de Práctica en un Centro Específico")
        
        practicas_comunes = df[col_nomen_des].dropna().unique()
        col_esp1, col_esp2 = st.columns(2)
        with col_esp1:
            practica_esp = st.selectbox("1. Buscá la práctica/insumo:", practicas_comunes, key="prac_especifica")
            
        df_prac_esp_filtrada = df[df[col_nomen_des] == practica_esp]
        centros_disponibles = df_prac_esp_filtrada[col_razon_social].dropna().unique()
        
        with col_esp2:
            centro_esp = st.selectbox("2. Elegí el centro proveedor:", centros_disponibles, key="centro_especifico")
            
        df_resultado_esp = df_prac_esp_filtrada[df_prac_esp_filtrada[col_razon_social] == centro_esp]
        
        if not df_resultado_esp.empty:
            st.info(f"**Análisis de '{practica_esp}' en '{centro_esp}':**")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Precio Promedio", formato_arg(df_resultado_esp[col_precio_u].mean()))
            m2.metric("Precio Más Bajo", formato_arg(df_resultado_esp[col_precio_u].min()))
            m3.metric("Precio Más Alto", formato_arg(df_resultado_esp[col_precio_u].max()))
            m4.metric("Volumen Autorizado", formato_arg(df_resultado_esp[col_cant].sum(), False))
        else:
            st.warning("No hay registros para esta combinación.")

    # ----------------------------------------
    # TAB 3: AUDITORÍA DE AFILIADOS
    # ----------------------------------------
    with tab3:
        st.header("Análisis de Consumo por Afiliado")
        
        lista_afiliados = df['afiliado_display'].dropna().unique()
        afiliado_sel = st.selectbox("Escribí el NOMBRE o el NÚMERO del afiliado para buscarlo:", lista_afiliados)
        
        df_afil = df[df['afiliado_display'] == afiliado_sel]
        nom_afil_actual = df_afil[col_nom_afiliado].iloc[0]
        num_afil_actual = df_afil[col_num_afiliado].iloc[0]
        
        st.markdown(f"### 👤 {nom_afil_actual} (Nº {num_afil_actual})")
        st.write(f"**Gasto Total Cuatrimestral:** {formato_arg(df_afil[col_precio_t].sum())}")
        
        col_af1, col_af2 = st.columns(2)
        with col_af1:
            fig_afil_comp = px.pie(df_afil, values=col_precio_t, names=col_clasif, title="Composición del Gasto")
            fig_afil_comp.update_traces(textinfo='label+percent+value', texttemplate='%{label}<br>$%{value:,.2f}',
                                        hovertemplate='Clasificación: %{label}<br>Gasto: $%{value:,.2f}<extra></extra>')
            fig_afil_comp.update_layout(separators=".,")
            st.plotly_chart(fig_afil_comp, use_container_width=True)
            
        with col_af2:
            df_afil_mes = df_afil.groupby('Mes', observed=False)[col_precio_t].sum().reset_index()
            fig_afil_mes = px.bar(df_afil_mes, x='Mes', y=col_precio_t, text=col_precio_t, title="Consumo en el Tiempo")
            fig_afil_mes.update_traces(texttemplate='$%{text:,.2f}', textposition='outside', textfont_size=14,
                                       hovertemplate='Gasto: $%{y:,.2f}<extra></extra>', cliponaxis=False)
            fig_afil_mes.update_layout(separators=".,", yaxis=dict(range=[0, df_afil_mes[col_precio_t].max() * 1.3]))
            st.plotly_chart(fig_afil_mes, use_container_width=True)
            
        st.subheader("Historial de Consumos del Afiliado")
        # Mostrar dataframe con nombres formales
        df_afil_display = df_afil[[col_fecha, col_nomen_des, col_cant, col_precio_u, col_precio_t, col_razon_social, col_sede]].sort_values(col_fecha)
        df_afil_display = df_afil_display.rename(columns=nombres_formales)
        
        # Aplicamos formato argentino a las columnas de dinero
        st.dataframe(df_afil_display.style.format({
            "Precio Unitario": lambda x: formato_arg(x),
            "Precio Total": lambda x: formato_arg(x),
            "Fecha": lambda x: x.strftime('%Y-%m-%d')
        }), use_container_width=True)

    # ----------------------------------------
    # TAB 4: CALIDAD Y DUPLICADOS
    # ----------------------------------------
    with tab4:
        st.header("Control de Calidad de Datos ObSBA")
        
        st.subheader("⚠️ Auditoría de Registros Duplicados")
        st.markdown("Buscando prácticas idénticas autorizadas para un mismo afiliado **en la misma fecha**...")
        
        # Lógica de detección de duplicados (Misma fecha, mismo afiliado, misma práctica)
        df_duplicados = df[df.duplicated(subset=[col_fecha, col_num_afiliado, col_nomen_des], keep=False)]
        
        if not df_duplicados.empty:
            df_duplicados = df_duplicados.sort_values(by=[col_fecha, col_num_afiliado])
            cant_casos = df_duplicados.groupby([col_fecha, col_num_afiliado, col_nomen_des]).ngroups
            st.error(f"Se detectaron {cant_casos} casos potenciales de doble carga o sobre-autorización.")
            
            df_dup_display = df_duplicados[[col_fecha, col_num_afiliado, col_nom_afiliado, col_nomen_des, col_cant, col_precio_t, col_razon_social]]
            df_dup_display = df_dup_display.rename(columns=nombres_formales)
            
            st.dataframe(df_dup_display.style.format({
                "Precio Total": lambda x: formato_arg(x),
                "Fecha": lambda x: x.strftime('%Y-%m-%d')
            }), use_container_width=True)
        else:
            st.success("¡Excelente! No se detectaron autorizaciones duplicadas para el mismo afiliado en la misma fecha.")

        st.markdown("---")
        st.subheader("⚠️ Inconsistencias en el Nomenclador")
        
        inconsistencias = df.groupby(col_nomen_cod)[col_nomen_des].nunique().reset_index()
        codigos_problematicos = inconsistencias[inconsistencias[col_nomen_des] > 1][col_nomen_cod]
        
        if not codigos_problematicos.empty:
            st.warning(f"Se encontraron {len(codigos_problematicos)} códigos con descripciones múltiples.")
            df_inconsistente = df[df[col_nomen_cod].isin(codigos_problematicos)][[col_nomen_cod, col_nomen_des]].drop_duplicates().sort_values(col_nomen_cod)
            df_inconsistente = df_inconsistente.rename(columns=nombres_formales)
            st.dataframe(df_inconsistente, use_container_width=True)
        else:
            st.success("El nomenclador está limpio. Un código = Una descripción.")

else:
    st.info("👈 Subí el reporte de Excel para generar la visualización.")
