import React, { useState, useEffect } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = React.createContext();

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      // Verify token and get user info
      axios.get(`${API}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      }).then(response => {
        setUser(response.data);
      }).catch(() => {
        localStorage.removeItem('token');
        setToken(null);
      }).finally(() => {
        setLoading(false);
      });
    } else {
      setLoading(false);
    }
  }, [token]);

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, { email, password });
      const { access_token, user: userData } = response.data;
      
      localStorage.setItem('token', access_token);
      setToken(access_token);
      setUser(userData);
      
      return { success: true };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Login failed' };
    }
  };

  const register = async (userData) => {
    try {
      const response = await axios.post(`${API}/auth/register`, userData);
      const { access_token, user: newUser } = response.data;
      
      localStorage.setItem('token', access_token);
      setToken(access_token);
      setUser(newUser);
      
      return { success: true };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Registration failed' };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };

  if (loading) {
    return <div className="loading-screen">Loading...</div>;
  }

  return (
    <AuthContext.Provider value={{ user, login, register, logout, token }}>
      {children}
    </AuthContext.Provider>
  );
};

const useAuth = () => {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

// Components
const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const result = await login(email, password);
    if (!result.success) {
      setError(result.error);
    }
    setLoading(false);
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="brand-section">
          <h1 className="brand-title">Luggixx</h1>
          <p className="brand-subtitle">Your trusted porter service</p>
        </div>
        
        <form onSubmit={handleSubmit} className="auth-form">
          <h2 className="form-title">Welcome Back</h2>
          
          {error && <div className="error-message">{error}</div>}
          
          <div className="form-group">
            <label>Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="form-input"
              placeholder="Enter your email"
            />
          </div>
          
          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="form-input"
              placeholder="Enter your password"
            />
          </div>
          
          <button type="submit" disabled={loading} className="submit-btn">
            {loading ? 'Logging in...' : 'Login'}
          </button>
          
          <p className="auth-link">
            Don't have an account? <a href="/register">Sign up</a>
          </p>
        </form>
      </div>
    </div>
  );
};

const Register = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    password: '',
    role: 'customer'
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const result = await register(formData);
    if (!result.success) {
      setError(result.error);
    }
    setLoading(false);
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="brand-section">
          <h1 className="brand-title">Luggixx</h1>
          <p className="brand-subtitle">Join our community</p>
        </div>
        
        <form onSubmit={handleSubmit} className="auth-form">
          <h2 className="form-title">Create Account</h2>
          
          {error && <div className="error-message">{error}</div>}
          
          <div className="form-group">
            <label>Full Name</label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleChange}
              required
              className="form-input"
              placeholder="Enter your full name"
            />
          </div>
          
          <div className="form-group">
            <label>Email</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              className="form-input"
              placeholder="Enter your email"
            />
          </div>
          
          <div className="form-group">
            <label>Phone</label>
            <input
              type="tel"
              name="phone"
              value={formData.phone}
              onChange={handleChange}
              required
              className="form-input"
              placeholder="Enter your phone number"
            />
          </div>
          
          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              className="form-input"
              placeholder="Create a password"
            />
          </div>
          
          <div className="form-group">
            <label>I am a:</label>
            <div className="role-selection">
              <label className="radio-label">
                <input
                  type="radio"
                  name="role"
                  value="customer"
                  checked={formData.role === 'customer'}
                  onChange={handleChange}
                />
                <span className="radio-text">Customer (Need porter service)</span>
              </label>
              <label className="radio-label">
                <input
                  type="radio"
                  name="role"
                  value="porter"
                  checked={formData.role === 'porter'}
                  onChange={handleChange}
                />
                <span className="radio-text">Porter (Provide service)</span>
              </label>
            </div>
          </div>
          
          <button type="submit" disabled={loading} className="submit-btn">
            {loading ? 'Creating Account...' : 'Sign Up'}
          </button>
          
          <p className="auth-link">
            Already have an account? <a href="/login">Login</a>
          </p>
        </form>
      </div>
    </div>
  );
};

const MapView = () => {
  const { user, logout } = useAuth();
  const [rides, setRides] = useState([]);
  const [showRequestForm, setShowRequestForm] = useState(false);
  const [requestForm, setRequestForm] = useState({
    pickup_location: '',
    destination: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchRides();
  }, []);

  const fetchRides = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/rides/my-rides`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setRides(response.data);
    } catch (error) {
      console.error('Error fetching rides:', error);
    }
  };

  const handleRequestRide = async (e) => {
    e.preventDefault();
    if (!requestForm.pickup_location || !requestForm.destination) {
      setError('Please fill in all fields');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/rides/request`, requestForm, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setRides([response.data, ...rides]);
      setShowRequestForm(false);
      setRequestForm({ pickup_location: '', destination: '' });
    } catch (error) {
      setError(error.response?.data?.detail || 'Failed to request ride');
    }
    
    setLoading(false);
  };

  const updateRideStatus = async (rideId, status) => {
    try {
      const token = localStorage.getItem('token');
      await axios.put(`${API}/rides/${rideId}/status?status=${status}`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchRides();
    } catch (error) {
      console.error('Error updating ride status:', error);
    }
  };

  return (
    <div className="map-container">
      <header className="app-header">
        <div className="header-content">
          <h1 className="app-title">Luggixx</h1>
          <div className="user-info">
            <span className="welcome-text">Hello, {user.name}</span>
            <span className="user-role">{user.role}</span>
            <button onClick={logout} className="logout-btn">Logout</button>
          </div>
        </div>
      </header>

      <main className="main-content">
        {/* Map Placeholder */}
        <div className="map-placeholder">
          <div className="map-overlay">
            <h3>Interactive Map Coming Soon</h3>
            <p>Your rides and available porters will appear here</p>
          </div>
        </div>

        {/* Customer Controls */}
        {user.role === 'customer' && (
          <div className="customer-controls">
            {!showRequestForm ? (
              <button 
                onClick={() => setShowRequestForm(true)}
                className="request-ride-btn"
              >
                Request a Porter
              </button>
            ) : (
              <div className="request-form">
                <h3>Request Porter Service</h3>
                {error && <div className="error-message">{error}</div>}
                <form onSubmit={handleRequestRide}>
                  <div className="form-group">
                    <label>Pickup Location</label>
                    <input
                      type="text"
                      value={requestForm.pickup_location}
                      onChange={(e) => setRequestForm({...requestForm, pickup_location: e.target.value})}
                      placeholder="Where should the porter meet you?"
                      className="form-input"
                    />
                  </div>
                  <div className="form-group">
                    <label>Destination</label>
                    <input
                      type="text"
                      value={requestForm.destination}
                      onChange={(e) => setRequestForm({...requestForm, destination: e.target.value})}
                      placeholder="Where do you need to go?"
                      className="form-input"
                    />
                  </div>
                  <div className="form-actions">
                    <button type="submit" disabled={loading} className="submit-btn">
                      {loading ? 'Requesting...' : 'Request Porter'}
                    </button>
                    <button 
                      type="button" 
                      onClick={() => setShowRequestForm(false)}
                      className="cancel-btn"
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              </div>
            )}
          </div>
        )}

        {/* Rides List */}
        <div className="rides-section">
          <h3>{user.role === 'customer' ? 'My Ride Requests' : 'My Assigned Rides'}</h3>
          {rides.length === 0 ? (
            <div className="no-rides">
              <p>No rides yet</p>
            </div>
          ) : (
            <div className="rides-list">
              {rides.map(ride => (
                <div key={ride.id} className="ride-card">
                  <div className="ride-info">
                    <div className="ride-locations">
                      <div className="location">
                        <span className="location-label">From:</span>
                        <span className="location-text">{ride.pickup_location}</span>
                      </div>
                      <div className="location">
                        <span className="location-label">To:</span>
                        <span className="location-text">{ride.destination}</span>
                      </div>
                    </div>
                    
                    {user.role === 'customer' && ride.porter_name && (
                      <div className="porter-info">
                        <span className="porter-label">Porter:</span>
                        <span className="porter-name">{ride.porter_name}</span>
                        <span className="porter-phone">{ride.porter_phone}</span>
                      </div>
                    )}
                    
                    <div className="ride-meta">
                      <span className={`status status-${ride.status}`}>{ride.status.toUpperCase()}</span>
                      <span className="ride-time">
                        {new Date(ride.created_at).toLocaleDateString()} at {new Date(ride.created_at).toLocaleTimeString()}
                      </span>
                    </div>
                  </div>
                  
                  {user.role === 'porter' && ride.status === 'assigned' && (
                    <div className="ride-actions">
                      <button 
                        onClick={() => updateRideStatus(ride.id, 'in_progress')}
                        className="action-btn start-btn"
                      >
                        Start Journey
                      </button>
                    </div>
                  )}
                  
                  {user.role === 'porter' && ride.status === 'in_progress' && (
                    <div className="ride-actions">
                      <button 
                        onClick={() => updateRideStatus(ride.id, 'completed')}
                        className="action-btn complete-btn"
                      >
                        Complete Ride
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

const ProtectedRoute = ({ children }) => {
  const { user } = useAuth();
  return user ? children : <Navigate to="/login" />;
};

function App() {
  return (
    <div className="App">
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/" element={
              <ProtectedRoute>
                <MapView />
              </ProtectedRoute>
            } />
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </div>
  );
}

export default App;