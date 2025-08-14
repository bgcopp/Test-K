
import React from 'react';

interface TableProps {
    headers: string[];
    children: React.ReactNode;
    toolbar?: React.ReactNode;
}

const Table: React.FC<TableProps> = ({ headers, children, toolbar }) => {
    return (
        <div className="rounded-lg border border-secondary-light overflow-hidden">
            {toolbar && (
                 <div className="bg-secondary p-2 border-b border-secondary-light flex items-center space-x-2">
                     {toolbar}
                 </div>
            )}
            <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-secondary-light">
                    <thead className="bg-secondary-light">
                        <tr>
                            {headers.map((header) => (
                                <th key={header} scope="col" className="px-6 py-3 text-left text-xs font-medium text-medium uppercase tracking-wider">
                                    {header}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody className="bg-secondary divide-y divide-secondary-light">
                        {children}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default Table;
