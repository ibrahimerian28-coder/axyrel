def to_num(value):
    """
    Safely converts values to float.

    Returns 0 for empty or invalid values.
    """

    try:
        return (
            float(str(value).replace(",", ""))
            if value not in ["", None]
            else 0
        )

    except (ValueError, TypeError):
        return 0
