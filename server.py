from contextlib import asynccontextmanager
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.controllers import user_controller, agent_controller, pipeline_controller, oanda_controller
from src.controllers import trader_account_controller, trader_account_trades_controller
from src.core.create_db_tables import create_tables

# Load environment variables from .env file
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # On startup
    await create_tables()
    yield
    # On shutdown (if needed)
    

# Define the FastAPI app at the module level
app = FastAPI(
    title="Stembots Technologies",
    version="1.0",
    description="Stembots technologies specializes in building robots",
    lifespan=lifespan
)

# Configure CORS
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the agent router
app.include_router(agent_controller.router)
# Include the pipeline router
app.include_router(pipeline_controller.router)
# Include the user router
app.include_router(user_controller.router)
# Include the oanda router
app.include_router(oanda_controller.router)
# Include the trader account router
app.include_router(trader_account_controller.router)
# Include the trader account trades router
app.include_router(trader_account_trades_controller.router)

def main():
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()

