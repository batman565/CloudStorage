import { createContext, useContext } from "react";
import RootStore from ".";

export const StoreContext = createContext();

export const StoreProvider = ({ children }) => {
  const rootStore = new RootStore();
  
  return (
    <StoreContext.Provider value={rootStore}>
      {children}
    </StoreContext.Provider>
  );
};

export const useStore = () => useContext(StoreContext);