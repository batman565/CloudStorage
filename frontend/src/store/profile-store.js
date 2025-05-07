import axios from "axios";
import { makeAutoObservable } from "mobx";

class Profile {
  username = "";
  email = "";
  storage_used;
  storage_max;
  admin = false;

  constructor() {
    makeAutoObservable(this);
  }

  get_info = async (token) => {
    try {
      const response = await axios.get(`/api/user/`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      this.username = response.data.username;
      this.email = response.data.email;
      this.storage_used = response.data.storage_used;
      this.storage_max = response.data.storage_max;
      this.admin = response.data.admin;
    } catch (err) {
      return 0;
    }
  };
}

export default Profile;
