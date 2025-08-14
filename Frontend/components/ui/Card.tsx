
import React from 'react';

interface CardProps {
    title: string;
    value: string | number;
    icon: React.ReactNode;
}

const Card: React.FC<CardProps> = ({ title, value, icon }) => {
    return (
        <div className="bg-secondary p-6 rounded-lg shadow-lg flex items-center space-x-4 border border-secondary-light">
            <div className="p-3 bg-secondary-light rounded-full text-primary">
                {icon}
            </div>
            <div>
                <p className="text-sm font-medium text-medium">{title}</p>
                <p className="text-2xl font-bold text-light">{value}</p>
            </div>
        </div>
    );
};

export default Card;
