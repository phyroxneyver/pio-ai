from sqlalchemy import Column, Integer, String

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    # Aquí es donde va el hash, NUNCA la contraseña en plano
    hashed_password = Column(String(255), nullable=False) 
