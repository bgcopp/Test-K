
import React from 'react';

interface CheckboxProps extends React.InputHTMLAttributes<HTMLInputElement> {
    label: string;
    id: string;
}

const Checkbox: React.FC<CheckboxProps> = ({ label, id, ...props }) => {
    return (
        <label htmlFor={id} className="flex items-center space-x-2 cursor-pointer">
            <input
                id={id}
                type="checkbox"
                className="h-4 w-4 rounded bg-secondary-light border-gray-500 text-primary focus:ring-primary"
                {...props}
            />
            <span className="text-sm text-light">{label}</span>
        </label>
    );
};

export default Checkbox;
