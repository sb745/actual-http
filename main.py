import datetime
from datetime import date
import decimal
import os

from actual import Actual
from actual.queries import create_account, create_transaction, get_accounts
from actual.budgets import get_budget_history
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel
from typing import Optional
import json

load_dotenv()

app = FastAPI(
    title="Actual-HTTP",
    description="Simple API wrapper for ActualBudget",
    version="1.0.0",
)

class TransactionRequest(BaseModel):
    account: str
    payee: str
    category: str = None
    amount: float
    notes: str = None
    payment: bool = True
    cleared: bool = False

class BudgetRequest(BaseModel):
    year: int
    month: int
    day: Optional[int] = 1

class ActualCredentials(BaseModel):
    password: str
    encryption_password: str | None
    actual_file: str

def get_credentials(
    x_actual_password: str = Header(...),
    x_actual_encryption_password: str = Header(None),
    x_actual_file: str = Header(...)
) -> ActualCredentials:
    # Convert "None" string to actual None
    encryption_password = (
        None if x_actual_encryption_password in (None, "None", "none", "") 
        else x_actual_encryption_password
    )
    
    return ActualCredentials(
        password=x_actual_password,
        encryption_password=encryption_password,
        actual_file=x_actual_file
    )

def _get_budget_history_internal(year: int, month: int, day: int, credentials: ActualCredentials):
    # Internal helper function to avoid FastAPI dependency injection issues
    # Validate date parameters
    target_date = date(year, month, day)
    
    with Actual(
        base_url=os.getenv("ACTUAL_HOST"),
        password=credentials.password,
        encryption_password=credentials.encryption_password,
        file=credentials.actual_file
    ) as actual:
        history = get_budget_history(
            actual.session,
            target_date,
        )
        # Get budget for the specific month
        budget = history.from_month(target_date)
        
        # Convert to dictionary and return as JSON
        return budget.as_dict()

def add_transaction(transaction: TransactionRequest, credentials: ActualCredentials):
    with Actual(
        base_url=os.getenv("ACTUAL_HOST"),
        password=credentials.password,
        encryption_password=credentials.encryption_password,
        file=credentials.actual_file
    ) as actual:
        if transaction.payment:
            amount = decimal.Decimal(-abs(transaction.amount))
        else:
            amount = decimal.Decimal(abs(transaction.amount))
        t = create_transaction(
            actual.session,
            date=datetime.date.today(),
            account=transaction.account,
            payee=transaction.payee,
            category=transaction.category,
            amount=amount,
            notes=transaction.notes,
            cleared=transaction.cleared,
        )
        actual.commit()
        try:
            actual.run_rules([t])
            print("Rules ran successfully")
        except Exception as e:
            print("Error running rules:" + str(e))
        finally:
            actual.commit()
            return "Transaction added"


@app.post("/transaction/add")
async def create_new_transaction(
    transaction: TransactionRequest, 
    credentials: ActualCredentials = Depends(get_credentials)
):
    try:
        return add_transaction(transaction, credentials)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/budget/{year}/{month}")
async def get_budget_history_endpoint(
    year: int,
    month: int,
    credentials: ActualCredentials = Depends(get_credentials)
):
    try:
        return _get_budget_history_internal(year, month, 1, credentials)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/budget/current")
async def get_current_budget(credentials: ActualCredentials = Depends(get_credentials)):
    today = date.today()
    try:
        return _get_budget_history_internal(today.year, today.month, 1, credentials)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/accounts/balances")
async def get_account_balances(credentials: ActualCredentials = Depends(get_credentials)):
    try:
        with Actual(
            base_url=os.getenv("ACTUAL_HOST"),
            password=credentials.password,
            encryption_password=credentials.encryption_password,
            file=credentials.actual_file
        ) as actual:
            accounts = get_accounts(actual.session)
            
            if accounts is None:
                return {"error": "No accounts found or query failed"}
            
            account_balances = []
            for account in accounts:
                print(f"Account: {account}, Balance: {account.balance}")
                account_balances.append({
                    "name": account.name,
                    "balance": float(account.balance) if account.balance is not None else 0.0,
                    "id": account.id,
                    "closed": account.closed,
                    "offbudget": account.offbudget
                })
            
            return account_balances
    except Exception as e:
        import traceback
        print(f"Full error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API is running"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5007)
