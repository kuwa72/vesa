"""
Run script for VESA application.
"""
import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    # Get configuration from environment variables
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("DEBUG", "True").lower() == "true"
    
    # Run the application
    uvicorn.run(
        "vesa.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )
