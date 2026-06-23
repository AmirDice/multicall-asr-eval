"""Fully fictional Spanish software-helpdesk calls used to synthesise a
multi-call recording. No real people, companies, or customer data — this is
generated audio for a reproducible ASR/diarization evaluation.

Each call is a list of turns: (speaker, text). `speaker` is "agent" or
"client". A long recording is built by concatenating several calls with
silence gaps, which mimics a call-centre queue recording where one audio
file contains several unrelated conversations.

Domain vocabulary is intentionally seeded with brand-like and technical
terms (GestorPro, FactuCloud, SEPA, código de barras) so the entity-accuracy
metric has something meaningful to measure — the same failure mode real ASR
hits on proper nouns and jargon.
"""

from __future__ import annotations

CALLS: list[dict] = [
    {
        "id": "CALL-001",
        "topic": "Descuadre de stock tras una venta anulada",
        "turns": [
            ("agent", "Soporte GestorPro, buenos días."),
            ("client", "Hola, buenos días. Le llamo de la tienda Pinares. Soy Marta."),
            ("agent", "Hola Marta, cuénteme, ¿en qué le ayudo?"),
            ("client", "Tengo un descuadre de stock en un artículo. Aparecen menos unidades de las que tengo en el almacén."),
            ("agent", "Vale. ¿Recuerda si anuló alguna venta de ese artículo esta semana?"),
            ("client", "Sí, ayer anulé una venta de tres unidades porque me equivoqué de producto."),
            ("agent", "Ahí está el problema. Al anular con Control más T, si no confirma el reintegro, el stock no vuelve a sumar. Vamos a corregirlo desde el ajuste de inventario."),
            ("client", "Perfecto. ¿Me dice los pasos?"),
            ("agent", "Entre en Almacén, luego en Ajuste de inventario, busque el artículo y ponga las tres unidades que faltan. Guarde con F12."),
            ("client", "Hecho. Ya me cuadra. Muchas gracias."),
            ("agent", "A usted. Buen día."),
        ],
    },
    {
        "id": "CALL-002",
        "topic": "Error al generar fichero SEPA de remesa",
        "turns": [
            ("agent", "Soporte GestorPro, buenas."),
            ("client", "Buenas. Soy Javier, de Electrodomésticos del Sur. No consigo generar la remesa SEPA, me da un error."),
            ("agent", "¿Qué mensaje de error le aparece exactamente?"),
            ("client", "Dice que el IBAN de un cliente no es válido."),
            ("agent", "Vale, eso es que un IBAN está mal escrito en una ficha. ¿Cuántos recibos lleva la remesa?"),
            ("client", "Unos cuarenta."),
            ("agent", "Vaya a Listados, filtre por IBAN vacío o incorrecto. Le saldrá el cliente que falla."),
            ("client", "Un momento... sí, hay uno con el IBAN incompleto."),
            ("agent", "Corríjalo, guarde, y vuelva a generar la remesa. Debería salir el fichero SEPA sin problema."),
            ("client", "Ya está, ahora sí lo ha generado. Gracias, Javier."),
            ("agent", "A usted, hasta luego."),
        ],
    },
    {
        "id": "CALL-003",
        "topic": "Alta de un proveedor nuevo y asociación de artículos",
        "turns": [
            ("agent", "GestorPro, dígame."),
            ("client", "Hola, llamo de la ferretería Costa. Quería dar de alta un proveedor nuevo, se llama Suministros Aribau."),
            ("agent", "Sin problema. Entre en Compras, Proveedores, y pulse Nuevo. Rellene el nombre y el CIF."),
            ("client", "Vale, ya lo tengo creado. ¿Y cómo le asocio los artículos?"),
            ("agent", "Desde la ficha del proveedor, pestaña Artículos, puede asociarlos uno a uno o con la importación por lista."),
            ("client", "Tengo como doscientos artículos de ese proveedor."),
            ("agent", "Entonces use la importación por lista. Prepare un Excel con el código y el precio de compra, y lo sube desde Utilidades, Importar."),
            ("client", "Perfecto, eso me ahorra mucho tiempo. Gracias."),
            ("agent", "De nada. Cualquier cosa, nos llama."),
        ],
    },
    {
        "id": "CALL-004",
        "topic": "Código de barras asignado a un artículo equivocado",
        "turns": [
            ("agent", "Soporte GestorPro, buenas tardes, le atiende Lucía."),
            ("client", "Hola Lucía. Soy Pedro, de la papelería Centro. Tengo un lío con un código de barras."),
            ("agent", "Cuénteme qué pasa."),
            ("client", "Cuando escaneo un bolígrafo, me sale en pantalla una libreta. El código está cruzado."),
            ("agent", "Eso es que ese código de barras está asignado a dos artículos. Vamos a quitarlo del que no toca."),
            ("client", "Vale."),
            ("agent", "Entre en la ficha de la libreta, pestaña Códigos, y borre el código que se repite. Déjelo solo en el bolígrafo."),
            ("client", "Listo, borrado. Escaneo otra vez... ahora sí sale el bolígrafo."),
            ("agent", "Genial. Quedaría arreglado."),
            ("client", "Muchas gracias, hasta luego."),
        ],
    },
]


def all_turns_flat() -> list[tuple[str, str, str]]:
    """Return (call_id, speaker, text) for every turn across all calls."""
    out = []
    for call in CALLS:
        for speaker, text in call["turns"]:
            out.append((call["id"], speaker, text))
    return out
