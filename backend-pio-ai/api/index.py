try:
    from app.main import app
except Exception as e:
    import traceback
    import json

    async def app(scope, receive, send):
        assert scope['type'] == 'http'
        error_detail = traceback.format_exc()
        body = json.dumps({"error": str(e), "traceback": error_detail}).encode("utf-8")
        
        await send({
            'type': 'http.response.start',
            'status': 500,
            'headers': [
                (b'content-type', b'application/json'),
                (b'content-length', str(len(body)).encode("utf-8")),
            ]
        })
        await send({
            'type': 'http.response.body',
            'body': body
        })
