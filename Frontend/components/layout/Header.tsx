
import React from 'react';

interface HeaderProps {
    title: string;
}

const Header: React.FC<HeaderProps> = ({ title }) => {
    return (
        <header className="bg-secondary shadow-md p-4 border-b border-secondary-light">
            <h1 className="text-2xl font-semibold text-light">{title}</h1>
        </header>
    );
};

export default Header;
