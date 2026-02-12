from .base_view import BaseView


class PrinterModels(BaseView):
    name = "printer_models"
    columns = ["PrinterModel"]
    columns_actions = {}
    query = """
    SELECT
    PrinterModel
    FROM printermodels

    ORDER BY PrinterModel
    """


    



    def delete(self, app, selected_rows):
        pass
       
