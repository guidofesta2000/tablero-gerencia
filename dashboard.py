import streamlit as st
import pandas as pd
import plotly.express as px

# Función para formatear moneda y números estilo argentino (AHORA BLINDADA)
def formato_arg(valor, es_moneda=True):
    if pd.isna(valor):
        return "0"
    try:
        valor_num = float(valor)
        if es_moneda:
            texto = f"${valor_num:,.2f}"
        else:
            texto = f"{valor_num:,.0f}"
        return texto.replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        # Si el dato está corrupto o es texto puro, lo devuelve intacto sin romper la página
        return str(valor)

st.set_page_config(page_title="Dashboard Alta Gerencia - ObSBA", layout="wide")
st.title("📊 Panel de Control Directivo - Autorizaciones ObSBA")

st.sidebar.header("Carga de Base de Datos")
st.sidebar.markdown("Subí el Excel del período a analizar.")
uploaded_file = st.sidebar.file_uploader("Archivo Excel", type=["xlsx", "xls"], key="carga_excel_main")

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    
    # 1. Limpieza inicial de columnas
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    
    # 2. Armonización de datos (Adaptación automática para bases consolidadas de Colab)
    if 'monto' in df.columns:
        df['precio_total'] = df['monto']
        
    if 'precio_total' in df.columns and 'cantidad' in df.columns:
        divisor = df['cantidad'].replace(0, 1)
        df['monto_unitario'] = df['precio_total'] / divisor

    # 3. RENOMBRAMIENTO ESTRUCTURAL DEFINITIVO
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
    
    # Prevenimos errores de concatenación si hay afiliados en blanco
    df[col_num_afiliado] = df[col_num_afiliado].fillna("Sin Datos")
    df[col_nom_afiliado] = df[col_nom_afiliado].fillna("Sin Nombre")
    df['afiliado_display'] = df[col_num_afiliado].astype(str) + " - " + df[col_nom_afiliado].astype(str)
    
    # Rellenamos sedes vacías para que no queden nulos en el gráfico
    if col_sede in df.columns:
        df[col_sede] = df[col_sede].fillna('Sin detalle de sede autorizante')

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
        col2.metric("Volumen Total (Suma Unidades)", formato_arg(df[col_cant].sum(), False))
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
            st.subheader("Volumen Global de Autorizaciones (Clasificación)")
            df_clasif = df.groupby(col_clasif)[col_cant].sum().reset_index().sort_values(col_cant, ascending=True)
            df_clasif['texto_label'] = df_clasif[col_cant].apply(lambda x: formato_arg(x, False))
            
            fig_clasif = px.bar(df_clasif, x=col_cant, y=col_clasif, orientation='h', text='texto_label')
            fig_clasif.update_traces(textposition='outside', textfont_size=13, textangle=0, hovertemplate='Cantidad: %{text}<extra></extra>', cliponaxis=False)
            fig_clasif.update_layout(separators=",.", xaxis_tickformat=",.0f", xaxis=dict(range=[0, df_clasif[col_cant].max() * 1.25]))
            st.plotly_chart(fig_clasif, use_container_width=True, key="graf_clasif_macro")

        st.markdown("---")
        st.subheader("Evolución Histórica de Autorizaciones (Operativo vs. Administrativo)")
        col_c1, col_c2 = st.columns(2)
        
        with col_c1:
            st.markdown("**Volumen Físico (Suma de unidades/insumos)**")
            df_mes_cant = df.groupby('Mes', observed=False)[col_cant].sum().reset_index()
            df_mes_cant = df_mes_cant[df_mes_cant[col_cant] > 0]
            df_mes_cant['texto_label_cant'] = df_mes_cant[col_cant].apply(lambda x: formato_arg(x, False))
            
            fig_cant = px.line(df_mes_cant, x='Mes', y=col_cant, markers=True, text='texto_label_cant')
            fig_cant.update_traces(textposition='top center', textfont_size=14, hovertemplate='Unidades: %{text}<extra></extra>', cliponaxis=False)
            fig_cant.update_layout(separators=",.", yaxis_tickformat=",.0f")
            st.plotly_chart(fig_cant, use_container_width=True, key="graf_cant_macro_linea_unidades")

        with col_c2:
            st.markdown("**Carga Administrativa (Cantidad de trámites/órdenes)**")
            df_mes_tramites = df.groupby('Mes', observed=False).size().reset_index(name='Trámites')
            df_mes_tramites = df_mes_tramites[df_mes_tramites['Trámites'] > 0]
            df_mes_tramites['texto_label_tram'] = df_mes_tramites['Trámites'].apply(lambda x: formato_arg(x, False))
            
            fig_tram = px.line(df_mes_tramites, x='Mes', y='Trámites', markers=True, text='texto_label_tram', color_discrete_sequence=['#ff9999'])
            fig_tram.update_traces(textposition='top center', textfont_size=14, hovertemplate='Trámites: %{text}<extra></extra>', cliponaxis=False)
            fig_tram.update_layout(separators=",.", yaxis_tickformat=",.0f")
            st.plotly_chart(fig_tram, use_container_width=True, key="graf_cant_macro_linea_tramites")

        # NUEVO BLOQUE: Carga Administrativa por Sede
        if col_sede in df.columns:
            st.markdown("---")
            st.subheader("🏢 Carga Administrativa por Sede Autorizadora")
            st.markdown("Cantidad total de trámites (órdenes) procesados históricamente en cada sede.")
            
            df_sedes = df.groupby(col_sede).size().reset_index(name='Trámites').sort_values('Trámites', ascending=True)
            df_sedes = df_sedes[df_sedes['Trámites'] > 0]
            df_sedes['texto_label'] = df_sedes['Trámites'].apply(lambda x: formato_arg(x, False))
            
            fig_sedes = px.bar(df_sedes, x='Trámites', y=col_sede, orientation='h', text='texto_label', color_discrete_sequence=['#4c78a8'])
            fig_sedes.update_traces(textposition='outside', textfont_size=13, textangle=0, hovertemplate='Trámites: %{text}<extra></extra>', cliponaxis=False)
            fig_sedes.update_layout(separators=",.", xaxis_tickformat=",.0f", xaxis=dict(range=[0, df_sedes['Trámites'].max() * 1.25]))
            st.plotly_chart(fig_sedes, use_container_width=True, key="graf_tramites_sede")

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
            
            st.markdown("---")
            st.subheader("🔍 Desglose Interno por Categoría")
            st.markdown("Seleccioná una clasificación para ver exactamente qué prácticas la componen.")
            
            clasificaciones_disp = df_micro[col_clasif].dropna().unique()
            clasif_sel = st.selectbox("Elegí la Clasificación a desglosar:", clasificaciones_disp, key="selector_clasif_desglose")
            
            if clasif_sel:
                df_desglose = df_micro[df_micro[col_clasif] == clasif_sel]
                df_desglose_agrupado_gasto = df_desglose.groupby(col_nomen_des)[col_precio_t].sum().reset_index().sort_values(col_precio_t, ascending=True)
                
                df_desglose_top_gasto = df_desglose_agrupado_gasto.tail(15)
                df_desglose_top_gasto['texto_label'] = df_desglose_top_gasto[col_precio_t].apply(formato_arg)
                
                fig_desglose_gasto = px.bar(df_desglose_top_gasto, x=col_precio_t, y=col_nomen_des, orientation='h', text='texto_label', 
                                      title=f"Top 15 Prácticas con Mayor Gasto en '{clasif_sel}'")
                fig_desglose_gasto.update_traces(textposition='outside', textfont_size=13, textangle=0, hovertemplate='Gasto: %{text}<extra></extra>', cliponaxis=False)
                fig_desglose_gasto.update_layout(separators=",.", xaxis_tickformat=",.0f", xaxis=dict(range=[0, df_desglose_top_gasto[col_precio_t].max() * 1.3]))
                st.plotly_chart(fig_desglose_gasto, use_container_width=True, key="graf_desglose_cat_gasto")
                
                st.markdown("**Detalle completo de todas las prácticas en esta clasificación:**")
                df_desglose_tabla = df_desglose.groupby(col_nomen_des).agg({col_cant: 'sum', col_precio_t: 'sum'}).reset_index().sort_values(col_precio_t, ascending=False)
                
                df_desglose_mostrar = df_desglose_tabla.copy()
                df_desglose_mostrar[col_cant] = df_desglose_mostrar[col_cant].apply(lambda x: formato_arg(x, False))
                df_desglose_mostrar[col_precio_t] = df_desglose_mostrar[col_precio_t].apply(formato_arg)
                st.dataframe(df_desglose_mostrar, use_container_width=True)

                st.markdown("---")
                st.subheader("🕵️️‍♂️ Trazabilidad de Afiliados por Práctica")
                st.markdown(f"Seleccioná una práctica específica dentro de **{clasif_sel}** para ver el listado exacto de afiliados y consumos.")

                practicas_en_clasif = df_desglose[col_nomen_des].dropna().unique()
                practica_drilldown = st.selectbox("Elegí la práctica a auditar:", practicas_en_clasif, key="drilldown_practica")

                if practica_drilldown:
                    df_drilldown = df_desglose[df_desglose[col_nomen_des] == practica_drilldown].copy()
                    df_drilldown_display = df_drilldown[[col_fecha, col_nomen_des, 'afiliado_display', col_cant, col_precio_t]].sort_values(col_fecha)

                    df_drilldown_display = df_drilldown_display.rename(columns={
                        col_fecha: 'Fecha',
                        col_nomen_des: 'Práctica / Insumo',
                        'afiliado_display': 'Afiliado (Nº y Nombre)',
                        col_cant: 'Cantidad',
                        col_precio_t: 'Precio Total'
                    })

                    df_drilldown_mostrar = df_drilldown_display.copy()
                    df_drilldown_mostrar['Cantidad'] = df_drilldown_mostrar['Cantidad'].apply(lambda x: formato_arg(x, False))
                    df_drilldown_mostrar['Precio Total'] = df_drilldown_mostrar['Precio Total'].apply(formato_arg)
                    df_drilldown_mostrar['Fecha'] = df_drilldown_mostrar['Fecha'].apply(lambda x: x.strftime('%d/%m/%Y') if pd.notnull(x) and hasattr(x, 'strftime') else str(x) if pd.notnull(x) else "")
                    st.dataframe(df_drilldown_mostrar, use_container_width=True)

                st.markdown("---")
                st.subheader(f"📊 Top 15 Prácticas con Mayor Frecuencia en '{clasif_sel}'")
                
                col_top1, col_top2 = st.columns(2)
                with col_top1:
                    st.markdown("**Por Volumen Físico (Suma de Unidades)**")
                    df_desglose_agrupado_cant = df_desglose.groupby(col_nomen_des)[col_cant].sum().reset_index().sort_values(col_cant, ascending=True).tail(15)
                    df_desglose_agrupado_cant['texto_label'] = df_desglose_agrupado_cant[col_cant].apply(lambda x: formato_arg(x, False))
                    fig_cant_cat = px.bar(df_desglose_agrupado_cant, x=col_cant, y=col_nomen_des, orientation='h', text='texto_label', color_discrete_sequence=['#ff9999'])
                    fig_cant_cat.update_traces(textposition='outside', textfont_size=13, textangle=0, hovertemplate='Unidades: %{text}<extra></extra>', cliponaxis=False)
                    fig_cant_cat.update_layout(separators=",.", xaxis_tickformat=",.0f", xaxis=dict(range=[0, df_desglose_agrupado_cant[col_cant].max() * 1.3]))
                    st.plotly_chart(fig_cant_cat, use_container_width=True, key="graf_desglose_cat_cant_unidades")
                    
                with col_top2:
                    st.markdown("**Por Carga Administrativa (Cantidad de Trámites)**")
                    df_desglose_agrupado_tram = df_desglose.groupby(col_nomen_des).size().reset_index(name='Trámites').sort_values('Trámites', ascending=True).tail(15)
                    df_desglose_agrupado_tram['texto_label'] = df_desglose_agrupado_tram['Trámites'].apply(lambda x: formato_arg(x, False))
                    fig_tram_cat = px.bar(df_desglose_agrupado_tram, x='Trámites', y=col_nomen_des, orientation='h', text='texto_label', color_discrete_sequence=['#ffcc99'])
                    fig_tram_cat.update_traces(textposition='outside', textfont_size=13, textangle=0, hovertemplate='Trámites: %{text}<extra></extra>', cliponaxis=False)
                    fig_tram_cat.update_layout(separators=",.", xaxis_tickformat=",.0f", xaxis=dict(range=[0, df_desglose_agrupado_tram['Trámites'].max() * 1.3]))
                    st.plotly_chart(fig_tram_cat, use_container_width=True, key="graf_desglose_cat_cant_tramites")

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
        st.subheader("⚖️ Comparativa de Mercado entre Prestadores")
        st.markdown("Compará el precio unitario promedio de una misma práctica en todos los centros que la realizan.")
        
        practicas_comunes = df[col_nomen_des].dropna().unique()
        practica_comp = st.selectbox("Seleccioná la Práctica / Insumo a analizar:", practicas_comunes, key="prac_comparativa")
        
        df_comp = df[df[col_nomen_des] == practica_comp]
        if not df_comp.empty:
            df_comp_agrupado = df_comp.groupby(col_razon_social).agg({col_precio_u: 'mean', col_cant: 'sum'}).reset_index().sort_values(col_precio_u, ascending=True)
            df_comp_agrupado['texto_label'] = df_comp_agrupado[col_precio_u].apply(formato_arg)
            
            fig_comp = px.bar(df_comp_agrupado, x=col_precio_u, y=col_razon_social, orientation='h', text='texto_label', 
                              title=f"Precio Unitario Promedio por Centro para '{practica_comp}'", color=col_precio_u, color_continuous_scale='Reds')
            fig_comp.update_traces(textposition='outside', textfont_size=13, textangle=0, hovertemplate='Precio Promedio: %{text}<br>Cantidad Total: %{customdata}', customdata=df_comp_agrupado[col_cant], cliponaxis=False)
            fig_comp.update_layout(separators=",.", xaxis_tickformat=",.0f", xaxis=dict(range=[0, df_comp_agrupado[col_precio_u].max() * 1.25]))
            st.plotly_chart(fig_comp, use_container_width=True, key="graf_comp_mercado")
            
            with st.expander("Ver tabla detallada de la comparativa"):
                df_comp_mostrar = df_comp_agrupado.sort_values(col_precio_u, ascending=False).copy()
                df_comp_mostrar[col_precio_u] = df_comp_mostrar[col_precio_u].apply(formato_arg)
                df_comp_mostrar[col_cant] = df_comp_mostrar[col_cant].apply(lambda x: formato_arg(x, False))
                st.dataframe(df_comp_mostrar, use_container_width=True)

        st.markdown("---")
        st.subheader("🔍 Consulta Rápida: Centro Específico")
        
        col_esp1, col_esp2 = st.columns(2)
        with col_esp1:
            practica_esp = st.selectbox("1. Buscá la práctica/insumo:", practicas_comunes, key="prac_especifica")
            
        df_prac_esp_filtrada = df[df[col_nomen_des] == practica_esp]
        centros_disponibles = df_prac_esp_filtrada[col_razon_social].dropna().unique()
        
        with col_esp2:
            centro_esp = st.selectbox("2. Elegí el centro proveedor:", centros_disponibles, key="centro_especifico")
            
        df_resultado_esp = df_prac_esp_filtrada[df_prac_esp_filtrada[col_razon_social] == centro_esp]
        
        if not df_resultado_esp.empty:
            st.info(f"**Resumen de '{practica_esp}' en '{centro_esp}':**")
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
        st.header("Análisis y Auditoría de Afiliados")
        
        st.subheader("🏆 Ranking de Afiliados con Mayor Consumo")
        st.markdown("Revisá el Top 50 de mayor gasto. Podés buscar y copiar el número del afiliado para analizarlo abajo.")
        
        top_afiliados = df.groupby([col_num_afiliado, col_nom_afiliado])[col_precio_t].sum().reset_index().sort_values(col_precio_t, ascending=False).head(50)
        
        top_afil_mostrar = top_afiliados.copy()
        top_afil_mostrar[col_precio_t] = top_afil_mostrar[col_precio_t].apply(formato_arg)
        st.dataframe(top_afil_mostrar, use_container_width=True)
        
        st.markdown("---")
        
        st.subheader("🔍 Lupa sobre un Afiliado Específico")
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
            
            df_afil_mostrar = df_afil_display.copy()
            df_afil_mostrar['Precio Unitario'] = df_afil_mostrar['Precio Unitario'].apply(formato_arg)
            df_afil_mostrar['Precio Total'] = df_afil_mostrar['Precio Total'].apply(formato_arg)
            df_afil_mostrar['Fecha'] = df_afil_mostrar['Fecha'].apply(lambda x: x.strftime('%d/%m/%Y') if pd.notnull(x) and hasattr(x, 'strftime') else str(x) if pd.notnull(x) else "")
            st.dataframe(df_afil_mostrar, use_container_width=True)

    # ----------------------------------------
    # TAB 5: CALIDAD Y DUPLICADOS (PREVENCIÓN DE FRAUDE)
    # ----------------------------------------
    with tab5:
        st.header("Auditoría de Duplicados y Control de Nomenclador")
        
        st.subheader("🚨 Detección de Prácticas Múltiples (Mismo Afiliado, Misma Fecha, Misma Práctica)")
        
        df_duplicados = df[df.duplicated(subset=[col_fecha, col_num_afiliado, col_nomen_des], keep=False)].copy()
        
        if not df_duplicados.empty:
            df_duplicados = df_duplicados.sort_values(by=[col_fecha, col_num_afiliado])
            
            monto_riesgo = df_duplicados[col_precio_t].sum()
            volumen_riesgo = df_duplicados[col_cant].sum()
            casos_unicos = df_duplicados.groupby([col_fecha, col_num_afiliado, col_nomen_des]).ngroups
            
            kpi1, kpi2, kpi3 = st.columns(3)
            kpi1.metric("Casos Potenciales Detectados", formato_arg(casos_unicos, False))
            kpi2.metric("Monto Total Bajo Auditoría", formato_arg(monto_riesgo))
            kpi3.metric("Volumen Extra Involucrado", formato_arg(volumen_riesgo, False))
            
            st.markdown("---")
            
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
                
            df_tabla_dup = df_duplicados.copy()
            if filtro_prov != "Todos":
                df_tabla_dup = df_tabla_dup[df_tabla_dup[col_razon_social] == filtro_prov]
            if filtro_prac != "Todas":
                df_tabla_dup = df_tabla_dup[df_tabla_dup[col_nomen_des] == filtro_prac]
            if filtro_afil != "Todos":
                df_tabla_dup = df_tabla_dup[df_tabla_dup['afiliado_display'] == filtro_afil]

            df_tabla_dup_display = df_tabla_dup[[col_fecha, col_num_afiliado, col_nom_afiliado, col_nomen_des, col_cant, col_precio_t, col_razon_social]]
            
            df_tabla_dup_mostrar = df_tabla_dup_display.copy()
            df_tabla_dup_mostrar['Precio Total'] = df_tabla_dup_mostrar['Precio Total'].apply(formato_arg)
            df_tabla_dup_mostrar['Fecha'] = df_tabla_dup_mostrar['Fecha'].apply(lambda x: x.strftime('%d/%m/%Y') if pd.notnull(x) and hasattr(x, 'strftime') else str(x) if pd.notnull(x) else "")
            st.dataframe(df_tabla_dup_mostrar, use_container_width=True)
            
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
    st.info("👈 Subí el reporte de Excel consolidado (BASE_BI) para generar la visualización.")
