from fastapi import Form
class OAuth2EmailRequestForm:
    def __init__(
        self,
        username: str = Form(...),  # Replace "username" with "email"
        password: str = Form(...),
        scope: str = Form(""),
        client_id: str = Form(None),
        client_secret: str = Form(None),
    ):
        self.email = username
        self.password = password
        self.scope = scope
        self.client_id = client_id
        self.client_secret = client_secret
