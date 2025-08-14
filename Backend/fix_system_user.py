#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para crear el usuario SYSTEM necesario para los triggers de auditoría
"""

import sys
import os
from datetime import datetime
from pathlib import Path

# Agregar el directorio Backend al path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from database.connection import db_manager
from database.models import User
from werkzeug.security import generate_password_hash
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar el DatabaseManager
db_manager.initialize()

def create_system_user():
    """Crea el usuario SYSTEM si no existe"""
    try:
        with db_manager.get_session() as session:
            # Verificar si el usuario SYSTEM ya existe
            system_user = session.query(User).filter_by(id='SYSTEM').first()
            
            if system_user:
                logger.info("✅ El usuario SYSTEM ya existe en la base de datos")
                logger.info(f"   - ID: {system_user.id}")
                logger.info(f"   - Nombre: {system_user.name}")
                logger.info(f"   - Email: {system_user.email}")
                return True
                
            # Crear el usuario SYSTEM
            logger.info("🔧 Creando usuario SYSTEM...")
            
            system_user = User(
                id='SYSTEM',
                email='system@kronos.internal',
                name='Sistema Automatizado',
                password_hash=generate_password_hash('SystemPassword2024!'),  # Password no será usado
                role_id='admin',  # Asignar rol admin por defecto
                status='active',
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            session.add(system_user)
            session.commit()
            
            logger.info("✅ Usuario SYSTEM creado exitosamente")
            logger.info(f"   - ID: {system_user.id}")
            logger.info(f"   - Nombre: {system_user.name}")
            logger.info(f"   - Email: {system_user.email}")
            logger.info(f"   - Role: {system_user.role_id}")
            
            return True
        
    except Exception as e:
        logger.error(f"❌ Error al crear usuario SYSTEM: {str(e)}")
        return False

def verify_system_user():
    """Verifica que el usuario SYSTEM puede ser usado por los triggers"""
    try:
        with db_manager.get_session() as session:
            # Verificar que el usuario existe
            system_user = session.query(User).filter_by(id='SYSTEM').first()
            
            if not system_user:
                logger.error("❌ Usuario SYSTEM no encontrado")
                return False
                
            # Verificar que está activo
            if system_user.status != 'active':
                logger.warning("⚠️ Usuario SYSTEM existe pero no está activo")
                system_user.status = 'active'
                session.commit()
                logger.info("✅ Usuario SYSTEM activado")
                
            logger.info("✅ Usuario SYSTEM verificado y listo para usar")
            return True
        
    except Exception as e:
        logger.error(f"❌ Error verificando usuario SYSTEM: {str(e)}")
        return False

def main():
    """Función principal"""
    logger.info("=" * 60)
    logger.info("SCRIPT DE CORRECCIÓN - USUARIO SYSTEM")
    logger.info("=" * 60)
    
    # Crear usuario SYSTEM
    if create_system_user():
        logger.info("\n✅ PASO 1: Usuario SYSTEM creado/verificado")
    else:
        logger.error("\n❌ PASO 1: Error creando usuario SYSTEM")
        return 1
        
    # Verificar que está listo para usar
    if verify_system_user():
        logger.info("\n✅ PASO 2: Usuario SYSTEM verificado")
    else:
        logger.error("\n❌ PASO 2: Error verificando usuario SYSTEM")
        return 1
        
    logger.info("\n" + "=" * 60)
    logger.info("✅ CORRECCIÓN COMPLETADA EXITOSAMENTE")
    logger.info("El sistema ahora puede procesar archivos de operador sin errores")
    logger.info("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())