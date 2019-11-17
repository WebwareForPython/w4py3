"""PSP Plug-in for Webware for Python"""

from .PSPServletFactory import PSPServletFactory


def installInWebware(application):
    application.addServletFactory(PSPServletFactory(application))
