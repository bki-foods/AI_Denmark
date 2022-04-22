from abc import ABC, abstractmethod
import pandas as pd

class CoffeeDataConnection(ABC):
    """
    An abstract class for connecting to a database or data file of coffee data. Inherit from this class to make a
    connection to a new type of database/data file.
    """
    @abstractmethod
    def get_coffee_contracts(self):
        pass

    @abstractmethod
    def get_recipe_information(self):
        pass

    @abstractmethod
    def get_roaster_input(self):
        pass

    @abstractmethod
    def get_roaster_output(self):
        pass

    @abstractmethod
    def get_gc_grades(self):
        pass

    @abstractmethod
    def get_finished_goods_grades(self):
        pass

    @abstractmethod
    def get_order_relationships(self):
        pass


class ExcelConnection(CoffeeDataConnection):
    """
    An example of a class that implements CoffeeDataConnection to read from an excel file.
    """
    def __init__(self, file):
        self.data = pd.read_excel(file, sheet_name=["Kaffekontrakt", "Recepter", "LOAD_R", "UNLOAD_R", "Råvarekarakterer", "Færdigvarekarakterer", "Ordrerelationer"])

    def get_coffee_contracts(self):
        return self.data["Kaffekontrakt"]

    def get_recipe_information(self):
        return self.data["Recepter"]

    def get_roaster_input(self):
        return self.data["LOAD_R"]

    def get_roaster_output(self):
        return self.data["UNLOAD_R"]

    def get_gc_grades(self):
        return self.data["Råvarekarakterer"]

    def get_finished_goods_grades(self):
        return self.data["Færdigvarekarakterer"]

    def get_order_relationships(self):
        return self.data["Ordrerelationer"]