import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Dashboard Alta Gerencia - OSPBA", layout="wide")
st.title("📊 Panel de Control Directivo - Autorizaciones OSPBA")

# Barra lateral para carga de datos
st.sidebar.header("Carga de Base de Datos")
st.sidebar.markdown("Subí el Excel del cuatrimestre (Mayo - Agosto).")
uploaded_file = st.sidebar.file_uploader("Archivo Excel", type=["xlsx", "xls"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    
    # Preprocesamiento
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
    
    # Formateo de fechas
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
    # TAB 1: RESUMEN EJECUTIVO (MACRO)
    # ----------------------------------------
    with tab1:
        st.header("Visión General del Cuatrimestre (Mayo - Agosto)")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Facturación Total", f"${df[col_precio_t].sum():,.2f}")
        col2.metric("Volumen Total (Cantidades)", f"{df[col_cant].sum():,.0f}")
        col3.metric("Afiliados Atendidos", f"{df[col_num_afiliado].nunique()}")
        col4.metric("Total de Prestadores", f"{df[col_razon_social].nunique()}")
        
        st.markdown("---")
        
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.subheader("Evolución de Facturación Mensual")
            df_mes_fact = df.groupby('Mes', observed=False)[col_precio_t].sum().reset_index()
            fig_fact = px.line(df_mes_fact, x='Mes', y=col_precio_t, markers=True, text=col_precio_t,
                               labels={col_precio_t: 'Facturación ($)'})
            fig_fact.update_traces(line_color='#1f77b4', line_width=3, marker_size=10, 
                                   texttemplate='$%{text:,.2f}', textposition='top center',
                                   hovertemplate='Gasto: $%{y:,.2f}<extra></extra>', cliponaxis=False)
            fig_fact.update_layout(yaxis_tickformat='$,.2f')
            st.plotly_chart(fig_fact, use_container_width=True)
            
        with col_t2:
            st.subheader("Volumen de Autorizaciones por Clasificación")
            df_clasif = df.groupby(col_clasif)[col_cant].sum().reset_index().sort_values(col_cant, ascending=False)
            fig_clasif = px.bar(df_clasif, x=col_cant, y=col_clasif, orientation='h', text=col_cant,
                                labels={col_cant: 'Cantidad Autorizada', col_clasif: 'Tipo de Práctica/Insumo'})
            fig_clasif.update_traces(texttemplate='%{text:,.0f}', textposition='outside', 
                                     hovertemplate='Cantidad: %{x:,.0f}<extra></extra>', cliponaxis=False)
            st.plotly_chart(fig_clasif, use_container_width=True)

        st.subheader("Desglose Mensual por Clasificación")
        df_clasif_mes = df.groupby(['Mes', col_clasif], observed=False)[col_cant].sum().reset_index()
        fig_clasif_mes = px.bar(df_clasif_mes, x='Mes', y=col_cant, color=col_clasif, barmode='group', text=col_cant)
        fig_clasif_mes.update_traces(texttemplate='%{text:,.0f}', textposition='outside', 
                                     hovertemplate='Cantidad: %{y:,.0f}<extra></extra>', cliponaxis=False)
        st.plotly_chart(fig_clasif_mes, use_container_width=True)

    # ----------------------------------------
    # TAB 2: COSTOS Y PRESTADORES
    # ----------------------------------------
    with tab2:
        st.header("Análisis de Costos, Precios Unitarios y Proveedores")
        
        st.subheader("Top 10 Prácticas/Insumos que más presupuesto consumen")
        df_top_costos = df.groupby(col_nomen_des)[col_precio_t].sum().reset_index().sort_values(col_precio_t, ascending=False).head(10)
        fig_top_costos = px.bar(df_top_costos, x=col_nomen_des, y=col_precio_t, text=col_precio_t,
                                labels={col_precio_t: 'Gasto Total ($)', col_nomen_des: 'Descripción'})
        fig_top_costos.update_traces(texttemplate='$%{text:,.2f}', textposition='outside', 
                                     hovertemplate='Gasto: $%{y:,.2f}<extra></extra>', cliponaxis=False)
        fig_top_costos.update_layout(yaxis_tickformat='$,.2f')
        st.plotly_chart(fig_top_costos, use_container_width=True)

        st.markdown("---")
        st.subheader("Comparativa Global de Precios entre Prestadores")
        
        practicas_comunes = df[col_nomen_des].dropna().unique()
        practica_sel = st.selectbox("Seleccioná un insumo o práctica para ver en qué centros se hace y comparar:", practicas_comunes)
        
        df_practica = df[df[col_nomen_des] == practica_sel]
        
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            df_precio_prestador = df_practica.groupby(col_razon_social)[col_precio_u].mean().reset_index().sort_values(col_precio_u)
            fig_comp_precios = px.bar(df_precio_prestador, x=col_razon_social, y=col_precio_u, text=col_precio_u,
                                      title="Precio Promedio Unitario por Centro",
                                      labels={col_razon_social: 'Centro / Prestador', col_precio_u: 'Precio Unitario Promedio ($)'},
                                      color=col_precio_u, color_continuous_scale='Reds')
            fig_comp_precios.update_traces(texttemplate='$%{text:,.2f}', textposition='outside', 
                                           hovertemplate='Precio Promedio: $%{y:,.2f}<extra></extra>', cliponaxis=False)
            fig_comp_precios.update_layout(yaxis_tickformat='$,.2f')
            st.plotly_chart(fig_comp_precios, use_container_width=True)
            
        with col_p2:
            df_precio_mes = df_practica.groupby(['Mes', col_razon_social], observed=False)[col_precio_u].mean().reset_index()
            fig_evol_precios = px.line(df_precio_mes, x='Mes', y=col_precio_u, color=col_razon_social, markers=True, text=col_precio_u,
                                       title="Evolución del Precio Unitario a lo largo de los meses")
            fig_evol_precios.update_traces(texttemplate='$%{text:,.2f}', textposition='top center', 
                                           hovertemplate='Precio Promedio: $%{y:,.2f}<extra></extra>', cliponaxis=False)
            fig_evol_precios.update_layout(yaxis_tickformat='$,.2f')
            st.plotly_chart(fig_evol_precios, use_container_width=True)

        st.markdown("---")
        st.subheader("🔍 Consulta Rápida: Precio de Práctica en un Centro Específico")
        
        col_esp1, col_esp2 = st.columns(2)
        with col_esp1:
            practica_esp = st.selectbox("1. Buscá la práctica/insumo:", practicas_comunes, key="prac_especifica")
            
        df_prac_esp_filtrada = df[df[col_nomen_des] == practica_esp]
        centros_disponibles = df_prac_esp_filtrada[col_razon_social].dropna().unique()
        
        with col_esp2:
            centro_esp = st.selectbox("2. Elegí el centro/prestador:", centros_disponibles, key="centro_especifico")
            
        df_resultado_esp = df_prac_esp_filtrada[df_prac_esp_filtrada[col_razon_social] == centro_esp]
        
        if not df_resultado_esp.empty:
            precio_prom = df_resultado_esp[col_precio_u].mean()
            precio_min = df_resultado_esp[col_precio_u].min()
            precio_max = df_resultado_esp[col_precio_u].max()
            volumen_total = df_resultado_esp[col_cant].sum()
            
            st.info(f"**Análisis de '{practica_esp}' en '{centro_esp}':**")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Precio Promedio", f"${precio_prom:,.2f}")
            m2.metric("Precio Más Bajo Registrado", f"${precio_min:,.2f}")
            m3.metric("Precio Más Alto Registrado", f"${precio_max:,.2f}")
            m4.metric("Cantidad Total Autorizada", f"{volumen_total:,.0f}")
        else:
            st.warning("No hay registros para esta combinación.")

    # ----------------------------------------
    # TAB 3: AUDITORÍA DE AFILIADOS Y DEMOGRAFÍA
    # ----------------------------------------
    with tab3:
        st.header("Análisis de Consumo por Afiliado y Zona")
        
        col_dem1, col_dem2 = st.columns(2)
        with col_dem1:
            df_zona = df.groupby(col_zona)[col_precio_t].sum().reset_index()
            fig_zona = px.pie(df_zona, values=col_precio_t, names=col_zona, title='Distribución del Gasto por Zona')
            fig_zona.update_traces(textinfo='label+percent+value', texttemplate='%{label}<br>$%{value:,.2f}',
                                   hovertemplate='Zona: %{label}<br>Gasto: $%{value:,.2f}<extra></extra>')
            st.plotly_chart(fig_zona, use_container_width=True)
            
        with col_dem2:
            st.markdown("**Top 5 Afiliados con Mayor Consumo**")
            top_afiliados = df.groupby([col_num_afiliado, col_nom_afiliado])[col_precio_t].sum().reset_index().sort_values(col_precio_t, ascending=False).head(5)
            st.dataframe(top_afiliados.style.format({col_precio_t: '${:,.2f}'}), use_container_width=True)

        st.markdown("---")
        st.subheader("🔍 Lupa sobre un Afiliado Específico")
        
        lista_afiliados = df['afiliado_display'].dropna().unique()
        afiliado_sel = st.selectbox("Escribí el NOMBRE o el NÚMERO del afiliado para buscarlo:", lista_afiliados)
        
        df_afil = df[df['afiliado_display'] == afiliado_sel]
        
        num_afil_actual = df_afil[col_num_afiliado].iloc[0]
        nom_afil_actual = df_afil[col_nom_afiliado].iloc[0]
        
        st.markdown(f"### 👤 {nom_afil_actual} (Nº {num_afil_actual})")
        st.write(f"**Gasto Total Cuatrimestral:** ${df_afil[col_precio_t].sum():,.2f}")
        
        col_af1, col_af2 = st.columns(2)
        with col_af1:
            fig_afil_comp = px.pie(df_afil, values=col_precio_t, names=col_clasif, title="Composición del Gasto")
            fig_afil_comp.update_traces(textinfo='label+percent+value', texttemplate='%{label}<br>$%{value:,.2f}',
                                        hovertemplate='Clasificación: %{label}<br>Gasto: $%{value:,.2f}<extra></extra>')
            st.plotly_chart(fig_afil_comp, use_container_width=True)
            
        with col_af2:
            df_afil_mes = df_afil.groupby('Mes', observed=False)[col_precio_t].sum().reset_index()
            fig_afil_mes = px.bar(df_afil_mes, x='Mes', y=col_precio_t, text=col_precio_t, title="Consumo en el Tiempo (Mes a Mes)")
            fig_afil_mes.update_traces(texttemplate='$%{text:,.2f}', textposition='outside', 
                                       hovertemplate='Gasto: $%{y:,.2f}<extra></extra>', cliponaxis=False)
            fig_afil_mes.update_layout(yaxis_tickformat='$,.2f')
            st.plotly_chart(fig_afil_mes, use_container_width=True)
            
        st.dataframe(df_afil[[col_fecha, col_nomen_des, col_cant, col_precio_u, col_precio_t, col_razon_social]].sort_values(col_fecha), use_container_width=True)

    # ----------------------------------------
    # TAB 4: ANÁLISIS DE SEDES Y CALIDAD DE DATOS
    # ----------------------------------------
    with tab4:
        st.header("Desempeño de Sedes y Detección de Inconsistencias")
        
        st.subheader("Volumen de Autorizaciones por Sede y Tipo")
        df_sedes = df.groupby([col_sede, col_clasif])[col_cant].sum().reset_index()
        fig_sedes = px.bar(df_sedes, x=col_sede, y=col_cant, color=col_clasif, barmode='stack', text=col_cant,
                           title="¿Qué tipo de prácticas/insumos autoriza cada sede?")
        fig_sedes.update_traces(texttemplate='%{text:,.0f}', textposition='inside',
                                hovertemplate='Cantidad: %{y:,.0f}<extra></extra>')
        st.plotly_chart(fig_sedes, use_container_width=True)
        
        st.markdown("---")
        st.subheader("⚠️ Control de Calidad: Inconsistencias en Nomenclador")
        st.markdown("Buscando códigos de nomenclador que tengan **más de una descripción asociada**...")
        
        inconsistencias = df.groupby(col_nomen_cod)[col_nomen_des].nunique().reset_index()
        codigos_problematicos = inconsistencias[inconsistencias[col_nomen_des] > 1][col_nomen_cod]
        
        if not codigos_problematicos.empty:
            st.error(f"Se encontraron {len(codigos_problematicos)} código(s) con descripciones inconsistentes.")
            df_inconsistente = df[df[col_nomen_cod].isin(codigos_problematicos)][[col_nomen_cod, col_nomen_des]].drop_duplicates().sort_values(col_nomen_cod)
            st.dataframe(df_inconsistente, use_container_width=True)
        else:
            st.success("¡Excelente! Cada código de nomenclador corresponde a una única descripción.")

else:
    st.info("👈 Subí el reporte de Excel para generar la visualización.")
