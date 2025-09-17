import datetime
import decimal
import os

from actual import Actual
from actual.queries import create_account, create_transaction
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel

load_dotenv()

app = FastAPI(
    title="Actual Budget API Rest",
    description="Simple API to create transactions using ActualBudget",
    version="0.1.0",
)

API_KEY = os.getenv("API_KEY")


class TransactionRequest(BaseModel):
    account: str
    payee: str
    amount: float
    notes: str
    outcome: bool = True
    cleared: bool = True


def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key"
        )
    return x_api_key


def add_transaction(transaction: TransactionRequest):
    with Actual(
        base_url=os.getenv("ACTUAL_HOST"),
        password=os.getenv("ACTUAL_PASSWORD"),
        file=os.getenv("ACTUAL_FILE"),
    ) as actual:
        if transaction.outcome:
            amount = decimal.Decimal(-abs(transaction.amount))
        else:
            amount = decimal.Decimal(abs(transaction.amount))
        t = create_transaction(
            actual.session,
            datetime.date.today(),
            transaction.account,
            transaction.payee,
            notes=transaction.notes,
            amount=amount,
            cleared=transaction.cleared,
        )
        actual.commit()  # use the actual.commit() instead of session.commit()!
        try:
            actual.run_rules([t])
            print("Rules ran successfully")
        except Exception as e:
            print("Error running rules:" + str(e))
        finally:
            actual.commit()  # use the actual.commit() instead of session.commit()!
            return "Transaction added"


@app.post("/transaction")
async def create_new_transaction(
    transaction: TransactionRequest, api_key: str = Depends(verify_api_key)
):
    try:
        return add_transaction(transaction)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API is running"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
