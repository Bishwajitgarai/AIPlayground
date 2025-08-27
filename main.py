import uvicorn
import os

safe_core=max(1,os.cpu_count())
safe_core=1
print(f"Ruuning Cpu Count will be {safe_core}")

if __name__=="__main__":
    uvicorn.run("app.app:app",host="0.0.0.0",port=10000,workers=safe_core)