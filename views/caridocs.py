from .base_view import BaseView


class CaridocView(BaseView):
    name = "caridocs"
    columns = ["CARIdoc", "CARIDocument", "Format CARIdoc", "Format Druckeinlage", "mm Width", "mm Height" ]
    columns_actions = {}
    query = """
    SELECT
    cd.CARIdoc,
    cd.BeschreibungFormular,
    cd.FormatCARIDoc,
    cd.FormatDruckeinlage,
    de.WidthMM,
    de.HeightMM
    FROM caridocs cd
    LEFT JOIN druckeinlage de on cd.FormatDruckeinlage = de.FormatDruckeinlage

    ORDER BY CARIdoc
    """

    def delete(self, app, selected_rows):
        pass
       
