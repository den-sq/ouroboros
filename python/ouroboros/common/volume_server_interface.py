import requests

VOLUME_SERVER_URL = "http://host.docker.internal:3001"
PLUGIN_NAME = "main"


def get_volume_path():
    """
    Get the path to the main server's volume folder.
    """
    return f"/volume/{PLUGIN_NAME}/"


async def copy_to_volume(files):
    """
    Copy host files to the main server's volume folder.

    Parameters
    ----------
    files : list[dict]
        A list of dictionaries containing the source and target paths for the files to copy.

    Returns
    -------
    tuple[bool, str]
        A tuple containing a boolean indicating if the operation was successful and an error message if it
        was not.
    """

    data = {
        "volumeName": "ouroboros-volume",
        "pluginFolderName": "main",
        "files": files,
    }

    return await request_volume_server("copy-to-volume", data)


async def copy_to_host(files):
    """
    Copy files from the main server's volume folder to the host.

    Parameters
    ----------
    files : list[dict]
        A list of dictionaries containing the source and target paths for the files to copy.

    Returns
    -------
    tuple[bool, str]
        A tuple containing a boolean indicating if the operation was successful and an error message if it
        was not.
    """

    data = {
        "volumeName": "ouroboros-volume",
        "pluginFolderName": "main",
        "files": files,
    }

    return await request_volume_server("copy-to-host", data)


async def clear_plugin_folder():
    """
    Clear the main server's plugin folder.

    Returns
    -------
    tuple[bool, str]
        A tuple containing a boolean indicating if the operation was successful and an error message if it
        was not.
    """

    data = {
        "volumeName": "ouroboros-volume",
        "pluginFolderName": "main",
    }

    return await request_volume_server("clear-plugin-folder", data)


async def request_volume_server(path, data):
    """
    Send a request to the main server's volume server.

    Parameters
    ----------
    path : str
        The path to the endpoint on the volume server.
    data : dict
        The data to send in the request.

    Returns
    -------
    tuple[bool, str]
        A tuple containing a boolean indicating if the operation was successful and an error message if it
        was not.
    """

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
