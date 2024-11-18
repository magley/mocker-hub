import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import axios from 'axios';
import { Button } from 'react-bootstrap';
import Table from 'react-bootstrap/Table';

function App() {
    const [count, setCount] = useState(0);
    const [data, setData] = useState([]);

    const testRequest = () => {
        // Send request directly:
        //axios.get("http://127.0.0.1:8000/api/v1/users/test").then((res) => {

        // Send request through nginx:
        axios.get("http://127.0.0.1/api/users/test").then((res) => {
            console.log(res);
            setData(res.data);
        }).catch(err => {
            console.error(err);
        })
    }

    return (
        <>
            <div>
                <a href="https://vite.dev" target="_blank">
                    <img src={viteLogo} className="logo" alt="Vite logo" />
                </a>
                <a href="https://react.dev" target="_blank">
                    <img src={reactLogo} className="logo react" alt="React logo" />
                </a>
            </div>
            <h1>Vite + React</h1>
            <Button onClick={testRequest}>Click me and check the console</Button>
            <Table striped bordered hover>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Name</th>
                    </tr>
                </thead>
                <tbody>
                    {
                        data.map((obj: any, _) =>
                            <tr key={obj.id}>
                                <th>{obj.id}</th>
                                <th>{obj.name}</th>
                            </tr>
                        )
                    }
                </tbody>
            </Table>
            <div className="card">
                <button onClick={() => setCount((count) => count + 1)}>
                    count is {count}
                </button>
                <p>
                    Edit <code>src/App.tsx</code> and save to test HMR
                </p>
            </div>
            <p className="read-the-docs">
                Click on the Vite and React logos to learn more
            </p>
        </>
    )
}

export default App
