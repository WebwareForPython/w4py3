import os
from Examples.ExamplePage import ExamplePage


class PSPExamplePage(ExamplePage):

    def cornerTitle(self):
        return "PSP Examples"

    def writeOtherMenu(self):
        self.menuHeading('Other')
        self.menuItem(
            f'View source of<br/>{self.title()}',
            self.request().uriWebwareRoot() + 'PSP/Examples/View?filename=' +
            os.path.basename(self.request().serverSidePath()))
