-- ============================================================================
-- KRONOS Initial Data - SQLite
-- ============================================================================
-- Este archivo contiene los datos iniciales para la base de datos KRONOS
-- basados en los mockData del frontend.
--
-- IMPORTANTE: Las contraseñas se almacenan como placeholders y DEBEN ser
-- hasheadas usando BCrypt en Python antes de la inserción.
-- ============================================================================

-- Verificar que foreign keys estén habilitadas
PRAGMA foreign_keys = ON;

BEGIN TRANSACTION;

-- ============================================================================
-- ROLES INICIALES
-- ============================================================================
-- Basado en initialRoles de mockData.ts

-- 1. Super Administrador - Permisos completos
INSERT INTO roles (id, name, permissions) VALUES (
    '1',
    'Super Administrador',
    '{
        "users": {"create": true, "read": true, "update": true, "delete": true},
        "roles": {"create": true, "read": true, "update": true, "delete": true},
        "missions": {"create": true, "read": true, "update": true, "delete": true},
        "dashboard": {"read": true},
        "targetAnalysis": {"execute": true}
    }'
);

-- 2. Editor de Misiones - Permisos de edición de misiones
INSERT INTO roles (id, name, permissions) VALUES (
    '2',
    'Editor de Misiones',
    '{
        "users": {"create": false, "read": true, "update": false, "delete": false},
        "roles": {"create": false, "read": true, "update": false, "delete": false},
        "missions": {"create": true, "read": true, "update": true, "delete": false},
        "dashboard": {"read": true},
        "targetAnalysis": {"execute": true}
    }'
);

-- 3. Visualizador - Solo permisos de lectura
INSERT INTO roles (id, name, permissions) VALUES (
    '3',
    'Visualizador',
    '{
        "users": {"create": false, "read": true, "update": false, "delete": false},
        "roles": {"create": false, "read": true, "update": false, "delete": false},
        "missions": {"create": false, "read": true, "update": false, "delete": false},
        "dashboard": {"read": true},
        "targetAnalysis": {"execute": false}
    }'
);

-- ============================================================================
-- USUARIOS INICIALES
-- ============================================================================
-- Basado en initialUsers de mockData.ts
-- NOTA: Los password_hash aquí son placeholders. En producción estos deben
-- ser generados usando BCrypt en Python.

-- Usuario administrador principal
INSERT INTO users (id, name, email, password_hash, role_id, status, avatar) VALUES (
    'admin',
    'Administrador KRONOS',
    'admin@example.com',
    '$2b$12$PLACEHOLDER_HASH_TO_BE_REPLACED_BY_PYTHON_SCRIPT', -- password: "password"
    '1',
    'active',
    'https://picsum.photos/seed/admin/100/100'
);

-- Usuarios de ejemplo basados en mockData
INSERT INTO users (id, name, email, password_hash, role_id, status, avatar) VALUES 
(
    'u1',
    'Alice Johnson',
    'alice.j@example.com',
    '$2b$12$PLACEHOLDER_HASH_TO_BE_REPLACED_BY_PYTHON_SCRIPT',
    '1',
    'active',
    'https://picsum.photos/seed/alice/100/100'
),
(
    'u2',
    'Bob Williams',
    'bob.w@example.com',
    '$2b$12$PLACEHOLDER_HASH_TO_BE_REPLACED_BY_PYTHON_SCRIPT',
    '2',
    'active',
    'https://picsum.photos/seed/bob/100/100'
),
(
    'u3',
    'Charlie Brown',
    'charlie.b@example.com',
    '$2b$12$PLACEHOLDER_HASH_TO_BE_REPLACED_BY_PYTHON_SCRIPT',
    '3',
    'inactive',
    'https://picsum.photos/seed/charlie/100/100'
),
(
    'u4',
    'Diana Prince',
    'diana.p@example.com',
    '$2b$12$PLACEHOLDER_HASH_TO_BE_REPLACED_BY_PYTHON_SCRIPT',
    '2',
    'active',
    'https://picsum.photos/seed/diana/100/100'
),
(
    'u5',
    'Ethan Hunt',
    'ethan.h@example.com',
    '$2b$12$PLACEHOLDER_HASH_TO_BE_REPLACED_BY_PYTHON_SCRIPT',
    '3',
    'active',
    'https://picsum.photos/seed/ethan/100/100'
);

-- ============================================================================
-- MISIONES DE EJEMPLO
-- ============================================================================
-- Basado en initialMissions de mockData.ts

INSERT INTO missions (id, code, name, description, status, start_date, end_date, created_by) VALUES 
(
    'm1',
    'PX-001',
    'Proyecto Fénix',
    'Investigar anomalías de rayos cósmicos en la galaxia de Andrómeda.',
    'En Progreso',
    '2023-01-15',
    '2024-12-31',
    'u1'
),
(
    'm2',
    'DD-002',
    'Operación Inmersión Profunda',
    'Explorar la Fosa de las Marianas en busca de nuevas especies biológicas.',
    'Completada',
    '2022-05-20',
    '2023-05-19',
    'u1'
),
(
    'm3',
    'AS-003',
    'Centinela del Ártico',
    'Monitorear las tasas de derretimiento de los casquetes polares y el impacto climático.',
    'Planificación',
    '2025-02-01',
    '2026-02-01',
    'u2'
),
(
    'm4',
    'PC-004',
    'Proyecto Quimera',
    'Investigación genética de extremófilos para la colonización espacial.',
    'Cancelada',
    '2023-08-01',
    '2024-08-01',
    'u4'
);

-- ============================================================================
-- DATOS CELULARES DE EJEMPLO
-- ============================================================================
-- Datos para el Proyecto Fénix (m1) basados en mockData

INSERT INTO cellular_data (mission_id, lat, lon, signal, operator) VALUES 
('m1', 34.0522, -118.2437, -85, 'T-Mobile'),
('m1', 34.0533, -118.2448, -92, 'Verizon'),
('m1', 34.0544, -118.2459, -78, 'T-Mobile'),
('m1', 34.0555, -118.2460, -99, 'ATT');

-- ============================================================================
-- HOJAS DE OPERADORES DE EJEMPLO
-- ============================================================================
-- Basado en los operatorData de mockData

INSERT INTO operator_sheets (id, mission_id, name) VALUES 
('sheet-1', 'm1', 'Datos T-Mobile Q1 2024'),
('sheet-2', 'm1', 'Datos Verizon Q1 2024');

-- ============================================================================
-- REGISTROS DE DATOS DE OPERADORES
-- ============================================================================

-- Datos para la hoja de T-Mobile
INSERT INTO operator_data_records (sheet_id, operator_id, name, towers, coverage) VALUES 
('sheet-1', 'OP-TM-1001', 'T-Mobile', 150, '95.7%'),
('sheet-1', 'OP-TM-1002', 'T-Mobile', 20, '88.1%');

-- Datos para la hoja de Verizon
INSERT INTO operator_data_records (sheet_id, operator_id, name, towers, coverage) VALUES 
('sheet-2', 'OP-VZ-2001', 'Verizon', 210, '98.2%');

-- ============================================================================
-- DATOS DE EJEMPLO PARA ANÁLISIS
-- ============================================================================
-- Algunos registros de ejemplo en target_records para mostrar funcionalidad
-- En producción, estos se generarían mediante el proceso de análisis

INSERT INTO target_records (
    mission_id, target_id, operator, lat, lon, signal, towers, coverage, source_sheet
) VALUES 
('m1', 't_1_101', 'T-Mobile', 34.0522, -118.2437, -85, 150, '95.7%', 'Datos T-Mobile Q1 2024'),
('m1', 't_3_101', 'T-Mobile', 34.0544, -118.2459, -78, 150, '95.7%', 'Datos T-Mobile Q1 2024'),
('m1', 't_2_201', 'Verizon', 34.0533, -118.2448, -92, 210, '98.2%', 'Datos Verizon Q1 2024');

COMMIT;

-- ============================================================================
-- VERIFICACIONES POST-INSERCIÓN
-- ============================================================================
-- Estas consultas verifican que los datos se insertaron correctamente

.print "=== VERIFICACIÓN DE DATOS INICIALES ==="

.print "Roles creados:"
SELECT COUNT(*) as count FROM roles;

.print "Usuarios creados:"
SELECT COUNT(*) as count FROM users;

.print "Misiones creadas:"
SELECT COUNT(*) as count FROM missions;

.print "Datos celulares:"
SELECT mission_id, COUNT(*) as records FROM cellular_data GROUP BY mission_id;

.print "Hojas de operadores:"
SELECT mission_id, COUNT(*) as sheets FROM operator_sheets GROUP BY mission_id;

.print "Registros de análisis:"
SELECT mission_id, COUNT(*) as targets FROM target_records GROUP BY mission_id;

.print "=== DATOS INICIALES CARGADOS EXITOSAMENTE ==="