import React, { useState } from 'react';
import type { Role, Permissions } from '../types';
import { permissionLabels } from '../services/mockData';
import Table from '../components/ui/Table';
import Button from '../components/ui/Button';
import Modal from '../components/ui/Modal';
import Input from '../components/ui/Input';
import Checkbox from '../components/ui/Checkbox';
import { ICONS } from '../constants';
import { createRole, updateRole, deleteRole } from '../services/api';

interface RolesProps {
    roles: Role[];
    setRoles: React.Dispatch<React.SetStateAction<Role[]>>;
}

const Roles: React.FC<RolesProps> = ({ roles, setRoles }) => {
    const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
    const [editingRole, setEditingRole] = useState<Role | null>(null);
    const [currentPermissions, setCurrentPermissions] = useState<Permissions>(permissionLabels as any);
    const [isLoading, setIsLoading] = useState(false);

    const getBlankPermissions = () => {
        return JSON.parse(JSON.stringify(Object.keys(permissionLabels).reduce((acc, key) => {
            const moduleInfo = permissionLabels[key as keyof typeof permissionLabels];
            if (!moduleInfo) return acc;
            return {
                ...acc,
                [key]: Object.keys(moduleInfo.permissions).reduce((pAcc, pKey) => ({...pAcc, [pKey]: false}), {})
            }
        }, {})));
    };

    const openModal = (role: Role | null = null) => {
        setEditingRole(role);
        if (role) {
            setCurrentPermissions(role.permissions);
        } else {
            setCurrentPermissions(getBlankPermissions());
        }
        setIsModalOpen(true);
    };

    const closeModal = () => {
        setIsModalOpen(false);
        setEditingRole(null);
    };
    
    const handlePermissionChange = (module: keyof Permissions, action: string, value: boolean) => {
        setCurrentPermissions(prev => ({
            ...prev,
            [module]: {
                ...prev[module],
                [action]: value,
            }
        }));
    };
    
    const handleSaveRole = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setIsLoading(true);
        const formData = new FormData(e.currentTarget);
        const roleName = formData.get('name') as string;
        const roleData = { name: roleName, permissions: currentPermissions };

        try {
            if (editingRole) {
                const updatedRole = await updateRole(editingRole.id, roleData);
                setRoles(roles.map(r => r.id === editingRole.id ? updatedRole : r));
            } else {
                const newRole = await createRole(roleData);
                setRoles([...roles, newRole]);
            }
            closeModal();
        } catch (error) {
             console.error("Failed to save role:", error);
            alert(`Error al guardar rol: ${(error as Error).message}`);
        } finally {
            setIsLoading(false);
        }
    };

    const handleDeleteRole = async (roleId: string) => {
        if (window.confirm('¿Estás seguro de que quieres eliminar este rol? Esto podría afectar a los usuarios asignados a él.')) {
            try {
                await deleteRole(roleId);
                setRoles(roles.filter(r => r.id !== roleId));
            } catch (error) {
                console.error("Failed to delete role:", error);
                alert(`Error al eliminar rol: ${(error as Error).message}`);
            }
        }
    };

    return (
        <div>
            <div className="flex justify-end items-center mb-6">
                <Button onClick={() => openModal()} icon={ICONS.plus}>Añadir Rol</Button>
            </div>

            <Table headers={['Nombre del Rol', 'Resumen de Permisos', 'Acciones']}>
                {roles.map(role => (
                    <tr key={role.id} className="hover:bg-secondary-light">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-light">{role.name}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-medium">
                            {Object.keys(role.permissions).length} módulos configurados
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                            <Button variant="secondary" onClick={() => openModal(role)} icon={ICONS.pencil} />
                            <Button variant="danger" onClick={() => handleDeleteRole(role.id)} icon={ICONS.trash} />
                        </td>
                    </tr>
                ))}
            </Table>

            <Modal isOpen={isModalOpen} onClose={closeModal} title={editingRole ? 'Editar Rol' : 'Añadir Rol'}>
                <form onSubmit={handleSaveRole} className="space-y-6">
                    <Input id="name" name="name" label="Nombre del Rol" defaultValue={editingRole?.name} required />
                    
                    <div>
                        <h3 className="text-lg font-medium text-light mb-2">Permisos</h3>
                        <div className="space-y-4">
                            {Object.entries(permissionLabels).filter(([,moduleInfo]) => moduleInfo).map(([moduleKey, moduleInfo]) => (
                                <div key={moduleKey} className="p-4 bg-secondary-light rounded-md">
                                    <h4 className="font-semibold text-light mb-2">{moduleInfo!.label}</h4>
                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                                        {Object.entries(moduleInfo!.permissions).map(([actionKey, actionLabel]) => (
                                            <Checkbox
                                                key={`${moduleKey}-${actionKey}`}
                                                id={`${moduleKey}-${actionKey}`}
                                                label={actionLabel}
                                                checked={(currentPermissions[moduleKey as keyof Permissions] as any)?.[actionKey] || false}
                                                onChange={(e) => handlePermissionChange(moduleKey as keyof Permissions, actionKey, e.target.checked)}
                                            />
                                        ))}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="flex justify-end pt-4 space-x-2">
                        <Button type="button" variant="secondary" onClick={closeModal} disabled={isLoading}>Cancelar</Button>
                        <Button type="submit" disabled={isLoading}>{isLoading ? 'Guardando...' : 'Guardar Rol'}</Button>
                    </div>
                </form>
            </Modal>
        </div>
    );
};

export default Roles;