from MiscUtils.Funcs import asclocaltime

from .ExamplePage import ExamplePage


class ShowTime(ExamplePage):

    def writeContent(self):
        self.write('<h4>The current time is:</h4>')
        self.write('<h5 style="color:green">', asclocaltime(), '</h5>')
