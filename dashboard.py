import streamlit as st
import pandas as pd
import plotly.express as px

# Función para formatear moneda y números estilo argentino
def formato_arg(valor, es_moneda=True):
    if pd.isna(valor):
        return "0"
    if es_moneda:
        texto = f"${valor:,.2f}"
    else:
        texto = f"{valor:,.0f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")

st.set_page_config(page_title="Dashboard Alta Gerencia - ObSBA", layout="wide")
st.title("📊 Panel de Control Directivo - Autorizaciones ObSBA")

st.sidebar.header("Carga de Base de Datos")
st.sidebar.markdown("Subí el Excel del período a analizar.")
uploaded_file = st.sidebar.file_uploader("Archivo Excel", type=["xlsx", "xls"], key="carga_excel")

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    
    # 1. Limpieza inicial
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    
    # 2. RENOMBRAMIENTO ESTRUCTURAL
    mapa_nombres = {
        'fecha': 'Fecha',
        'nomen_cod': 'Código',
        'nomen_des': 'Práctica / Insumo',
        'clasificacion': 'Clasificación',
        'cantidad': 'Cantidad',
        'monto_unitario': 'Precio Unitario',
        'precio_total': 'Precio Total',
        'razonsocia': 'Centro Proveedor',
        'afiliado': 'Nº Afiliado',
        'nombre': 'Nombre Afiliado',
        'zona': 'Zona',
        'sedes': 'Centro Autorizador'
    }
    mapa_nombres_presentes = {k: v for k, v in mapa_nombres.items() if k in df.columns}
    df.rename(columns=mapa_nombres_presentes, inplace=True)
    
    # Variables de columnas formales
    col_fecha = 'Fecha'
    col_cant = 'Cantidad'
    col_precio_u = 'Precio Unitario'
    col_precio_t = 'Precio Total'
    col_nomen_cod = 'Código'
    col_nomen_des = 'Práctica / Insumo'
    col_clasif = 'Clasificación'
    col_razon_social = 'Centro Proveedor'
    col_num_afiliado = 'Nº Afiliado'
    col_nom_afiliado = 'Nombre Afiliado'
    col_zona = 'Zona'
    col_sede = 'Centro Autorizador'

    # Tratamiento de fechas
    df[col_fecha] = pd.to_datetime(df[col_fecha], errors='coerce')
    df['Mes_Num'] = df[col_fecha].dt.month
    
    meses_map = {1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio', 
                 7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'}
    df['Mes'] = df['Mes_Num'].map(meses_map)
    
    orden_meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    df['Mes'] = pd.Categorical(df['Mes'], categories=orden_meses, ordered=True)
    df['afiliado_display'] = df[col_num_afiliado].astype(str) + " - " + df[col_nom_afiliado].astype(str)

    # Creamos las 5 pestañas
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 1. Resumen Ejecutivo (Macro)", 
        "📅 2. Análisis Mensual (Micro)",
        "🏥 3. Costos y Prestadores", 
        "👤 4. Auditoría de Afiliados",
        "🚨 5. Calidad y Duplicados"
    ])

    # ----------------------------------------
    # TAB 1: RESUMEN EJECUTIVO (MACRO TOTAL)
    # ----------------------------------------
    with tab1:
        st.header("Visión Global del Período Completo")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Facturación Total", formato_arg(df[col_precio_t].sum()))
        col2.metric("Volumen Total (Cantidades)", formato_arg(df[col_cant].sum(), False))
        col3.metric("Afiliados Atendidos", formato_arg(df[col_num_afiliado].nunique(), False))
        col4.metric("Total de Prestadores", formato_arg(df[col_razon_social].nunique(), False))
        
        st.markdown("---")
        col_t1, col_t2 = st.columns(2)
        
        with col_t1:
            st.subheader("Evolución Histórica de Facturación")
            df_mes_fact = df.groupby('Mes', observed=False)[col_precio_t].sum().reset_index()
            df_mes_fact = df_mes_fact[df_mes_fact[col_precio_t] > 0] 
            
            df_mes_fact['texto_label'] = df_mes_fact[col_precio_t].apply(formato_arg)
            fig_fact = px.line(df_mes_fact, x='Mes', y=col_precio_t, markers=True, text='texto_label')
            fig_fact.update_traces(textposition='top center', textfont_size=14, hovertemplate='Gasto: %{text}<extra></extra>', cliponaxis=False)
            fig_fact.update_layout(separators=",.", yaxis_tickformat=",.0f")
            st.plotly_chart(fig_fact, use_container_width=True, key="graf_fact_macro")
            
        with col_t2:
            st.subheader("Volumen Global de Autorizaciones")
            df_clasif = df.groupby(col_clasif)[col_cant].sum().reset_index().sort_values(col_cant, ascending=True)
            df_clasif['texto_label'] = df_clasif[col_cant].apply(lambda x: formato_arg(x, False))
            
            fig_clasif = px.bar(df_clasif, x=col_cant, y=col_clasif, orientation='h', text='texto_label')
            fig_clasif.update_traces(textposition='outside', textfont_size=13, textangle=0, hovertemplate='Cantidad: %{text}<extra></extra>', cliponaxis=False)
            fig_clasif.update_layout(separators=",.", xaxis_tickformat=",.0f", xaxis=dict(range=[0, df_clasif[col_cant].max() * 1.25]))
            st.plotly_chart(fig_clasif, use_container_width=True, key="graf_clasif_macro")

    # ----------------------------------------
    # TAB 2: ANÁLISIS MENSUAL (MICRO INTERACTIVO)
    # ----------------------------------------
    with tab2:
        st.header("Análisis de Volumen por Meses Específicos")
        st.markdown("Seleccioná los meses que deseás analizar para evitar saturación visual en los gráficos.")
        
        meses_presentes = [m for m in orden_meses if m in df['Mes'].dropna().unique()]
        meses_seleccionados = st.multiselect("Filtro de Meses:", options=meses_presentes, default=meses_presentes, key="filtro_meses_micro")
        
        if meses_seleccionados:
            df_micro = df[df['Mes'].isin(meses_seleccionados)]
            
            st.subheader("Comparativa de Volumen Entre Meses Seleccionados")
            df_clasif_mes = df_micro.groupby(['Mes', col_clasif], observed=False)[col_cant].sum().reset_index()
            df_clasif_mes = df_clasif_mes[df_clasif_mes[col_cant] > 0]
            df_clasif_mes['texto_label'] = df_clasif_mes[col_cant].apply(lambda x: formato_arg(x, False))
            
            fig_clasif_mes = px.bar(df_clasif_mes, x='Mes', y=col_cant, color=col_clasif, barmode='group', text='texto_label')
            fig_clasif_mes.update_traces(textposition='outside', textfont_size=13, textangle=0, hovertemplate='Cantidad: %{text}<extra></extra>', cliponaxis=False)
            fig_clasif_mes.update_layout(separators=",.", yaxis_tickformat=",.0f", yaxis=dict(range=[0, df_clasif_mes[col_cant].max() * 1.15]))
            st.plotly_chart(fig_clasif_mes, use_container_width=True, key="graf_comparativa_meses")
            
            st.subheader("Volumen Consolidado (Solo Meses Seleccionados)")
            df_clasif_micro = df_micro.groupby(col_clasif)[col_cant].sum().reset_index().sort_values(col_cant, ascending=True)
            df_clasif_micro['texto_label'] = df_clasif_micro[col_cant].apply(lambda x: formato_arg(x, False))
            
            fig_clasif_micro = px.bar(df_clasif_micro, x=col_cant, y=col_clasif, orientation='h', text='texto_label')
            fig_clasif_micro.update_traces(textposition='outside', textfont_size=13, textangle=0, hovertemplate='Cantidad: %{text}<extra></extra>', cliponaxis=False)
            fig_clasif_micro.update_layout(separators=",.", xaxis_tickformat=",.0f", xaxis=dict(range=[0, df_clasif_micro[col_cant].max() * 1.25]))
            st.plotly_chart(fig_clasif_micro, use_container_width=True, key="graf_clasif_micro")
        else:
            st.info("Seleccioná al menos un mes para visualizar los gráficos.")

    # ----------------------------------------
    # TAB 3: COSTOS Y PRESTADORES
    # ----------------------------------------
    with tab3:
        st.header("Análisis de Costos y Proveedores")
        
        st.subheader("Top 10 Prácticas que más presupuesto consumen")
        df_top_costos = df.groupby(col_nomen_des)[col_precio_t].sum().reset_index().sort_values(col_precio_t, ascending=True).tail(10)
        df_top_costos['texto_label'] = df_top_costos[col_precio_t].apply(formato_arg)
        
        fig_top_costos = px.bar(df_top_costos, x=col_precio_t, y=col_nomen_des, orientation='h', text='texto_label')
        fig_top_costos.update_traces(textposition='outside', textfont_size=13, textangle=0, hovertemplate='Gasto: %{text}<extra></extra>', cliponaxis=False)
        fig_top_costos.update_layout(separators=",.", xaxis_tickformat=",.0f", xaxis=dict(range=[0, df_top_costos[col_precio_t].max() * 1.3]))
        st.plotly_chart(fig_top_costos, use_container_width=True, key="graf_top_costos")

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
    # TAB 4: AUDITORÍA DE AFILIADOS
    # ----------------------------------------
    with tab4:
        st.header("Análisis de Consumo por Afiliado")
        
        lista_afiliados = df['afiliado_display'].dropna().unique()
        
        if len(lista_afiliados) > 0:
            afiliado_sel = st.selectbox("Escribí el NOMBRE o el NÚMERO del afiliado para buscarlo:", lista_afiliados, key="afiliado_buscador")
            
            df_afil = df[df['afiliado_display'] == afiliado_sel]
            nom_afil_actual = df_afil[col_nom_afiliado].iloc[0]
            num_afil_actual = df_afil[col_num_afiliado].iloc[0]
            
            st.markdown(f"### 👤 {nom_afil_actual} (Nº {num_afil_actual})")
            st.write(f"**Gasto Total Registrado:** {formato_arg(df_afil[col_precio_t].sum())}")
            
            col_af1, col_af2 = st.columns(2)
            with col_af1:
                fig_afil_comp = px.pie(df_afil, values=col_precio_t, names=col_clasif, title="Composición del Gasto")
                fig_afil_comp.update_traces(textinfo='label+percent', hovertemplate='Clasificación: %{label}<br>Gasto representativo<extra></extra>')
                fig_afil_comp.update_layout(separators=",.")
                st.plotly_chart(fig_afil_comp, use_container_width=True, key="graf_pie_afil")
                
            with col_af2:
                df_afil_mes = df_afil.groupby('Mes', observed=False)[col_precio_t].sum().reset_index()
                df_afil_mes = df_afil_mes[df_afil_mes[col_precio_t] > 0]
                df_afil_mes['texto_label'] = df_afil_mes[col_precio_t].apply(formato_arg)
                
                fig_afil_mes = px.bar(df_afil_mes, x='Mes', y=col_precio_t, text='texto_label', title="Consumo en el Tiempo")
                fig_afil_mes.update_traces(textposition='outside', textfont_size=13, textangle=0, hovertemplate='Gasto: %{text}<extra></extra>', cliponaxis=False)
                fig_afil_mes.update_layout(separators=",.", yaxis_tickformat=",.0f", yaxis=dict(range=[0, df_afil_mes[col_precio_t].max() * 1.3]))
                st.plotly_chart(fig_afil_mes, use_container_width=True, key="graf_bar_afil")
                
            st.subheader("Historial de Consumos del Afiliado")
            df_afil_display = df_afil[[col_fecha, col_nomen_des, col_cant, col_precio_u, col_precio_t, col_razon_social, col_sede]].sort_values(col_fecha)
            
            st.dataframe(df_afil_display.style.format({
                "Precio Unitario": lambda x: formato_arg(x),
                "Precio Total": lambda x: formato_arg(x),
                "Fecha": lambda x: x.strftime('%d/%m/%Y') if pd.notnull(x) else ""
            }), use_container_width=True)

    # ----------------------------------------
    # TAB 5: CALIDAD Y DUPLICADOS (PREVENCIÓN DE FRAUDE)
    # ----------------------------------------
    with tab5:
        st.header("Auditoría de Duplicados y Control de Nomenclador")
        
        st.subheader("🚨 Detección de Prácticas Múltiples (Mismo Afiliado, Misma Fecha, Misma Práctica)")
        
        # Filtramos los duplicados exactos
        df_duplicados = df[df.duplicated(subset=[col_fecha, col_num_afiliado, col_nomen_des], keep=False)].copy()
        
        if not df_duplicados.empty:
            df_duplicados = df_duplicados.sort_values(by=[col_fecha, col_num_afiliado])
            
            # KPIs de Impacto Financiero
            monto_riesgo = df_duplicados[col_precio_t].sum()
            volumen_riesgo = df_duplicados[col_cant].sum()
            casos_unicos = df_duplicados.groupby([col_fecha, col_num_afiliado, col_nomen_des]).ngroups
            
            kpi1, kpi2, kpi3 = st.columns(3)
            kpi1.metric("Casos Potenciales Detectados", formato_arg(casos_unicos, False))
            kpi2.metric("Monto Total Bajo Auditoría", formato_arg(monto_riesgo))
            kpi3.metric("Volumen Extra Involucrado", formato_arg(volumen_riesgo, False))
            
            st.markdown("---")
            
            # Gráficos Analíticos de Fraude
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                st.markdown("**Top Centros Proveedores con Duplicados**")
                df_dup_prov = df_duplicados.groupby(col_razon_social)[col_precio_t].sum().reset_index().sort_values(col_precio_t, ascending=True).tail(10)
                df_dup_prov['texto_label'] = df_dup_prov[col_precio_t].apply(formato_arg)
                fig_dup_prov = px.bar(df_dup_prov, x=col_precio_t, y=col_razon_social, orientation='h', text='texto_label')
                fig_dup_prov.update_traces(textposition='outside', textfont_size=13, textangle=0, cliponaxis=False)
                fig_dup_prov.update_layout(separators=",.", xaxis_tickformat=",.0f", xaxis=dict(range=[0, df_dup_prov[col_precio_t].max() * 1.3]), margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig_dup_prov, use_container_width=True, key="graf_dup_prov")
                
            with col_g2:
                st.markdown("**Top Prácticas más Duplicadas**")
                df_dup_prac = df_duplicados.groupby(col_nomen_des)[col_cant].sum().reset_index().sort_values(col_cant, ascending=True).tail(10)
                df_dup_prac['texto_label'] = df_dup_prac[col_cant].apply(lambda x: formato_arg(x, False))
                fig_dup_prac = px.bar(df_dup_prac, x=col_cant, y=col_nomen_des, orientation='h', text='texto_label')
                fig_dup_prac.update_traces(textposition='outside', textfont_size=13, textangle=0, cliponaxis=False)
                fig_dup_prac.update_layout(separators=",.", xaxis_tickformat=",.0f", xaxis=dict(range=[0, df_dup_prac[col_cant].max() * 1.3]), margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig_dup_prac, use_container_width=True, key="graf_dup_prac")

            st.markdown("**Ranking de Afiliados Bajo Sospecha (Mayor cantidad de repeticiones)**")
            df_dup_afil = df_duplicados.groupby([col_num_afiliado, col_nom_afiliado]).size().reset_index(name='Cantidad de Registros Duplicados')
            df_dup_afil = df_dup_afil.sort_values(by='Cantidad de Registros Duplicados', ascending=False).head(5)
            st.dataframe(df_dup_afil, use_container_width=True)

            st.markdown("---")
            st.subheader("Buscador Interactivo de Duplicados")
            
            # Filtros desplegables
            f1, f2, f3 = st.columns(3)
            with f1:
                opciones_prov = ["Todos"] + list(df_duplicados[col_razon_social].dropna().unique())
                filtro_prov = st.selectbox("Filtrar por Centro Proveedor:", opciones_prov, key="filtro_prov")
            with f2:
                opciones_prac = ["Todas"] + list(df_duplicados[col_nomen_des].dropna().unique())
                filtro_prac = st.selectbox("Filtrar por Práctica:", opciones_prac, key="filtro_prac")
            with f3:
                opciones_afil = ["Todos"] + list(df_duplicados['afiliado_display'].dropna().unique())
                filtro_afil = st.selectbox("Filtrar por Afiliado:", opciones_afil, key="filtro_afil")
                
            # Aplicar filtros a la tabla
            df_tabla_dup = df_duplicados.copy()
            if filtro_prov != "Todos":
                df_tabla_dup = df_tabla_dup[df_tabla_dup[col_razon_social] == filtro_prov]
            if filtro_prac != "Todas":
                df_tabla_dup = df_tabla_dup[df_tabla_dup[col_nomen_des] == filtro_prac]
            if filtro_afil != "Todos":
                df_tabla_dup = df_tabla_dup[df_tabla_dup['afiliado_display'] == filtro_afil]

            df_tabla_dup_display = df_tabla_dup[[col_fecha, col_num_afiliado, col_nom_afiliado, col_nomen_des, col_cant, col_precio_t, col_razon_social]]
            st.dataframe(df_tabla_dup_display.style.format({
                "Precio Total": lambda x: formato_arg(x),
                "Fecha": lambda x: x.strftime('%d/%m/%Y') if pd.notnull(x) else ""
            }), use_container_width=True)
            
        else:
            st.success("¡Excelente! No se detectaron autorizaciones duplicadas.")

        st.markdown("---")
        st.subheader("⚠️ Inconsistencias en el Nomenclador")
        
        inconsistencias = df.groupby(col_nomen_cod)[col_nomen_des].nunique().reset_index()
        codigos_problematicos = inconsistencias[inconsistencias[col_nomen_des] > 1][col_nomen_cod]
        
        if not codigos_problematicos.empty:
            st.warning(f"Se encontraron {len(codigos_problematicos)} códigos con descripciones múltiples.")
            df_inconsistente = df[df[col_nomen_cod].isin(codigos_problematicos)][[col_nomen_cod, col_nomen_des]].drop_duplicates().sort_values(col_nomen_cod)
            st.dataframe(df_inconsistente, use_container_width=True)
        else:
            st.success("El nomenclador está limpio. Un código = Una descripción.")

else:
    st.info("👈 Subí el reporte de Excel para generar la visualización.")
