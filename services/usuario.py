import secrets
import re
import unicodedata
from database import db
from models import Usuario, Grupo, Atividade, Agendamento, ParticipantesAtiv
from sqlalchemy import or_
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
        identificador = identificador,
        imagem = data.image
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
    user = db.session.execute(
        db.select(Usuario).where(Usuario.identificador == data.identificador)
    ).scalar_one_or_none()
    if user is None:
        return {"Message": "User not found."}, 404
    return [{
        "nomeUsu": user.nomeUsu,
        "usuId": user.usuId,
        "email": user.email
    }], 200

# Load private profile data only for the authenticated account.
def get_user_profile(user_id):
    user = db.session.get(Usuario, user_id)
    if user is None:
        return {"Message": "User not found."}, 404
    return {
        "usuId": user.usuId,
        "nomeUsu": user.nomeUsu,
        "email": user.email,
        "identificador": user.identificador,
        "imagem": user.imagem
    }, 200


def user_delete(user_id):
    user = db.session.get(Usuario, user_id)
    if user is None:
        return {"Message": "User not found."}, 404

    try:
        owned_schedule_ids = db.session.execute(
            db.select(Agendamento.agenId)
            .join(Atividade, Agendamento.ativId == Atividade.ativId)
            .where(Atividade.criadorId == user_id)
        ).scalars().all()

        participant_records = db.session.execute(
            db.select(ParticipantesAtiv).where(
                or_(
                    ParticipantesAtiv.usuId == user_id,
                    ParticipantesAtiv.agenId.in_(owned_schedule_ids)
                )
            )
        ).scalars().all()
        for participant in participant_records:
            db.session.delete(participant)

        owned_groups = db.session.execute(
            db.select(Grupo).where(Grupo.criadorId == user_id)
        ).scalars().all()
        for group in owned_groups:
            db.session.delete(group)

        db.session.flush()

        owned_activities = db.session.execute(
            db.select(Atividade).where(Atividade.criadorId == user_id)
        ).scalars().all()
        for activity in owned_activities:
            db.session.delete(activity)

        db.session.delete(user)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return {"Message": "User deleted successfully."}, 200

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
