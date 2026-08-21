def route(page: str) -> None:
    modules = {
        "Dashboard": "modules.dashboard",
        "Customers": "modules.customers",
        "Maintenance": "modules.maintenance",
        "Inventory": "modules.inventory",
        "Expenses": "modules.expenses",
        "Invoices": "modules.invoices",
        "Profitability": "modules.profits",
        "Store": "modules.store",
    }
    module_name = modules.get(page)
    if not module_name:
        return
    module = __import__(module_name, fromlist=["app"])
    module.app()
