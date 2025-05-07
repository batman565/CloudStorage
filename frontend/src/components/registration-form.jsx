import { useState } from "react";
import { useStore } from "../store/store-context";
import { useNavigate, Link } from "react-router-dom";
import axios from "axios";

const RegistrationForm = () => {
  const { authStore } = useStore();
  const navigate = useNavigate();
  
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [validationErrors, setValidationErrors] = useState({});

  const validateForm = () => {
    const errors = {};
    const usernameRegex = /^[a-zA-Z0-9_]{3,30}$/;
    const passwordRegex = /^(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*]).{8,}$/;
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!usernameRegex.test(username)) {
      errors.username = "Username must be 3-30 chars (letters, numbers, _)";
    }
    
    if (!emailRegex.test(email)) {
      errors.email = "Invalid email format";
    }
    
    if (!passwordRegex.test(password)) {
      errors.password = "Password must contain: 8+ chars, 1 uppercase, 1 number, 1 special symbol";
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;

    try {
      const response = await axios.post("/api/user/create/", {
        username,
        email,
        password
      });

      authStore.setAuthData(
        response.data.access_token,
        response.data.expire
      );
      
      navigate("/");
    } catch (error) {
      if (error.response?.data?.detail === "Username or email already registered") {
        setValidationErrors({
          server: "Username or email already exists"
        });
      } else {
        setValidationErrors({
          server: error.response?.data?.detail || "Registration failed"
        });
      }
    }
  };

  return (
    <div className="login-container">
      <form onSubmit={handleSubmit} className="login-form">
        <h2>Registration</h2>

        <div className="form-group">
          <label>Username</label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            className={validationErrors.username ? "error" : ""}
          />
          {validationErrors.username && (
            <div className="error-message">{validationErrors.username}</div>
          )}
        </div>

        <div className="form-group">
          <label>Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className={validationErrors.email ? "error" : ""}
          />
          {validationErrors.email && (
            <div className="error-message">{validationErrors.email}</div>
          )}
        </div>

        <div className="form-group">
          <label>Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className={validationErrors.password ? "error" : ""}
          />
          {validationErrors.password && (
            <div className="error-message"><br/>{validationErrors.password}</div>
          )}
        </div>

        {validationErrors.server && (
          <div className="error-message">{validationErrors.server}</div>
        )}

        <button
          type="submit"
          className="login-button"
        >
          Register
        </button>

        <div className="auth-link">
          Already have an account? <Link to="/login">Login here</Link>
        </div>
      </form>
    </div>
  );
};

export default RegistrationForm;