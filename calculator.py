import ast
import math
import operator
from pathlib import Path
from typing import Callable

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field


STATIC_DIR = Path(__file__).resolve().parent / "static"
MAX_EXPRESSION_LENGTH = 256
MAX_AST_NODES = 64
MAX_INTEGER_BITS = 4096
MAX_EXPONENT = 1000

_BINARY_OPERATORS: dict[type[ast.operator], Callable[[int | float, int | float], int | float]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY_OPERATORS: dict[type[ast.unaryop], Callable[[int | float], int | float]] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

app = FastAPI(title="Modern Calculator")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class CalculationRequest(BaseModel):
    expression: str = Field(min_length=1, max_length=MAX_EXPRESSION_LENGTH)


def _evaluate(node: ast.expr) -> int | float:
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        value = node.value
    elif isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPERATORS:
        left = _evaluate(node.left)
        right = _evaluate(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > MAX_EXPONENT:
            raise ValueError(f"Exponent magnitude must not exceed {MAX_EXPONENT}.")
        value = _BINARY_OPERATORS[type(node.op)](left, right)
    elif isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPERATORS:
        value = _UNARY_OPERATORS[type(node.op)](_evaluate(node.operand))
    else:
        raise ValueError("Only basic arithmetic operations are supported.")

    if isinstance(value, int) and value.bit_length() > MAX_INTEGER_BITS:
        raise ValueError("The result is too large.")
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("The result is not a finite number.")
    if not isinstance(value, (int, float)):
        raise ValueError("The result must be a real number.")
    return value


@app.get("/")
async def calculator_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/calc")
async def calculate(request: CalculationRequest) -> dict[str, str | int | float]:
    expression = request.expression.strip()
    if not expression:
        raise HTTPException(status_code=400, detail="Enter an expression.")

    try:
        parsed = ast.parse(expression, mode="eval")
        if sum(1 for _ in ast.walk(parsed)) > MAX_AST_NODES:
            raise ValueError("The expression is too complex.")
        result = _evaluate(parsed.body)
    except SyntaxError as error:
        raise HTTPException(status_code=400, detail="Invalid arithmetic expression.") from error
    except (ArithmeticError, ValueError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return {"expression": expression, "result": result}
