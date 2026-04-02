from utils import plugins

PLUGIN_NAME = "REPEC"
DISPLAY_NAME = "REPEC"
DESCRIPTION = (
    "Generates and serves ReDIF metadata files for the Research Papers in "
    "Economics (REPEC) archive network."
)
AUTHOR = "Janeway Team"
VERSION = "1.0"
SHORT_NAME = "repec"
MANAGER_URL = "repec_admin"
JANEWAY_VERSION = "1.7"


class RepecPlugin(plugins.Plugin):
    plugin_name = PLUGIN_NAME
    display_name = DISPLAY_NAME
    description = DESCRIPTION
    author = AUTHOR
    short_name = SHORT_NAME
    manager_url = MANAGER_URL
    version = VERSION
    janeway_version = JANEWAY_VERSION
    is_workflow_plugin = False


def install():
    RepecPlugin.install()


def hook_registry():
    RepecPlugin.hook_registry()
