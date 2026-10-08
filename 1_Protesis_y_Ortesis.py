import streamlit as st
import pandas as pd
import plotly.express as px

# Función para formatear moneda y números
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
        return str(valor)

# Función maestra a prueba de fallos PyArrow
def mostrar_tabla_segura(df, cols_moneda=None, cols_cantidad=None, cols_fecha=None):
    if df.empty:
        st.dataframe(df, use_container_width=True)
        return
        
    df_safe = df.copy().reset_index(drop=True)
    
    if cols_fecha:
        for c in cols_fecha:
            if c in df_safe.columns:
                df_safe[c] = pd.to_datetime(df_safe[c], errors='coerce').dt.strftime('%d/%m/%Y').fillna("")
                
    formato = {}
    if cols_moneda:
        for c in cols_moneda:
            if c in df_safe.columns:
                formato[c] = lambda x: formato_arg(x, True)
    if cols_cantidad:
        for c in cols_cantidad:
            if c in df_safe.columns:
                formato[c] = lambda x: formato_arg(x, False)
                
    try:
        if formato:
            st.dataframe(df_safe.style.format(formato), use_container_width=True)
        else:
            st.dataframe(df_safe, use_container_width=True)
    except Exception:
        st.dataframe(df_safe, use_container_width=True)

st.set_page_config(page_title="Auditoría de Prótesis y Órtesis", layout="wide")
st.title("🦴 Tablero Específico: Prótesis y Órtesis")

st.sidebar.header("Carga de Base de Datos")
st.sidebar.markdown("Subí el mismo Excel consolidado (BASE_BI).")
uploaded_file = st.sidebar.file_uploader("Archivo Excel", type=["xlsx", "xls"], key="carga_excel_protesis")

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    
    # 1. Limpieza y Armonización
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    
    if 'monto' in df.columns:
        df['precio_total'] = df['monto']
        
    if 'precio_total' in df.columns and 'cantidad' in df.columns:
        divisor = df['cantidad'].replace(0, 1)
        df['monto_unitario'] = df['precio_total'] / divisor

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
    
    # Tratamiento de fechas
    df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
    df['Mes_Num'] = df['Fecha'].dt.month
    meses_map = {1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio', 
                 7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'}
    df['Mes'] = df['Mes_Num'].map(meses_map)
    orden_meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    df['Mes'] = pd.Categorical(df['Mes'], categories=orden_meses, ordered=True)
    
    df['Nº Afiliado'] = df['Nº Afiliado'].fillna("Sin Datos")
    df['Nombre Afiliado'] = df['Nombre Afiliado'].fillna("Sin Nombre")
    df['afiliado_display'] = df['Nº Afiliado'].astype(str) + " - " + df['Nombre Afiliado'].astype(str)

    # ---------------------------------------------------------
    # AISLAMIENTO DE LA CATEGORÍA Y FILTRO "SIN INSUMOS"
    # ---------------------------------------------------------
    st.sidebar.markdown("---")
    st.sidebar.header("Filtro de Limpieza")
    st.sidebar.markdown("El sistema elimina automáticamente descripciones que contengan estas palabras para limpiar los insumos de la lista de prótesis:")
    
    # Palabras clave por defecto para eliminar insumos
    palabras_defecto = "DESCARTABLE, SONDA, BOLSA, APOSITO, AGUJA, CATETER, JERINGA, GUIA, BALON, CINTURON, ALGODON, VENDAS, GASAS, PILAS, PASTA"
    excluir_input = st.sidebar.text_area("Palabras a excluir (separadas por coma):", palabras_defecto).upper()
    
    # Filtramos primero la categoría macro
    if 'Clasificación' in df.columns:
        df_protesis = df[df['Clasificación'] == 'Insumos, Prótesis y Órtesis'].copy()
    else:
        df_protesis = df.copy() # Por si suben una base ya pre-filtrada

    # Aplicamos la exclusión de palabras
    if excluir_input:
        lista_excluir = [p.strip() for p in excluir_input.split(",") if p.strip()]
        for palabra in lista_excluir:
            df_protesis = df_protesis[~df_protesis['Práctica / Insumo'].str.upper().str.contains(palabra, na=False)]

    # Filtro manual final por si quedó algo colado
    practicas_limpias = sorted(df_protesis['Práctica / Insumo'].dropna().unique())
    seleccion_manual = st.sidebar.multiselect("Filtrar o revisar ítems específicos (Vacío = Muestra todos):", practicas_limpias)
    
    if seleccion_manual:
        df_protesis = df_protesis[df_protesis['Práctica / Insumo'].isin(seleccion_manual)]

    if df_protesis.empty:
        st.warning("No hay datos para mostrar con los filtros actuales. Revisá las palabras excluidas.")
    else:
        # ---------------------------------------------------------
        # KPI: CANTIDAD TOTAL DEL PERÍODO
        # ---------------------------------------------------------
        st.header("1. Resumen Global del Período")
        k1, k2, k3 = st.columns(3)
        k1.metric("Gasto Total en Prótesis/Órtesis", formato_arg(df_protesis['Precio Total'].sum()))
        k2.metric("Volumen Físico (Unidades)", formato_arg(df_protesis['Cantidad'].sum(), False))
        k3.metric("Proveedores Involucrados", formato_arg(df_protesis['Centro Proveedor'].nunique(), False))

        st.markdown("---")

        # ---------------------------------------------------------
        # GRÁFICO: CANTIDAD TOTAL MES A MES
        # ---------------------------------------------------------
        st.header("2. Evolución Mes a Mes")
        col_m1, col_m2 = st.columns(2)
        
        with col_m1:
            st.subheader("Gasto Mensual Facturado")
            df_mes = df_protesis.groupby('Mes', observed=False)['Precio Total'].sum().reset_index()
            df_mes = df_mes[df_mes['Precio Total'] > 0]
            df_mes['label'] = df_mes['Precio Total'].apply(formato_arg)
            
            fig_mes_plata = px.line(df_mes, x='Mes', y='Precio Total', markers=True, text='label')
            fig_mes_plata.update_traces(textposition='top center', textfont_size=13, cliponaxis=False)
            fig_mes_plata.update_layout(separators=",.", yaxis_tickformat=",.0f")
            st.plotly_chart(fig_mes_plata, use_container_width=True)

        with col_m2:
            st.subheader("Volumen de Unidades Mensual")
            df_mes_cant = df_protesis.groupby('Mes', observed=False)['Cantidad'].sum().reset_index()
            df_mes_cant = df_mes_cant[df_mes_cant['Cantidad'] > 0]
            df_mes_cant['label'] = df_mes_cant['Cantidad'].apply(lambda x: formato_arg(x, False))
            
            fig_mes_cant = px.bar(df_mes_cant, x='Mes', y='Cantidad', text='label', color_discrete_sequence=['#ff9999'])
            fig_mes_cant.update_traces(textposition='outside', textfont_size=13, cliponaxis=False)
            fig_mes_cant.update_layout(separators=",.", yaxis_tickformat=",.0f")
            st.plotly_chart(fig_mes_cant, use_container_width=True)

        st.markdown("---")

        # ---------------------------------------------------------
        # ANÁLISIS: CANTIDAD TOTAL FACTURADA POR INSUMO/PRÓTESIS
        # ---------------------------------------------------------
        st.header("3. Total Facturado por Prótesis / Órtesis")
        st.markdown("Ranking de los ítems que mayor presupuesto consumieron en el período.")
        
        df_items = df_protesis.groupby('Práctica / Insumo').agg(
            Gasto_Total=('Precio Total', 'sum'),
            Unidades=('Cantidad', 'sum')
        ).reset_index().sort_values('Gasto_Total', ascending=False)
        
        # Gráfico Top 15 Ítems
        df_items_top = df_items.head(15).sort_values('Gasto_Total', ascending=True)
        df_items_top['label'] = df_items_top['Gasto_Total'].apply(formato_arg)
        
        fig_items = px.bar(df_items_top, x='Gasto_Total', y='Práctica / Insumo', orientation='h', text='label', title="Top 15 Prótesis más Costosas")
        fig_items.update_traces(textposition='outside', textfont_size=13, cliponaxis=False)
        fig_items.update_layout(separators=",.", xaxis_tickformat=",.0f", xaxis=dict(range=[0, df_items_top['Gasto_Total'].max() * 1.3]))
        st.plotly_chart(fig_items, use_container_width=True)

        # Tabla Completa de Ítems
        with st.expander("Ver detalle completo de todos los ítems facturados"):
            mostrar_tabla_segura(df_items, cols_moneda=['Gasto_Total'], cols_cantidad=['Unidades'])

        st.markdown("---")

        # ---------------------------------------------------------
        # ANÁLISIS: EMPRESAS Y PROVEEDORES
        # ---------------------------------------------------------
        st.header("4. Autorizaciones por Empresa / Proveedor")
        st.markdown("Distribución del gasto según a qué empresa se le autorizó la provisión.")
        
        df_empresas = df_protesis.groupby('Centro Proveedor').agg(
            Gasto_Total=('Precio Total', 'sum'),
            Unidades=('Cantidad', 'sum')
        ).reset_index().sort_values('Gasto_Total', ascending=False)

        col_e1, col_e2 = st.columns([1, 1])
        with col_e1:
            df_empresas_top = df_empresas.head(10).sort_values('Gasto_Total', ascending=True)
            df_empresas_top['label'] = df_empresas_top['Gasto_Total'].apply(formato_arg)
            fig_empresas = px.bar(df_empresas_top, x='Gasto_Total', y='Centro Proveedor', orientation='h', text='label', color_discrete_sequence=['#4c78a8'])
            fig_empresas.update_traces(textposition='outside', textfont_size=13, cliponaxis=False)
            fig_empresas.update_layout(separators=",.", xaxis_tickformat=",.0f", xaxis=dict(range=[0, df_empresas_top['Gasto_Total'].max() * 1.3]))
            st.plotly_chart(fig_empresas, use_container_width=True)
            
        with col_e2:
            st.markdown("**Listado Completo por Empresa**")
            mostrar_tabla_segura(df_empresas, cols_moneda=['Gasto_Total'], cols_cantidad=['Unidades'])

        st.markdown("---")

        # ---------------------------------------------------------
        # TRAZABILIDAD (REGISTRO CRUDO)
        # ---------------------------------------------------------
        st.header("5. Trazabilidad de Autorizaciones")
        st.markdown("Detalle registro por registro de la base filtrada (podés usar los buscadores de columna si necesitas exportarlo).")
        
        columnas_mostrar = ['Fecha', 'Práctica / Insumo', 'Cantidad', 'Precio Unitario', 'Precio Total', 'Centro Proveedor', 'afiliado_display']
        df_trazabilidad = df_protesis[columnas_mostrar].sort_values('Fecha', ascending=False)
        df_trazabilidad = df_trazabilidad.rename(columns={'afiliado_display': 'Afiliado'})
        
        mostrar_tabla_segura(df_trazabilidad, cols_moneda=['Precio Unitario', 'Precio Total'], cols_cantidad=['Cantidad'], cols_fecha=['Fecha'])

else:
    st.info("👈 Subí el reporte de Excel consolidado (BASE_BI) en el panel izquierdo para generar la visualización de Prótesis.")
