import axios from 'axios';
import { makeAutoObservable } from 'mobx';

class DownloadStore {
  upload = async (file, currentFolder, token) => {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(
        `/api/file/upload/${currentFolder}`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
            Authorization: `Bearer ${token}`,
          },
        }
      );
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  constructor() {
    makeAutoObservable(this);
  }
}

export default new DownloadStore();

