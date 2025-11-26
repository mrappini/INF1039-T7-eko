import sqlalchemy as db
from sqlalchemy import text
import hashlib
#import random
import secrets
engine = db.create_engine("sqlite:///login.sqlite")
#bad= ["SELECT", "DROP","DELETE","INSERT","CREATE","ALTER","GRANT","REVOKE","*","WHERE"]
conn = engine.connect() 

metadata = db.MetaData()

#conn.execute(text("DROP TABLE Usuario"))
Entrada = db.Table('Usuario', metadata,
              db.Column('Email', db.String(255),primary_key=True),
               db.Column('Usuario', db.String(255),nullable=False),
              db.Column('Senha', db.String(255), nullable=False),
               db.Column('Uid', db.String(255),nullable=False),
             
              )

metadata.create_all(engine) 

def sha512(inp: str): return(hashlib.sha512(inp.encode()).hexdigest())
"""
def sanitize(inp: str,filter):
    for item in filter:
        inp = inp.removeprefix(item)
        inp = inp.removesuffix(item)
    return inp
"""

def get_user(email):
    getuser = db.select(Entrada).where(Entrada.c.Email == email)
    return(conn.execute(getuser).fetchone())

def login_match(email,senha):
    user_entry = get_user(email)
    if user_entry==None: return 404
    if sha512(senha)!=user_entry[2]: return 403
    return 200



def new_user(email,usuario,senha):
    user_entry = get_user(email)
    print(user_entry)
    if user_entry !=None: return "exists"
    register = db.insert(Entrada).values(Email=email, Usuario=usuario, Senha=sha512(senha),Uid=secrets.token_bytes(20).hex())
    Result = conn.execute(register)
    conn.commit()
    return Result.rowcount


R = new_user("pedro@gmail.com","xxPedroxx","1234")
print(R)
R = login_match("pedro@gmail.com","1234")
print(R)
