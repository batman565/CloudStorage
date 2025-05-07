import { useState } from "react";
import { useStore } from "../store/store-context";
import { useNavigate } from "react-router-dom";

const LoginForm = () => {
  const { authStore } = useStore();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      console.log(username);
      console.log(password);
      await authStore.login(username, password);
      navigate("/");
    } catch (error) {}
  };

  return (
    <div className="login-container">
      <form onSubmit={handleSubmit} className="login-form">
        <h2>Login</h2>

        <div className="form-group">
          <label>Username</label>
          <input
            type="text"
            value={username}
            onChange={(e) => {
              setUsername(e.target.value);
            }}
            required
          />
        </div>

        <div className="form-group">
          <label>Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>

        {authStore.error && (
          <div className="error-message">{authStore.error}</div>
        )}

        <button
          type="submit"
          disabled={authStore.isLoading}
          className="login-button"
        >
          {authStore.isLoading ? "Loading..." : "Login"}
        </button>
        <p className="TextLoginTo">
          Don't have an account?{" "}
          <a className="Textlinkto" href="/registration">
            Sign Up
          </a>
        </p>
      </form>
    </div>
  );
};

export default LoginForm;
