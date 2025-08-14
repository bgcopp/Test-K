import React, { useState } from 'react';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import { login } from '../services/api';

interface LoginProps {
    onLogin: () => void;
}

const Login: React.FC<LoginProps> = ({ onLogin }) => {
    const [email, setEmail] = useState('admin@example.com');
    const [password, setPassword] = useState('password');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);
        try {
            await login({ email, password });
            onLogin();
        } catch (err) {
            setError((err as Error).message || 'Error de autenticación.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex items-center justify-center min-h-screen bg-dark">
            <div className="w-full max-w-md p-8 space-y-8 bg-secondary rounded-xl shadow-lg">
                <h1 className="text-4xl font-bold text-center text-light">KRONOS</h1>
                <p className="text-center text-medium">¡Bienvenido de nuevo! Por favor, inicia sesión en tu cuenta.</p>
                <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
                    <Input 
                        id="email" 
                        label="Correo Electrónico" 
                        type="email" 
                        placeholder="usuario@ejemplo.com" 
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required 
                    />
                    <Input 
                        id="password" 
                        label="Contraseña" 
                        type="password" 
                        placeholder="••••••••" 
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required 
                    />
                    {error && <p className="text-sm text-red-500 text-center">{error}</p>}
                    <Button type="submit" variant="primary" className="w-full" disabled={isLoading}>
                        {isLoading ? 'Iniciando...' : 'Iniciar Sesión'}
                    </Button>
                </form>
            </div>
        </div>
    );
};

export default Login;