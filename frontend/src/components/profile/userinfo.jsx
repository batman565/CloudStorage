import { useEffect } from "react";
import { useStore } from "../../store/store-context";
import { observer } from "mobx-react-lite";

const Userinfo = () => {
  const { authStore } = useStore();
  const { userInfoStore } = useStore();

  useEffect(() => {
    const fetchinfo = async () => {
      await userInfoStore.get_info(authStore.token);
    };
    fetchinfo();
  }, [authStore.token]);

  return (
    <div>
      <h2>{userInfoStore.username}</h2>
    </div>
  );
};

export default observer(Userinfo);
