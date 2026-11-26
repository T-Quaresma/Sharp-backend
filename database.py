from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import inspect, text

class Base(DeclarativeBase):
  pass

db = SQLAlchemy(model_class=Base)


def migrate_schema():
  columns = {column["name"] for column in inspect(db.engine).get_columns("usuarios")}
  if "imagem" not in columns and "avatar" in columns:
    with db.engine.begin() as connection:
      connection.execute(text("ALTER TABLE usuarios RENAME COLUMN avatar TO imagem"))
  elif "imagem" not in columns:
    with db.engine.begin() as connection:
      connection.execute(text("ALTER TABLE usuarios ADD COLUMN imagem VARCHAR"))
  elif "avatar" in columns:
    with db.engine.begin() as connection:
      connection.execute(text(
        "UPDATE usuarios SET imagem = avatar WHERE imagem IS NULL"
      ))