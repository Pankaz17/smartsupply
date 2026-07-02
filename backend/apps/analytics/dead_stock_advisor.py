"""Dead Stock Advisor — dynamic business suggestions (advisory only)."""


def get_dead_stock_suggestions(days_without_sale):
    """
    Return actionable suggestions based on how long a product has been unsold.

    Suggestions are advisory only; nothing is automated.
    """
    if days_without_sale >= 120:
        return [
            'Stop Reordering',
            'Bundle Remaining Stock',
            'Heavy Discount Campaign',
        ]
    if days_without_sale >= 90:
        return [
            'Bundle with a Popular Product',
            'Run a Discount Campaign',
        ]
    if days_without_sale >= 60:
        return [
            'Run a Discount Campaign',
        ]
    return []


def format_suggestions_for_export(suggestions):
    return '; '.join(suggestions)
