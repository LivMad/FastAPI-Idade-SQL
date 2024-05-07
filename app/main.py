from pydantic import BaseModel
from sqlmodel import Field, Session, SQLModel, create_engine, select
import ulid
from time import time
from fastapi import FastAPI, HTTPException, status


class Contato(SQLModel, table=True):
    id: str | None = Field(primary_key=True, default_factory=lambda: str(ulid.new()))
    nome: str
    idade: int = Field(ge=0, lt=120)
    data_criacao: float | None = Field(default_factory=time)
    data_atualizacao: float | None = Field(default_factory=time)


class EditarContato(BaseModel):
    nome: str | None = None
    idade: int | None = Field(default=None, ge=0, lt=120)


postgres_url = "postgresql://user:123@localhost:5432/postgres"

engine = create_engine(postgres_url)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


app = FastAPI()


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.post("/cadastros/")
def novo_cadastro(novo: Contato):
    with Session(engine) as session:
        session.add(novo)
        session.commit()
        session.refresh(novo)
        return novo


@app.get("/cadastros/{cadastro_id}")
def get_cadastro(cadastro_id: str):
    with Session(engine) as session:
        cadastro = session.exec(
            select(Contato).where(Contato.id == cadastro_id)
        ).first()
        if cadastro is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"id = {cadastro_id} não encontrado",
            )
        return cadastro


@app.get("/cadastros/")
def todos_cadastros():
    with Session(engine) as session:
        cadastro = session.exec(select(Contato)).all()
        return cadastro


@app.patch("/cadastros/{cadastro_id}")
def editar_contato(cadastro_id: str, contato_editado: EditarContato):
    with Session(engine) as session:
        contato = session.exec(select(Contato).where(Contato.id == cadastro_id)).first()

        if contato is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"id = {cadastro_id} não encontrado",
            )

        if contato_editado.nome is not None:
            contato.nome = contato_editado.nome
        if contato_editado.idade is not None:
            contato.idade = contato_editado.idade

        session.add(contato)
        session.commit()
        session.refresh(contato)
        return contato


@app.delete("/cadastros/{cadastro_id}")
def deletar_cadastro(cadastro_id: str):
    with Session(engine) as session:
        contato = session.exec(select(Contato).where(Contato.id == cadastro_id)).first()
        if contato is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"id = {cadastro_id} não encontrado",
            )
        session.delete(contato)
        session.commit()
