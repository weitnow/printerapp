from .base_view import BaseView


class PrintInsertView(BaseView):
    name = "printinserts"
    columns = ["Druckeinlage", "Breite mm", "Höhe mm"]
    columns_actions = {}
    query = """
    SELECT
    FormatDruckeinlage,
    WidthMM,
    HeightMM
    FROM druckeinlage

    ORDER BY FormatDruckeinlage
    """


    



    def delete(self, app, selected_rows):
        pass
       
