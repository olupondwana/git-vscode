# Modern Calculator

A small FastAPI calculator with a responsive static UI and a JSON calculation API.

## Run

```powershell
python -m pip install -r requirements.txt
python -m uvicorn calculator:app --reload
```

Open <http://127.0.0.1:8000> in a browser.

## API

Send an arithmetic expression to `POST /api/calc`:

```json
{"expression": "(8 - 2) / 3"}
```

Successful responses include the expression and numeric result:

```json
{"expression": "(8 - 2) / 3", "result": 2}
```

The API supports basic arithmetic (`+`, `-`, `*`, `/`, `//`, `%`, `**`), unary signs, and parentheses. Invalid or unsupported expressions return an HTTP 400 response.
