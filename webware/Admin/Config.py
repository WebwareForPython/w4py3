from WebUtils.Funcs import htmlForDict

from .AdminSecurity import AdminSecurity


class Config(AdminSecurity):

    def title(self):
        return 'Config'

    def writeContent(self):
        self.writeln(htmlForDict(
            self.application().config(), topHeading='Application'))
