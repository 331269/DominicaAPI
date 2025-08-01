import os
import tempfile
import pandas as pd
import streamlit as st
from settings import subrecetas, ubicaciones
from calculadora.calcular_ingredientes import calcular_ingredientes

# ---------- Helpers ----------

def construir_df_producto(subreceta_name: str, cantidad: int) -> pd.DataFrame:
    ingredientes = calcular_ingredientes(subreceta_name, cantidad)
    df = pd.DataFrame(
        list(ingredientes.items()),
        columns=["Ingrediente", "Cantidad"]
    )
    df["Clave_subreceta"] = subrecetas[subreceta_name]
    df["Subreceta"] = subreceta_name
    df["Cantidad_ensamblada"] = cantidad
    return df

def guardar_csv_atomico(df: pd.DataFrame, filename: str) -> None:
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    file_exists = os.path.isfile(filename)

    # Escribir en temporal
    dirpath = os.path.dirname(filename) or "."
    with tempfile.NamedTemporaryFile("w", delete=False, dir=dirpath, suffix=".csv", encoding="utf-8", newline="") as tmp:
        df.to_csv(
            tmp.name,
            mode="w",
            header=not file_exists,
            index=False
        )
        tmp_path = tmp.name

    if file_exists:
        # Append sin duplicar header
        with open(filename, "a", encoding="utf-8", newline="") as orig, open(tmp_path, "r", encoding="utf-8") as tmpf:
            lines = tmpf.readlines()
            if len(lines) > 1:
                orig.writelines(lines[1:])  # saltar header
        os.remove(tmp_path)
    else:
        os.replace(tmp_path, filename)

def subir_csv_a_sharepoint(local_path: str, carpeta_remote: str):
    """
    Placeholder: aquí implementas la integración real con SharePoint/Graph API.
    Por ahora simula éxito.
    """
    pass  # simula que funcionó

# ---------- Inicializar estado ----------

st.set_page_config(page_title="Demo Subrecetas", layout="wide")

if "productos_agregados" not in st.session_state:
    st.session_state.productos_agregados = []

st.title("📦 Registro de Subrecetas - Demo")
logo_path = os.path.join(os.path.dirname(__file__), "..", "dominica_logo_demo.jpg")
st.image(logo_path, width=180)

# ---------- Selección de ubicación primero ----------

with st.expander("0. Seleccionar ubicación de pertenencia", expanded=True):
    codigo_ubicacion = st.selectbox("Código de ubicación", options=list(ubicaciones.keys()))
    sucursal = ubicaciones[codigo_ubicacion]
    st.success(f"Ubicación seleccionada: **{sucursal}**")

# ---------- Selección de subreceta y cantidad ----------

with st.expander("1. Seleccionar subreceta y cantidad"):
    seleccionar_subreceta = st.selectbox(
        "Elige un producto:", options=list(subrecetas.keys())
    )
    st.write(f"Código del producto: `{subrecetas[seleccionar_subreceta]}`")

    cantidad_ensamblar = st.number_input(
        "Cantidad a ensamblar", min_value=0, max_value=100, format="%i"
    )

    if cantidad_ensamblar > 0:
        df_ingredientes = construir_df_producto(seleccionar_subreceta, cantidad_ensamblar)
        st.subheader("📝 Ingredientes calculados")
        st.dataframe(df_ingredientes[["Ingrediente", "Cantidad"]], use_container_width=True)
    else:
        st.info("Ingresa una cantidad mayor a 0 para ver ingredientes.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Agregar al buffer", disabled=cantidad_ensamblar <= 0):
            if cantidad_ensamblar <= 0:
                st.error("La cantidad debe ser mayor a 0 para agregar.")
            else:
                df_prod = construir_df_producto(seleccionar_subreceta, cantidad_ensamblar)
                st.session_state.productos_agregados.append(df_prod)
                st.success("Producto agregado al buffer.")
    with col2:
        if st.button("Deshacer último agregado"):
            if st.session_state.productos_agregados:
                removed = st.session_state.productos_agregados.pop()
                st.warning(f"Se removió: {removed.iloc[0]['Subreceta']} x{removed.iloc[0]['Cantidad_ensamblada']}")
            else:
                st.info("No hay nada que deshacer.")

# ---------- Buffer y edición ----------

st.markdown("---")
st.subheader("2. Buffer de productos pendientes")

if st.session_state.productos_agregados:
    buffer_df = pd.concat(st.session_state.productos_agregados, ignore_index=True)

    st.markdown("**Vista rápida del buffer**")
    st.dataframe(buffer_df, use_container_width=True)

    # Eliminación selectiva
    st.markdown("**Eliminar ítems específicos del buffer**")
    buffer_df["_idx_internal"] = buffer_df.index
    seleccionados = st.multiselect(
        "Selecciona filas a eliminar (por índice):",
        options=list(buffer_df["_idx_internal"].astype(int)),
        format_func=lambda x: f"Fila {x} | Subreceta: {buffer_df.loc[buffer_df['_idx_internal'] == x, 'Subreceta'].iat[0]} x{buffer_df.loc[buffer_df['_idx_internal'] == x, 'Cantidad_ensamblada'].iat[0]}"
    )
    if st.button("Eliminar seleccionados") and seleccionados:
        filtered = buffer_df[~buffer_df["_idx_internal"].isin(seleccionados)].drop(columns=["_idx_internal"])
        nuevos_list = []
        for _, grp in filtered.groupby(["Subreceta", "Cantidad_ensamblada", "Clave_subreceta"]):
            nuevos_list.append(grp.reset_index(drop=True))
        st.session_state.productos_agregados = nuevos_list
        st.success("Se eliminaron los seleccionados.")
        st.rerun()

    # Exportar buffer
    st.download_button(
        "Exportar buffer como CSV",
        buffer_df.drop(columns=["_idx_internal"]).to_csv(index=False).encode("utf-8"),
        file_name="buffer_subrecetas.csv",
        mime="text/csv"
    )
    st.write(f"Productos en buffer: {len(st.session_state.productos_agregados)}")
else:
    st.info("No hay productos en el buffer. Agrega uno arriba.")

# ---------- Envío ----------

st.markdown("---")
st.subheader("3. Enviar todo")

st.write(f"Se enviará a la sucursal: **{sucursal}**")

if st.button("Enviar todo"):
    if not st.session_state.productos_agregados:
        st.warning("Buffer vacío. Agrega productos antes de enviar.")
    else:
        try:
            output_df = pd.concat(st.session_state.productos_agregados, ignore_index=True)
            output_df["Sucursal"] = sucursal
            output_df["Fecha_envio"] = pd.Timestamp.utcnow().strftime("%Y-%m-%d %H:%M:%S")

            filename = "outputs/registro_subrecetas.csv"
            guardar_csv_atomico(output_df, filename)
            st.success("✅ Guardado local correctamente.")

            # Intentar subir a SharePoint (placeholder)
            try:
                subir_csv_a_sharepoint(filename, carpeta_remote="Subrecetas/Registros")
                st.success("🔄 También sincronizado con SharePoint (simulado).")
            except Exception as e:
                st.warning(f"No se pudo sincronizar con SharePoint: {e}")

            st.session_state.productos_agregados = []
        except Exception as e:
            st.error(f"Error al persistir la información: {e}")

# ---------- Estado final / debug opcional ----------

st.markdown("---")
with st.expander("Debug / estado interno"):
    st.write("Session state productos_agregados (raw):", st.session_state.productos_agregados)
    if os.path.isfile("outputs/registro_subrecetas.csv"):
        st.write("Último archivo guardado existe en:", os.path.abspath("outputs/registro_subrecetas.csv"))
