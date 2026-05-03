# RentGuard Frontend

一个独立的静态前端工作台，用来联调 `backend/app/main.py` 暴露的 RentGuard API。

## 使用方式

1. 先启动后端：

```powershell
cd backend
uvicorn app.main:app --reload
```

2. 再启动任意静态文件服务，例如：

```powershell
cd frontend
python -m http.server 3000
```

3. 打开 `http://127.0.0.1:3000`。

默认 API 地址是 `http://127.0.0.1:8000/api/v1`，如有需要可在页面顶部修改。
