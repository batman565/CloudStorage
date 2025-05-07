import AuthStore from "./auth-store";
import FileStore from "./file-store";
import Profile from "./profile-store";

class RootStore {
  constructor() {
    this.authStore = new AuthStore();
    this.fileStore = new FileStore(this.authStore);
    this.userInfoStore = new Profile();
  }
}

export default RootStore;
