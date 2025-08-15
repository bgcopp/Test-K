import React, { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import type { Mission } from '../types';
import { MissionStatus } from '../types';
import Table from '../components/ui/Table';
import Button from '../components/ui/Button';
import Modal from '../components/ui/Modal';
import Input from '../components/ui/Input';
import { ICONS } from '../constants';
import { createMission, updateMission, deleteMission } from '../services/api';
import { useConfirmation, confirmationPresets } from '../hooks/useConfirmation';

const statusColors: { [key in MissionStatus]: string } = {
    [MissionStatus.PLANNING]: 'bg-yellow-200 text-yellow-800',
    [MissionStatus.IN_PROGRESS]: 'bg-blue-200 text-blue-800',
    [MissionStatus.COMPLETED]: 'bg-green-200 text-green-800',
    [MissionStatus.CANCELLED]: 'bg-red-200 text-red-800',
};

interface MissionsProps {
    missions: Mission[];
    setMissions: React.Dispatch<React.SetStateAction<Mission[]>>;
}

const Missions: React.FC<MissionsProps> = ({ missions, setMissions }) => {
    const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
    const [editingMission, setEditingMission] = useState<Mission | null>(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const { showConfirmation } = useConfirmation();

    const openModal = (mission: Mission | null = null) => {
        setEditingMission(mission);
        setIsModalOpen(true);
    };

    const closeModal = () => {
        setIsModalOpen(false);
        setEditingMission(null);
    };

    const handleSaveMission = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setIsLoading(true);
        const formData = new FormData(e.currentTarget);
        const missionData = {
            code: formData.get('code') as string,
            name: formData.get('name') as string,
            description: formData.get('description') as string,
            status: formData.get('status') as MissionStatus,
            startDate: formData.get('startDate') as string,
            endDate: formData.get('endDate') as string,
        };

        try {
            if (editingMission) {
                const updated = await updateMission(editingMission.id, missionData);
                setMissions(missions.map(m => m.id === editingMission.id ? updated : m));
            } else {
                const newMission = await createMission(missionData);
                setMissions([...missions, newMission]);
            }
            closeModal();
        } catch (error) {
            console.error("Failed to save mission:", error);
            alert(`Error al guardar misión: ${(error as Error).message}`);
        } finally {
            setIsLoading(false);
        }
    };

    const handleDeleteMission = async (missionId: string) => {
        const mission = missions.find(m => m.id === missionId);
        if (!mission) return;

        const confirmed = await showConfirmation(
            confirmationPresets.deleteMission(mission.name)
        );
        
        if (confirmed) {
            try {
                await deleteMission(missionId);
                setMissions(missions.filter(m => m.id !== missionId));
            } catch (error) {
                console.error("Failed to delete mission:", error);
                // El error se mostrará a través del sistema de notificaciones
            }
        }
    };
    
    const filteredMissions = useMemo(() => {
        return missions.filter(mission =>
            mission.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            mission.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
            mission.code.toLowerCase().includes(searchTerm.toLowerCase())
        );
    }, [missions, searchTerm]);

    return (
        <div>
            <div className="flex justify-between items-center mb-6">
                <div className="relative">
                    <span className="absolute inset-y-0 left-0 flex items-center pl-3">
                        {ICONS.search}
                    </span>
                    <Input id="search-missions" type="text" placeholder="Buscar misiones..." className="!pl-10" onChange={e => setSearchTerm(e.target.value)} />
                </div>
                <Button onClick={() => openModal()} icon={ICONS.plus}>Añadir Misión</Button>
            </div>

            <Table headers={['Código', 'Nombre Misión', 'Estado', 'Fechas', 'Acciones']}>
                {filteredMissions.map(mission => (
                    <tr key={mission.id} className="hover:bg-secondary-light">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-medium">{mission.code}</td>
                        <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm font-medium text-light">{mission.name}</div>
                            <div className="text-sm text-medium truncate max-w-xs">{mission.description}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                            <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${statusColors[mission.status]}`}>
                                {mission.status}
                            </span>
                        </td>
                         <td className="px-6 py-4 whitespace-nowrap text-sm text-medium">
                            {mission.startDate} a {mission.endDate}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                             <Link to={`/missions/${mission.id}`}>
                                <Button variant="secondary" icon={ICONS.eye} title="Ver Detalles"/>
                             </Link>
                             <Button variant="secondary" onClick={() => openModal(mission)} icon={ICONS.pencil} title="Editar Misión"/>
                             <Button variant="danger" onClick={() => handleDeleteMission(mission.id)} icon={ICONS.trash} title="Eliminar Misión"/>
                        </td>
                    </tr>
                ))}
            </Table>

            <Modal isOpen={isModalOpen} onClose={closeModal} title={editingMission ? 'Editar Misión' : 'Añadir Misión'}>
                <form onSubmit={handleSaveMission} className="space-y-4">
                    <Input id="code" name="code" label="Código de Misión" defaultValue={editingMission?.code} placeholder="ej. PX-001" required />
                    <Input id="name" name="name" label="Nombre de Misión" defaultValue={editingMission?.name} required />
                    <div>
                        <label htmlFor="description" className="block text-sm font-medium text-medium mb-1">Descripción</label>
                        <textarea
                            id="description"
                            name="description"
                            rows={3}
                            defaultValue={editingMission?.description}
                            className="w-full px-3 py-2 bg-secondary-light border border-gray-600 rounded-md text-light placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary"
                        ></textarea>
                    </div>
                    <div>
                        <label htmlFor="status" className="block text-sm font-medium text-medium mb-1">Estado</label>
                        <select id="status" name="status" defaultValue={editingMission?.status} className="w-full px-3 py-2 bg-secondary-light border border-gray-600 rounded-md text-light focus:outline-none focus:ring-2 focus:ring-primary">
                            {Object.values(MissionStatus).map(status => (
                                <option key={status} value={status}>{status}</option>
                            ))}
                        </select>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <Input id="startDate" name="startDate" label="Fecha de Inicio" type="date" defaultValue={editingMission?.startDate} required />
                        <Input id="endDate" name="endDate" label="Fecha de Fin" type="date" defaultValue={editingMission?.endDate} required />
                    </div>
                    <div className="flex justify-end pt-4 space-x-2">
                        <Button type="button" variant="secondary" onClick={closeModal} disabled={isLoading}>Cancelar</Button>
                        <Button type="submit" disabled={isLoading}>{isLoading ? 'Guardando...' : 'Guardar Misión'}</Button>
                    </div>
                </form>
            </Modal>
        </div>
    );
};

export default Missions;