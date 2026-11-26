from pydantic import BaseModel, Field
from typing import Optional

# para a criação de um usuario, ele tera que cadastrar um nome, uma senha e um email a essa conta.
class User_Creation(BaseModel):
    name: str
    senha: str
    email: str
    image: Optional[str] = None

# para procurar um usuario, sera usado seu identificador unico.
class User_Search(BaseModel):
    identificador: str

    
# para deletar o sua propria conta o usuario tera que clicar na opção deletar conta, onde o front vai pegar o id dessa conta e deleta-la
class User_Delete(BaseModel):
    id: int

#para fazer a autenticação do usuario, ele tera que colocar o email e a senha cadastrada na conta.
class User_Auth(BaseModel):
    email: str
    senha: str