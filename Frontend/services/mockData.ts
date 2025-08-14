import type { User, Role, Mission, Permissions } from '../types';
import { MissionStatus } from '../types';

const fullPermissions: Permissions = {
    users: { create: true, read: true, update: true, delete: true },
    roles: { create: true, read: true, update: true, delete: true },
    missions: { create: true, read: true, update: true, delete: true },
    dashboard: { read: true },
    targetAnalysis: { execute: true },
};

const editorPermissions: Permissions = {
    users: { create: false, read: true, update: false, delete: false },
    roles: { create: false, read: true, update: false, delete: false },
    missions: { create: true, read: true, update: true, delete: false },
    dashboard: { read: true },
    targetAnalysis: { execute: true },
};

const viewerPermissions: Permissions = {
    users: { create: false, read: true, update: false, delete: false },
    roles: { create: false, read: true, update: false, delete: false },
    missions: { create: false, read: true, update: false, delete: false },
    dashboard: { read: true },
    targetAnalysis: { execute: false },
};

export const initialRoles: Role[] = [
    { id: '1', name: 'Super Administrador', permissions: fullPermissions },
    { id: '2', name: 'Editor de Misiones', permissions: editorPermissions },
    { id: '3', name: 'Visualizador', permissions: viewerPermissions },
];

export const initialUsers: User[] = [
    { id: 'u1', name: 'Alice Johnson', email: 'alice.j@example.com', roleId: '1', status: 'active', avatar: 'https://picsum.photos/seed/alice/100/100' },
    { id: 'u2', name: 'Bob Williams', email: 'bob.w@example.com', roleId: '2', status: 'active', avatar: 'https://picsum.photos/seed/bob/100/100' },
    { id: 'u3', name: 'Charlie Brown', email: 'charlie.b@example.com', roleId: '3', status: 'inactive', avatar: 'https://picsum.photos/seed/charlie/100/100' },
    { id: 'u4', name: 'Diana Prince', email: 'diana.p@example.com', roleId: '2', status: 'active', avatar: 'https://picsum.photos/seed/diana/100/100' },
    { id: 'u5', name: 'Ethan Hunt', email: 'ethan.h@example.com', roleId: '3', status: 'active', avatar: 'https://picsum.photos/seed/ethan/100/100' },
];

export const initialMissions: Mission[] = [
    { 
        id: 'm1', 
        code: 'PX-001', 
        name: 'Proyecto Fénix', 
        description: 'Investigar anomalías de rayos cósmicos en la galaxia de Andrómeda.', 
        status: MissionStatus.IN_PROGRESS, 
        startDate: '2023-01-15', 
        endDate: '2024-12-31', 
        cellularData: [
            { 
                id: 1, 
                punto: 'PT-001', 
                lat: '34.0522', 
                lon: '-118.2437', 
                mncMcc: '310260', 
                operador: 'T-Mobile', 
                rssi: -85, 
                tecnologia: 'LTE', 
                cellId: 'TMO-LA-001',
                lacTac: '12345',
                enb: 'eNB-001',
                channel: '1875',
                comentario: 'Zona residencial, señal estable'
            },
            { 
                id: 2, 
                punto: 'PT-002', 
                lat: '34.0533', 
                lon: '-118.2448', 
                mncMcc: '311480', 
                operador: 'Verizon', 
                rssi: -92, 
                tecnologia: '5G', 
                cellId: 'VZW-LA-045',
                lacTac: '23456',
                enb: 'gNB-045',
                channel: '3750',
                comentario: 'Centro comercial, alta densidad'
            },
            { 
                id: 3, 
                punto: 'PT-003', 
                lat: '34.0544', 
                lon: '-118.2459', 
                mncMcc: '310260', 
                operador: 'T-Mobile', 
                rssi: -78, 
                tecnologia: 'LTE', 
                cellId: 'TMO-LA-002',
                lacTac: '12346',
                comentario: 'Área industrial, interferencias ocasionales'
            },
            { 
                id: 4, 
                punto: 'PT-004', 
                lat: '34.0555', 
                lon: '-118.2460', 
                mncMcc: '310410', 
                operador: 'AT&T', 
                rssi: -99, 
                tecnologia: 'UMTS', 
                cellId: 'ATT-LA-078',
                lacTac: '34567',
                channel: '1900',
                comentario: 'Zona rural, cobertura limitada'
            },
        ], 
        operatorData: [
            {
                id: 'sheet-1',
                name: 'Datos T-Mobile Q1 2024',
                data: [
                    { id: 101, operatorId: 'OP-TM-1001', name: 'T-Mobile', towers: 150, coverage: '95.7%' },
                    { id: 102, operatorId: 'OP-TM-1002', name: 'T-Mobile', towers: 20, coverage: '88.1%' },
                ]
            },
            {
                id: 'sheet-2',
                name: 'Datos Verizon Q1 2024',
                data: [
                    { id: 201, operatorId: 'OP-VZ-2001', name: 'Verizon', towers: 210, coverage: '98.2%' },
                ]
            }
        ] 
    },
    { id: 'm2', code: 'DD-002', name: 'Operación Inmersión Profunda', description: 'Explorar la Fosa de las Marianas en busca de nuevas especies biológicas.', status: MissionStatus.COMPLETED, startDate: '2022-05-20', endDate: '2023-05-19', cellularData: [], operatorData: [] },
    { id: 'm3', code: 'AS-003', name: 'Centinela del Ártico', description: 'Monitorear las tasas de derretimiento de los casquetes polares y el impacto climático.', status: MissionStatus.PLANNING, startDate: '2025-02-01', endDate: '2026-02-01', cellularData: [], operatorData: [] },
    { id: 'm4', code: 'PC-004', name: 'Proyecto Quimera', description: 'Investigación genética de extremófilos para la colonización espacial.', status: MissionStatus.CANCELLED, startDate: '2023-08-01', endDate: '2024-08-01', cellularData: [], operatorData: [] },
];

export const permissionLabels: { [key in keyof Permissions]?: { label: string; permissions: { [key: string]: string } } } = {
    dashboard: { label: 'Panel de Control', permissions: { read: 'Ver Panel de Control' } },
    users: { label: 'Gestión de Usuarios', permissions: { create: 'Crear Usuarios', read: 'Ver Usuarios', update: 'Actualizar Usuarios', delete: 'Eliminar Usuarios' } },
    roles: { label: 'Gestión de Roles', permissions: { create: 'Crear Roles', read: 'Ver Roles', update: 'Actualizar Roles', delete: 'Eliminar Roles' } },
    missions: { label: 'Gestión de Misiones', permissions: { create: 'Crear Misiones', read: 'Ver Misiones', update: 'Actualizar Misiones', delete: 'Eliminar Misiones' } },
    targetAnalysis: { label: 'Posibles Objetivos', permissions: { execute: 'Ejecutar Análisis' } },
};