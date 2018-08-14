from .app import Hydroviewer

# This function gets a path to the user's workspace on the tethys server.
# Shapefiles will be saved to this workspace directory ( /workspaces/user_workspaces/user_name/layer_code/ )
# You'll need to add a function to clean up the workspace.
def get_user_workspace(request):

    workspace = Hydroviewer.get_user_workspace(request).path

    return workspace
