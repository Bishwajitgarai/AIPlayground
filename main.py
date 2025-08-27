import uvicorn
import os

safe_core=max(1,os.cpu_count())
print(f"Ruuning Cpu Count will be {safe_core}")

if __name__=="__main__":
    uvicorn.run("app.app:app",port=5000,workers=safe_core)