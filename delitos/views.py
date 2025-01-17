import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from django.shortcuts import render
from django.http import HttpResponse


df_global: pd.DataFrame = None


def cargar_dataframe() -> pd.DataFrame:
    global df_global
    if df_global is None:
        try:
            df_global = pd.read_csv("static/carpetasFGJ_2024.csv")
        except FileNotFoundError:
            return HttpResponse("Archivo no encontrado")
        except pd.errors.EmptyDataError:
            return HttpResponse("El archivo está vacío")
        except pd.errors.ParserError:
            return HttpResponse("Error al leer el archivo CSV")
        except Exception as e:
            return HttpResponse(f"Error: {str(e)}")

    return df_global


def agrupar_datos(df: pd.DataFrame, columna: str) -> pd.DataFrame:
    return df.groupby(columna)["delito"].count().reset_index(name="count")


def generar_grafico_barras(df: pd.DataFrame, x: str, y: str, color: str, titulo: str) -> str:
    fig = px.bar(
        df,
        x=x,
        y=y,
        color=color,
        template="plotly_dark",
        labels={x: x.capitalize(), y: "Cantidad"},
        title=titulo
    )
    return fig.to_html(full_html=False)


def home(request):
    df = cargar_dataframe()

    df_delitos_mes = agrupar_datos(df, "mes_hecho").sort_values("count", ascending=False)
    df_alcaldia = agrupar_datos(df, "alcaldia_hecho").sort_values("count", ascending=False)

    fig_delitos_alcaldia = generar_grafico_barras(
        df_alcaldia,
        "alcaldia_hecho",
        "count",
        "count",
        "Cantidad de delitos por alcaldía"
    )
    fig_delitos_mes = generar_grafico_barras(
        df_delitos_mes,
        "mes_hecho",
        "count",
        "count",
        "Cantidad de delitos por mes"
    )

    return render(request, "delitos/delitos_por_alcaldia.html", {"fig2": fig_delitos_alcaldia, "fig3": fig_delitos_mes})



def tipo_delito(request):
    df: pd.DataFrame = cargar_dataframe()
    lista_delitos: list = df.delito.sort_values().unique().tolist()
    lista_lugares: list = ["alcaldia_hecho", "colonia_hecho", "municipio_hecho"]

    # Obtener el delito a buscar del formulario
    if request.method == "POST":
        lugar_a_buscar: str = request.POST.get("lugar")
        delito_a_buscar: str = request.POST.get("delito")
    else:
        lugar_a_buscar: str = lista_lugares[0]
        delito_a_buscar: str = lista_delitos[0]

    # Crear un DataFrame que contenga todos los datos y solo los datos del delito a buscar
    df_delito: pd.DataFrame = df[(df.delito == delito_a_buscar)]

    # Agrupar los datos por alcaldía y contar la cantidad de delitos
    # df_delito_alcaldia: pd.DataFrame = df_delito.groupby(lugar_a_buscar)["delito"].count().reset_index(name="count")
    df_delito_alcaldia = agrupar_datos(df_delito, lugar_a_buscar)
    fig_delitos = generar_grafico_barras(
        df_delito_alcaldia,
        lugar_a_buscar,
        "count",
        "count",
        delito_a_buscar
    )

    return render(
        request,
        "delitos/tipo_delito.html",
        {
            "fig_delitos": fig_delitos,
            "lugares": lista_lugares,
            "delitos": lista_delitos,
            "delito_a_buscar": delito_a_buscar,
            "lugar_a_buscar": lugar_a_buscar,
        }
    )


def mapa(request):
    df = cargar_dataframe()
    # df_puntos = df.groupby(["alcaldia_hecho", "latitud", "longitud"])["delito"].count().reset_index().sort_values("delito", ascending=False)
    df_puntos = df.groupby(["colonia_hecho", "latitud", "longitud"]).agg(
        delito_count=('delito', 'count'),
        texto_delito=('delito', ', '.join)
    ).reset_index()
    #.sort_values("delito_count", ascending=False)

    fig_mapa = px.scatter_mapbox(
        df_puntos,
        lat=df_puntos["latitud"],
        lon=df_puntos["longitud"],
        color="delito_count",
        template="plotly_dark",
        zoom=11,
        height=600,
        mapbox_style="open-street-map",
    )
    fig_mapa.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        hovermode="closest",
    )
    fig_mapa.update_traces(
        hovertemplate=
        ' <b>Colonia: </b>' + df_puntos['colonia_hecho'].astype(str) + '<br>' +
        ' <b>Delito: </b>' + df_puntos['texto_delito'].astype(str) + '<br>' +
        ' <b>Cantidad de delitos: </b>' + df_puntos['delito_count'].astype(str) + '<br>',
    )

    return render(request, "delitos/mapa.html", {"fig_mapa": fig_mapa.to_html(full_html=False)})