from .base_view import BaseView


class LieugestionView(BaseView):
    name = "lieugestion"
    columns = ["StandortID", "Standort"]
    columns_actions = {}
    query = """
    SELECT
    StandortID,
    Standort
    FROM lieugestion

    ORDER BY StandortID
    """

    def delete(self, app, selected_rows):
        pass
       
