from fastapi import FastAPI, Query

app = FastAPI()


@app.get("/vector-graph-search")
async def vector_graph_search(
    query: str = Query(..., max_length=500), k: int = Query(5, gt=0, le=100)
):
    return "Hello world"
