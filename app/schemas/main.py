from pydantic import BaseModel,Field
from typing import Dict,Optional

class Result(BaseModel):
    nome: str
    cpf: str
    localidade: str
    beneficios: Dict[str, str]
    imagem_base64: str

class Search(BaseModel):
    search: str = Field(min_length=3)
    filtro_busca: Optional[str] = None

class Dados(BaseModel):
    status: str
    result: Optional[Result] = None
    id: Optional[str] = None
    error: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str