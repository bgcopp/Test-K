
import React from 'react';

interface PageWrapperProps {
    title: string;
    children: React.ReactNode;
    toolbar?: React.ReactNode;
}

const PageWrapper: React.FC<PageWrapperProps> = ({ title, toolbar, children }) => {
    return (
        <div className="container mx-auto px-4 py-6">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-3xl font-bold text-light">{title}</h1>
                {toolbar && <div>{toolbar}</div>}
            </div>
            <div className="bg-secondary rounded-lg shadow-xl p-6">
                {children}
            </div>
        </div>
    );
};

export default PageWrapper;
