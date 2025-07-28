import React, { useEffect, useState } from 'react';
import { AxiosError, AxiosResponse } from 'axios';
import { LogLevel, LogQueryDTO, LogsService } from '../api/logs.api';
import Spinner from 'react-bootstrap/Spinner';
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';
import { Row, Col, Table } from 'react-bootstrap';
import { Pagination } from 'react-bootstrap';
import "./AnalyticsSidebar.css";
import ReactMarkdown from 'react-markdown';

interface SidebarProps {
    onClose: () => void;
}

const markdownContent = `
# **Help**

# Keywords

## (1) \`text_content\`
The text of the log.

- \`text_content ~= "not don't couldn't no"\`
\\
Search by keywords (if any word is found, it's a match)

- \`text_content ~~= "tried to get"\`
\\
Search by term (the whole term must match)

## (2) \`log_level\`

Supports: \`info\`, \`warning\`, \`error\`, \`trace\` and \`debug\`.

- \`log_level == "info"\`
\\
Search all logs with the \`info\` badge.

- \`log_level == "info" or log_level == "error"\`
\\
Search all logs with the \`info\` _or_ \`error\` badge.

## (3) \`date_time\`

Dates can be compared using \`>\`, \`>=\`, \`<\`, \`<=\` and \`==\`.

- \`date_time <= "2025-07-27T08:06:10"\`
\\
Get logs submitted before the 27th of July 2025 at 08:06:10.

- \`date_time >= "2025-07-01" and date_time < "2025-07-27"\`
\\
Get logs submitted before 1st of July 2025 and 27th of July 2025.

# Complex queries

- \`(log_level == "warning" or log_level == "debug") and text_content ~= "http failure"\`
- \`(log_level == "info" or log_level == "debug") and (text_content ~~= "HTTP connection" or date_time >= "2025-07-25")\`
- \`log_level == "error" and not text_content ~= "HTTP"\`
`;

export const AnalyticsSidebar: React.FC<SidebarProps> = ({ onClose }) => {
    return (
        <div className="sidebar">
            <button className="close-btn" onClick={onClose}>×</button>
            <ReactMarkdown>{markdownContent}</ReactMarkdown>
        </div>
    );
};

