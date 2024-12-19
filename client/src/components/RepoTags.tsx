import React, { useEffect } from 'react';

export const RepoTags: React.FC<{ isActive: boolean }> = ({ isActive }) => {
    useEffect(() => {
        if (isActive) {
            // Load tags if they haven't been loaded yet.
        }
    }, [isActive]);

    return (
        <div className="tab-pane fade show active" id="tags">
            <p>Tags...</p>
        </div>
    );
};