from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, Literal




class AveCreate(BaseModel):
    # ✅ CAMBIO 1: Agregamos "huevo" a la lista Literal permitida
    tipo: Literal["pollito", "gallina", "huevo"] = Field(..., description="Tipo: 'pollito', 'gallina' o 'huevo'")
    
    # ✅ CAMBIO 2: Cambiamos gt=0 (mayor estricto) por ge=0 (mayor o igual)
    # Esto permite guardar un conteo de 0 cuando la IA se equivoca por completo.
    cantidad: int = Field(..., ge=0, description="La cantidad debe ser mayor o igual a 0")
    
    raza: Optional[str] = None
    notas: Optional[str] = None


class AveUpdate(BaseModel):
    # ✅ CAMBIO 3: También permitimos "huevo" en la actualización
    tipo: Optional[Literal["pollito", "gallina", "huevo"]] = None
    
    # ✅ CAMBIO 4: Permitimos 0 en la actualización
    cantidad: Optional[int] = Field(None, ge=0, description="La cantidad debe ser mayor o igual a 0")
    
    raza: Optional[str] = None
    notas: Optional[str] = None


class AveResponse(BaseModel):
    id: int
    tipo: str
    cantidad: int
    raza: Optional[str]
    fecha_ingreso: datetime
    notas: Optional[str]

    model_config = ConfigDict(from_attributes=True)




class ProduccionCreate(BaseModel):
    ave_id: int = Field(..., description="ID del ave asociada")
    cantidad_huevos: int = Field(..., gt=0, description="La cantidad de huevos debe ser mayor a 0")
    notas: Optional[str] = None


class ProduccionUpdate(BaseModel):
    cantidad_huevos: Optional[int] = Field(None, gt=0, description="La cantidad de huevos debe ser mayor a 0")
    notas: Optional[str] = None


class ProduccionResponse(BaseModel):
    id: int
    ave_id: int
    cantidad_huevos: int
    fecha: datetime
    notas: Optional[str]

    model_config = ConfigDict(from_attributes=True)