from settings.config import recetas
import streamlit as st


def calcular_ingredientes(nombre_receta, cantidad):
    receta_base = recetas.get(nombre_receta)
    if not receta_base:
        return st.write("No existe la receta seleccionada")

    receta_multiplicada = {
        ingrediente: round(cantidad * cantidad_base, 2)
        for ingrediente, cantidad_base in receta_base.items()
    }

    return receta_multiplicada
