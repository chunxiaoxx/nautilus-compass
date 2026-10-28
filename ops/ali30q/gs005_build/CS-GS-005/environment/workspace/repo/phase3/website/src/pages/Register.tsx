import { Navigate } from 'react-router-dom'

/** Register redirects to unified Login (Web3Auth handles both) */
const Register = () => <Navigate to="/login" replace />

export default Register
