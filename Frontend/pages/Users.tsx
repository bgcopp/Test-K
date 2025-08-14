import React, { useState, useMemo, useCallback } from 'react';
import type { User, Role } from '../types';
import Table from '../components/ui/Table';
import Button from '../components/ui/Button';
import Modal from '../components/ui/Modal';
import Input from '../components/ui/Input';
import { ICONS } from '../constants';
import { createUser, updateUser, deleteUser } from '../services/api';

interface UsersProps {
    users: User[];
    setUsers: React.Dispatch<React.SetStateAction<User[]>>;
    roles: Role[];
}

const Users: React.FC<UsersProps> = ({ users, setUsers, roles }) => {
    const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
    const [editingUser, setEditingUser] = useState<User | null>(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const openModal = (user: User | null = null) => {
        setEditingUser(user);
        setIsModalOpen(true);
    };

    const closeModal = () => {
        setIsModalOpen(false);
        setEditingUser(null);
    };

    const handleSaveUser = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setIsLoading(true);
        const formData = new FormData(e.currentTarget);
        const userData = {
            name: formData.get('name') as string,
            email: formData.get('email') as string,
            roleId: formData.get('roleId') as string,
            status: formData.get('status') as 'active' | 'inactive',
        };

        try {
            if (editingUser) {
                const updatedUser = await updateUser(editingUser.id, userData);
                setUsers(users.map(u => u.id === editingUser.id ? updatedUser : u));
            } else {
                const newUser = await createUser(userData);
                setUsers([...users, newUser]);
            }
            closeModal();
        } catch (error) {
            console.error("Failed to save user:", error);
            alert(`Error al guardar usuario: ${(error as Error).message}`);
        } finally {
            setIsLoading(false);
        }
    };
    
    const handleDeleteUser = async (userId: string) => {
        if (window.confirm('¿Estás seguro de que quieres eliminar este usuario?')) {
            try {
                await deleteUser(userId);
                setUsers(users.filter(u => u.id !== userId));
            } catch (error) {
                console.error("Failed to delete user:", error);
                alert(`Error al eliminar usuario: ${(error as Error).message}`);
            }
        }
    };

    const filteredUsers = useMemo(() => {
        return users.filter(user =>
            user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            user.email.toLowerCase().includes(searchTerm.toLowerCase())
        );
    }, [users, searchTerm]);

    const getRoleName = useCallback((roleId: string) => {
        return roles.find(r => r.id === roleId)?.name || 'Rol Desconocido';
    }, [roles]);

    return (
        <div>
            <div className="flex justify-between items-center mb-6">
                <div className="relative">
                    <span className="absolute inset-y-0 left-0 flex items-center pl-3">
                        {ICONS.search}
                    </span>
                    <Input id="search" type="text" placeholder="Buscar usuarios..." className="!pl-10" onChange={e => setSearchTerm(e.target.value)} />
                </div>
                <Button onClick={() => openModal()} icon={ICONS.plus}>Añadir Usuario</Button>
            </div>

            <Table headers={['Usuario', 'Correo', 'Rol', 'Estado', 'Acciones']}>
                {filteredUsers.map(user => (
                    <tr key={user.id} className="hover:bg-secondary-light">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-light">
                            <div className="flex items-center">
                                <img className="h-10 w-10 rounded-full" src={user.avatar} alt={user.name} />
                                <div className="ml-4">{user.name}</div>
                            </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-medium">{user.email}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-medium">{getRoleName(user.roleId)}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                            <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${user.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                                {user.status === 'active' ? 'Activo' : 'Inactivo'}
                            </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                            <Button variant="secondary" onClick={() => openModal(user)} icon={ICONS.pencil} />
                            <Button variant="danger" onClick={() => handleDeleteUser(user.id)} icon={ICONS.trash} />
                        </td>
                    </tr>
                ))}
            </Table>
            
            <Modal isOpen={isModalOpen} onClose={closeModal} title={editingUser ? 'Editar Usuario' : 'Añadir Usuario'}>
                <form onSubmit={handleSaveUser} className="space-y-4">
                    <Input id="name" name="name" label="Nombre Completo" defaultValue={editingUser?.name} required/>
                    <Input id="email" name="email" label="Correo Electrónico" type="email" defaultValue={editingUser?.email} required/>
                    <div>
                        <label htmlFor="roleId" className="block text-sm font-medium text-medium mb-1">Rol</label>
                        <select id="roleId" name="roleId" defaultValue={editingUser?.roleId} className="w-full px-3 py-2 bg-secondary-light border border-gray-600 rounded-md text-light focus:outline-none focus:ring-2 focus:ring-primary">
                            {roles.map(role => (
                                <option key={role.id} value={role.id}>{role.name}</option>
                            ))}
                        </select>
                    </div>
                     <div>
                        <label htmlFor="status" className="block text-sm font-medium text-medium mb-1">Estado</label>
                        <select id="status" name="status" defaultValue={editingUser?.status} className="w-full px-3 py-2 bg-secondary-light border border-gray-600 rounded-md text-light focus:outline-none focus:ring-2 focus:ring-primary">
                            <option value="active">Activo</option>
                            <option value="inactive">Inactivo</option>
                        </select>
                    </div>
                    <div className="flex justify-end pt-4 space-x-2">
                        <Button type="button" variant="secondary" onClick={closeModal} disabled={isLoading}>Cancelar</Button>
                        <Button type="submit" disabled={isLoading}>{isLoading ? 'Guardando...' : 'Guardar'}</Button>
                    </div>
                </form>
            </Modal>
        </div>
    );
};

export default Users;