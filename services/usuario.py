import secrets
import re
import unicodedata
from database import db
from models import Usuario
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError

def generate_identificador(nome):
    nome = unicodedata.normalize("NFKD", nome)
    nome = "".join(
        char for char in nome
        if not unicodedata.combining(char)
    )

    nome = re.sub(r"[^a-z0-9]", "", nome.lower())

    if not nome:
        nome = "usuario"

    while True:
        numero = secrets.randbelow(10000)
        identificador = f"{nome}#{numero:04d}"

        existing_user = db.session.execute(
            db.select(Usuario).where(
                Usuario.identificador == identificador
            )
        ).scalar_one_or_none()

        if existing_user is None:
            return identificador


# Creating User and adding it to the database.
def user_creation(data):
    existing_user = db.session.execute(db.select(Usuario).where(Usuario.nomeUsu == data.name)).scalar_one_or_none()
    if existing_user is not None:
        return {"Message": "User already exists."}, 409
    existing_email = db.session.execute(db.select(Usuario).where(Usuario.email == data.email)).scalar_one_or_none()
    if existing_email is not None:
        return {"Message": "Email already exists."}, 409
    identificador = generate_identificador(data.name)
    hashed_password = generate_password_hash(data.senha)
    new_user = Usuario(
        nomeUsu = data.name,
        email = data.email,
        senha = hashed_password,
        identificador = identificador
    )
    try:
        db.session.add(new_user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {"Message": "email or identificator already exists."}, 409
    return {"Message": "User created successfully!"}, 201

# Searching for a specific user.

def user_search(data):
    users = db.session.execute(db.select(Usuario).where(Usuario.nomeUsu == data.name)).scalars().all()
    if not users:
        return {"Message": "User not found."}
    user_list = []
    for user in users:
        user_list.append({"nomeUsu": user.nomeUsu, "usuId": user.usuId, "email": user.email})
    return user_list, 200

# User can only delete their own user so it's a direct approach

def user_delete(data):
    user = db.session.execute(db.select(Usuario).where(Usuario.usuId == data.id)).scalars().first()
    if user is None:
        return {"Message": "User not found."}
    else:
        db.session.delete(user)
        db.session.commit()
        return {"Message": "User deleted successfully."}

def credential_check(data):
    user = db.session.execute(db.select(Usuario).where(Usuario.email == data.email)).scalar_one_or_none()
    if user is None:
        return {"Message": "Email not found."}, 404
    if check_password_hash(
            user.senha,
            data.senha
        ):
        return {"usuId": user.usuId,
                "email": user.email}, 200
    else:
        return {"Message": "Invalid password."}, 401
