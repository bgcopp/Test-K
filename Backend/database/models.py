"""
KRONOS Database Models - SQLAlchemy ORM
=======================================================================
Modelos SQLAlchemy que corresponden al esquema de la base de datos SQLite
de KRONOS. Incluye todas las relaciones, validaciones y métodos de
utilidad necesarios para la aplicación.

Características principales:
- Modelos que corresponden exactamente al schema.sql
- Relaciones optimizadas para consultas frecuentes
- Validaciones de integridad de datos
- Métodos de serialización para API JSON
- Soporte completo para operaciones CRUD
=======================================================================
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
import json
from sqlalchemy import (
    Column, String, Text, Integer, Float, DateTime, ForeignKey,
    CheckConstraint, UniqueConstraint, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func

Base = declarative_base()


class BaseModel:
    """Clase base con métodos comunes para todos los modelos"""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el modelo a diccionario para serialización JSON"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                result[column.name] = value.isoformat()
            else:
                result[column.name] = value
        return result
    
    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """Actualiza el modelo desde un diccionario"""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)


class Role(Base, BaseModel):
    """Modelo para la tabla roles"""
    __tablename__ = 'roles'
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    permissions = Column(Text, nullable=False)  # JSON string
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp())
    
    # Relaciones
    users = relationship("User", back_populates="role")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("length(trim(name)) > 0", name='ck_role_name_not_empty'),
        Index('idx_roles_name', 'name'),
    )
    
    @validates('permissions')
    def validate_permissions(self, key, permissions):
        """Valida que permissions sea JSON válido"""
        try:
            json.loads(permissions)
            return permissions
        except (json.JSONDecodeError, TypeError):
            raise ValueError("permissions must be valid JSON")
    
    def get_permissions_dict(self) -> Dict[str, Any]:
        """Retorna permissions como diccionario"""
        return json.loads(self.permissions)
    
    def set_permissions_dict(self, permissions_dict: Dict[str, Any]) -> None:
        """Establece permissions desde un diccionario"""
        self.permissions = json.dumps(permissions_dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialización personalizada incluyendo permissions como dict"""
        result = super().to_dict()
        result['permissions'] = self.get_permissions_dict()
        return result
    
    def __repr__(self):
        return f"<Role(id='{self.id}', name='{self.name}')>"


class User(Base, BaseModel):
    """Modelo para la tabla users"""
    __tablename__ = 'users'
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    role_id = Column(String, ForeignKey('roles.id'), nullable=False)
    status = Column(String, nullable=False, default='active')
    avatar = Column(String)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp())
    last_login = Column(DateTime)
    
    # Relaciones
    role = relationship("Role", back_populates="users")
    created_missions = relationship("Mission", back_populates="creator")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("length(trim(name)) > 0", name='ck_user_name_not_empty'),
        CheckConstraint("length(trim(email)) > 0 AND email LIKE '%@%.%'", name='ck_user_email_format'),
        CheckConstraint("length(password_hash) >= 60", name='ck_user_password_hash_length'),
        CheckConstraint("status IN ('active', 'inactive')", name='ck_user_status_values'),
        Index('idx_users_email', 'email'),
        Index('idx_users_role_status', 'role_id', 'status'),
        Index('idx_users_last_login', 'last_login'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialización excluyendo password_hash y compatible con frontend"""
        result = super().to_dict()
        result.pop('password_hash', None)  # Nunca exponer el hash
        # Compatibilidad con frontend: role_id -> roleId
        if 'role_id' in result:
            result['roleId'] = result.pop('role_id')
        return result
    
    def has_permission(self, resource: str, action: str) -> bool:
        """Verifica si el usuario tiene un permiso específico"""
        permissions = self.role.get_permissions_dict()
        resource_perms = permissions.get(resource, {})
        return resource_perms.get(action, False)
    
    def __repr__(self):
        return f"<User(id='{self.id}', email='{self.email}', status='{self.status}')>"


class Mission(Base, BaseModel):
    """Modelo para la tabla missions"""
    __tablename__ = 'missions'
    
    id = Column(String, primary_key=True)
    code = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    status = Column(String, nullable=False, default='Planificación')
    start_date = Column(String, nullable=False)  # Stored as string to match frontend
    end_date = Column(String)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp())
    created_by = Column(String, ForeignKey('users.id'))
    
    # Relaciones
    creator = relationship("User", back_populates="created_missions")
    cellular_data = relationship("CellularData", back_populates="mission", cascade="all, delete-orphan")
    target_records = relationship("TargetRecord", back_populates="mission", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("length(trim(code)) > 0", name='ck_mission_code_not_empty'),
        CheckConstraint("length(trim(name)) > 0", name='ck_mission_name_not_empty'),
        CheckConstraint(
            "status IN ('Planificación', 'En Progreso', 'Completada', 'Cancelada')",
            name='ck_mission_status_values'
        ),
        Index('idx_missions_code', 'code'),
        Index('idx_missions_status_dates', 'status', 'start_date', 'end_date'),
        Index('idx_missions_created_by', 'created_by'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialización completa incluyendo datos relacionados y compatible con frontend"""
        result = super().to_dict()
        
        # Compatibilidad con frontend: campos en camelCase
        if 'start_date' in result:
            result['startDate'] = result.pop('start_date')
        if 'end_date' in result:
            result['endDate'] = result.pop('end_date')
        if 'created_at' in result:
            result['createdAt'] = result.pop('created_at')
        if 'updated_at' in result:
            result['updatedAt'] = result.pop('updated_at')
        if 'created_by' in result:
            result['createdBy'] = result.pop('created_by')
        
        # Incluir datos celulares (solo si se solicitan explícitamente)
        # Para evitar N+1 queries, estos se cargarán bajo demanda
        if hasattr(self, '_include_relations') and self._include_relations:
            result['cellularData'] = [cd.to_dict() for cd in self.cellular_data] if self.cellular_data else []
            result['operatorData'] = []  # Mantener estructura para compatibilidad con frontend
        
        return result
    
    def to_dict_with_relations(self) -> Dict[str, Any]:
        """Serialización completa incluyendo todas las relaciones"""
        self._include_relations = True
        result = self.to_dict()
        delattr(self, '_include_relations')
        return result
    
    def get_stats(self) -> Dict[str, int]:
        """Retorna estadísticas de la misión"""
        return {
            'cellularRecordsCount': len(self.cellular_data) if self.cellular_data else 0,
            'operatorSheetsCount': 0,  # Mantener para compatibilidad con frontend
            'targetRecordsCount': len(self.target_records) if self.target_records else 0
        }
    
    def __repr__(self):
        return f"<Mission(id='{self.id}', code='{self.code}', status='{self.status}')>"


class CellularData(Base, BaseModel):
    """Modelo para la tabla cellular_data expandida con todos los campos SCANHUNTER"""
    __tablename__ = 'cellular_data'
    
    # Identificación
    id = Column(Integer, primary_key=True, autoincrement=True)
    mission_id = Column(String, ForeignKey('missions.id'), nullable=False)
    
    # Información del punto de medición
    punto = Column(String, nullable=False)           # Nombre o código del punto
    
    # Ubicación geográfica
    lat = Column(Float, nullable=False)              # Latitud (grados decimales)
    lon = Column(Float, nullable=False)              # Longitud (grados decimales)
    
    # Información de red
    mnc_mcc = Column(String, nullable=False)         # Mobile Network Code + Mobile Country Code
    operator = Column(String, nullable=False)        # Nombre del operador
    
    # Métricas de señal
    rssi = Column(Integer, nullable=False)           # RSSI en dBm (valores negativos)
    
    # Información técnica celular
    tecnologia = Column(String, nullable=False)      # GSM, UMTS, LTE, 5G NR, etc.
    cell_id = Column(String, nullable=False)         # Identificador de celda
    lac_tac = Column(String)                         # LAC (2G/3G) o TAC (4G/5G)
    enb = Column(String)                            # eNodeB ID (LTE) o gNB ID (5G)
    channel = Column(String)                        # Canal de frecuencia
    
    # Información adicional
    comentario = Column(Text)                       # Observaciones, contexto temporal
    
    # Auditoría
    created_at = Column(DateTime, default=func.current_timestamp())
    
    # Relaciones
    mission = relationship("Mission", back_populates="cellular_data")
    
    # Constraints y validaciones
    __table_args__ = (
        # Validaciones geográficas
        CheckConstraint("lat >= -90.0 AND lat <= 90.0", name='ck_cellular_lat_range'),
        CheckConstraint("lon >= -180.0 AND lon <= 180.0", name='ck_cellular_lon_range'),
        
        # Validaciones de campos obligatorios
        CheckConstraint("length(trim(punto)) > 0", name='ck_cellular_punto_not_empty'),
        CheckConstraint("length(trim(mnc_mcc)) >= 5", name='ck_cellular_mnc_mcc_length'),
        CheckConstraint("length(trim(operator)) > 0", name='ck_cellular_operator_not_empty'),
        CheckConstraint("length(trim(tecnologia)) > 0", name='ck_cellular_tecnologia_not_empty'),
        CheckConstraint("length(trim(cell_id)) > 0", name='ck_cellular_cell_id_not_empty'),
        
        # RSSI debe ser negativo (típico en telecomunicaciones)
        CheckConstraint("rssi <= 0", name='ck_cellular_rssi_negative'),
        
        # Validación de tecnología (valores conocidos)
        CheckConstraint(
            "tecnologia IN ('GSM', 'UMTS', '3G', 'LTE', '4G', '5G NR', '5G')",
            name='ck_cellular_tecnologia_values'
        ),
        
        # Validación de formato MNC+MCC (números solamente)
        CheckConstraint(
            "mnc_mcc GLOB '[0-9]*' AND length(mnc_mcc) BETWEEN 5 AND 6",
            name='ck_cellular_mnc_mcc_format'
        ),
        
        # Validaciones opcionales para campos que pueden estar vacíos
        CheckConstraint("lac_tac IS NULL OR length(trim(lac_tac)) > 0", name='ck_cellular_lac_tac_valid'),
        CheckConstraint("enb IS NULL OR length(trim(enb)) > 0", name='ck_cellular_enb_valid'),
        CheckConstraint("channel IS NULL OR length(trim(channel)) > 0", name='ck_cellular_channel_valid'),
        
        # Índices críticos para consultas frecuentes
        Index('idx_cellular_mission_id', 'mission_id'),
        Index('idx_cellular_operator', 'operator'),
        Index('idx_cellular_tecnologia', 'tecnologia'),
        Index('idx_cellular_rssi', 'rssi'),
        Index('idx_cellular_punto', 'punto'),
        Index('idx_cellular_cell_id', 'cell_id'),
        Index('idx_cellular_mnc_mcc', 'mnc_mcc'),
        Index('idx_cellular_lac_tac', 'lac_tac'),
        Index('idx_cellular_enb', 'enb'),
        
        # Índices compuestos para consultas específicas de KRONOS
        Index('idx_cellular_mission_operator', 'mission_id', 'operator'),
        Index('idx_cellular_mission_tech', 'mission_id', 'tecnologia'),
        Index('idx_cellular_location', 'lat', 'lon'),
        Index('idx_cellular_geo_analysis', 'mission_id', 'operator', 'lat', 'lon', 'rssi'),
        Index('idx_cellular_coverage_analysis', 'mission_id', 'tecnologia', 'operator', 'rssi'),
    )
    
    @validates('tecnologia')
    def validate_tecnologia(self, key, tecnologia):
        """Valida que la tecnología sea un valor conocido"""
        valid_technologies = {'GSM', 'UMTS', '3G', 'LTE', '4G', '5G NR', '5G'}
        if tecnologia not in valid_technologies:
            raise ValueError(f"Tecnología debe ser uno de: {', '.join(valid_technologies)}")
        return tecnologia
    
    @validates('mnc_mcc')
    def validate_mnc_mcc(self, key, mnc_mcc):
        """Valida formato de MNC+MCC"""
        if not mnc_mcc.isdigit() or len(mnc_mcc) not in [5, 6]:
            raise ValueError("MNC+MCC debe contener solo números y tener 5-6 dígitos")
        return mnc_mcc
    
    @validates('rssi')
    def validate_rssi(self, key, rssi):
        """Valida que RSSI sea un valor negativo realista"""
        if rssi > 0:
            raise ValueError("RSSI debe ser un valor negativo (dBm)")
        if rssi < -150:  # Valor extremadamente bajo, posiblemente error
            raise ValueError("RSSI parece demasiado bajo, verificar medición")
        return rssi
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialización expandida para compatibilidad con frontend SCANHUNTER"""
        result = super().to_dict()
        
        # Convertir coordenadas a strings para coincidir con el frontend
        result['lat'] = str(result['lat']) if result.get('lat') is not None else ''
        result['lon'] = str(result['lon']) if result.get('lon') is not None else ''
        
        # Mapeo completo para compatibilidad con frontend (camelCase)
        mapping = {
            'mnc_mcc': 'mncMcc',
            'cell_id': 'cellId', 
            'lac_tac': 'lacTac',
            'operator': 'operador',  # Cambiar operator a operador para el frontend
            'created_at': 'createdAt'
        }
        
        for backend_key, frontend_key in mapping.items():
            if backend_key in result:
                result[frontend_key] = result.pop(backend_key)
        
        # Asegurar que campos opcionales tengan valores por defecto
        optional_fields = ['lacTac', 'enb', 'channel', 'comentario']
        for field in optional_fields:
            if field not in result or result[field] is None:
                result[field] = None
        
        return result
    
    def get_signal_quality(self) -> str:
        """Retorna la calidad de la señal basada en RSSI"""
        if self.rssi >= -70:
            return 'Excelente'
        elif self.rssi >= -85:
            return 'Buena'
        elif self.rssi >= -100:
            return 'Regular'
        else:
            return 'Mala'
    
    def is_lte_or_better(self) -> bool:
        """Verifica si la tecnología es LTE o superior"""
        return self.tecnologia in ['LTE', '4G', '5G NR', '5G']
    
    def get_location_string(self) -> str:
        """Retorna coordenadas como string para display"""
        return f"{self.lat:.6f}, {self.lon:.6f}"
    
    def __repr__(self):
        return f"<CellularData(id={self.id}, punto='{self.punto}', operator='{self.operator}', rssi={self.rssi}, tech='{self.tecnologia}')>"




class TargetRecord(Base, BaseModel):
    """Modelo para la tabla target_records"""
    __tablename__ = 'target_records'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    mission_id = Column(String, ForeignKey('missions.id'), nullable=False)
    target_id = Column(String, nullable=False)
    operator = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    signal = Column(Integer, nullable=False)
    towers = Column(Integer, nullable=False)
    coverage = Column(String, nullable=False)
    source_sheet = Column(String, nullable=False)
    analysis_date = Column(DateTime, default=func.current_timestamp())
    
    # Relaciones
    mission = relationship("Mission", back_populates="target_records")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("lat >= -90.0 AND lat <= 90.0", name='ck_target_lat_range'),
        CheckConstraint("lon >= -180.0 AND lon <= 180.0", name='ck_target_lon_range'),
        CheckConstraint("signal <= 0", name='ck_target_signal_negative'),
        CheckConstraint("towers > 0", name='ck_target_towers_positive'),
        CheckConstraint("length(trim(target_id)) > 0", name='ck_target_id_not_empty'),
        CheckConstraint("length(trim(operator)) > 0", name='ck_target_operator_not_empty'),
        CheckConstraint("length(trim(source_sheet)) > 0", name='ck_target_source_sheet_not_empty'),
        UniqueConstraint('mission_id', 'target_id', name='uq_target_records_mission_target'),
        Index('idx_target_records_mission', 'mission_id'),
        Index('idx_target_records_operator', 'operator'),
        Index('idx_target_records_signal', 'signal'),
        Index('idx_target_records_location', 'lat', 'lon'),
        Index('idx_target_records_analysis_date', 'analysis_date'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialización para compatibilidad con frontend"""
        result = super().to_dict()
        # Convertir campos para coincidir con la interfaz TypeScript
        result['targetId'] = result.pop('target_id')
        result['sourceSheet'] = result.pop('source_sheet')
        result['lat'] = str(result['lat'])
        result['lon'] = str(result['lon'])
        return result
    
    def __repr__(self):
        return f"<TargetRecord(target_id='{self.target_id}', operator='{self.operator}')>"


# ============================================================================
# FUNCIONES DE UTILIDAD
# ============================================================================

def get_all_models():
    """Retorna todos los modelos definidos"""
    return [Role, User, Mission, CellularData, TargetRecord]


def create_all_tables(engine):
    """Crea todas las tablas en la base de datos"""
    Base.metadata.create_all(engine)


def drop_all_tables(engine):
    """Elimina todas las tablas de la base de datos (usar con cuidado)"""
    Base.metadata.drop_all(engine)