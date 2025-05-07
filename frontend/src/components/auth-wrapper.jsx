// components/auth-wrapper.jsx
import { useContext } from 'react';
import { Navigate } from 'react-router-dom';
import { StoreContext } from '../store/store-context';
import { observer } from 'mobx-react-lite';

const AuthWrapper = observer(({ children }) => {
  const { authStore } = useContext(StoreContext);

  if (!authStore.isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
});

export default AuthWrapper;