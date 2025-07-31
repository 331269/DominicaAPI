from settings import subrecetas, ubicaciones
import streamlit as st
from calculadora.calcular_ingredientes import calcular_ingredientes
import pandas as pd
import os


st.title("Selecciona una Subreceta")

seleccionar_subreceta = st.selectbox(
    "Elige de la lista un producto:", options=list(subrecetas.keys()))

if seleccionar_subreceta in subrecetas:
    st.success(f"Seleccionaste la subreceta: {seleccionar_subreceta}")
    st.write(f"🔑 Código del producto: `{subrecetas[seleccionar_subreceta]}`")
else:
    st.warning("La subreceta escrita no está en la lista.")


cantidad_ensable = st.number_input(
    label="Cantidad a ensamblar",
    min_value=0,
    max_value=100,
    format="%i"
)

st.write(f"You entered: {cantidad_ensable}")

ingredientes_necesarios = calcular_ingredientes(
    seleccionar_subreceta, cantidad_ensable)

st.subheader("📝 Ingredientes necesarios")

ingredientes_df = pd.DataFrame(
    list(ingredientes_necesarios.items()),
    columns=["Ingrediente", "Cantidad"]
)

# Aplicar estilo blanco
styled_df = ingredientes_df.style.set_properties(**{
    'background-color': 'white',
    'color': 'black',
    'border-color': 'gray'
})

st.dataframe(styled_df, use_container_width=True)


if "productos_agregados" not in st.session_state:
    st.session_state.productos_agregados = []

if st.button("Agregar producto"):
    agrear_df = ingredientes_df.copy()
    agrear_df["Clave_subreceta"] = subrecetas[seleccionar_subreceta]
    agrear_df["Subreceta"] = seleccionar_subreceta
    agrear_df["Cantidad_ensamblada"] = cantidad_ensable
    st.session_state.productos_agregados.append(agrear_df)
    st.success("Información agregada")

st.subheader("Escoge la ubicación")
codigo_ubicacion = st.selectbox(
    "Código de ubicación:", options=list(ubicaciones.keys()))
st.write(f"Sucursal: {ubicaciones[codigo_ubicacion]}")

if st.button("Enviar"):
    if st.session_state.productos_agregados:
        output_df = pd.concat(
            st.session_state.productos_agregados, ignore_index=True)
        output_df["Sucursal"] = ubicaciones[codigo_ubicacion]

        os.makedirs("outputs", exist_ok=True)
        filename = "outputs/registro_subrecetas.csv"

        file_exists = os.path.isfile(filename)

        output_df.to_csv(
            filename,
            mode='a',
            header=not file_exists,
            index=False
        )

        st.success("Información agregada a Sharepoint")

        # Limpiar la lista después de guardar
        st.session_state.productos_agregados = []
    else:
        st.warning("No has agregado ningún producto todavía.")
