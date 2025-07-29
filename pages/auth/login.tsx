import React, { useState } from 'react';
import axios from 'axios';

const LoginPage = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');

    const handleSubmit = async (event: React.FormEvent) => {
        event.preventDefault();
        try {
            const response = await axios.post('http://localhost:8000/api/v1/auth/login', {
                email,
                password,
            });
            console.log('Login successful:', response.data);
            // Handle successful login (e.g., redirect, store token, etc.)
        } catch (error: any) {
            if (error.code === 'ERR_NETWORK') {
                console.error('Network error: Unable to reach the server. Please check your connection or backend server.');
                alert('Login failed: Unable to reach the server.');
            } else if (error.response?.status === 404) {
                console.error('Login endpoint not found. Please check the API URL.');
                alert('Login failed: Endpoint not found.');
            } else {
                console.error('An error occurred:', error.message);
                alert('Login failed: ' + error.message);
            }
        }
    };

    return (
        <div>
            <h1>Login</h1>
            <form onSubmit={handleSubmit}>
                <div>
                    <label>Email:</label>
                    <input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                    />
                </div>
                <div>
                    <label>Password:</label>
                    <input
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                    />
                </div>
                <button type="submit">Login</button>
            </form>
        </div>
    );
};

export default LoginPage;