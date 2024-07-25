import requests

VOLUME_SERVER_URL = "http://host.docker.internal:3001"
PLUGIN_NAME = "main"


def get_volume_path():
    """
    Get the path to the main server's volume folder.
    """
    return f"/volume/{PLUGIN_NAME}/"


async def copy_to_volume(files):
    data = {
        "volumeName": "ouroboros-volume",
        "pluginFolderName": "main",
        "files": files,
    }

    return await request_volume_server("copy-to-volume", data)


async def copy_to_host(files):
    data = {
        "volumeName": "ouroboros-volume",
        "pluginFolderName": "main",
        "files": files,
    }

    return await request_volume_server("copy-to-host", data)


async def clear_plugin_folder():
    data = {
        "volumeName": "ouroboros-volume",
        "pluginFolderName": "main",
    }

    return await request_volume_server("clear-plugin-folder", data)


async def request_volume_server(path, data):
    url = f"{VOLUME_SERVER_URL}/{path}"
    try:
        result = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json=data,
        )
        if not result.ok:
            return False, result.text
        else:
            return True, ""
    except Exception as error:
        return False, str(error)
