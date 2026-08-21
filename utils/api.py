import requests


def call_api(
    app_script_url,
    action,
    sheet,
    data=None,
    row_index=None,
    uuid=None
):
    """
    Sends requests to Google Apps Script.

    Parameters
    ----------
    app_script_url : str
        Apps Script URL.

    action : str
        append / update / delete

    sheet : str
        Target sheet name.

    data : list | dict | None
        Payload.

    row_index : int | None
        Optional row index.

    Returns
    -------
    bool
        True if request succeeded.
    """

    payload = {
    "action": action,
    "sheet": sheet,
    "data": data,
    "row_index": row_index,
    "uuid": uuid,
}

    try:

        response = requests.post(
            app_script_url,
            json=payload,
            timeout=20,
        )

        return response.text.strip() == "OK"

    except Exception:

        return False
