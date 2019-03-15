from budgetlist import app
import os

os.environ["BUDGET_DB_CONN"] = "postgresql://budgetuser:budge1234list*@localhost:5432/budgetlist"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 9000))
    app.run(port=port)
