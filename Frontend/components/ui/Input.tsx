
import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
    label?: string;
    id: string;
}

const Input: React.FC<InputProps> = ({ label, id, ...props }) => {
    return (
        <div>
            {label && <label htmlFor={id} className="block text-sm font-medium text-medium mb-1">{label}</label>}
            <input
                id={id}
                className="w-full px-3 py-2 bg-secondary-light border border-gray-600 rounded-md text-light placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                {...props}
            />
        </div>
    );
};

export default Input;
