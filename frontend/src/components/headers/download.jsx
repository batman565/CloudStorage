import React, { useRef } from 'react';
import { observer } from 'mobx-react-lite';
import { useStore } from "../../store/store-context";
import downloadStore from '../../store/download-store';


const Download = observer(() => {
    const { fileStore, authStore } = useStore();
    const fileInputRef = useRef(null);
  
    const handleFileSelect = async (e) => {
      const file = e.target.files?.[0];
      if (!file) return;
  
      try {
        await downloadStore.upload(
          file,
          fileStore.currentFolder?.id,
          authStore.token
        );
        await fileStore.loadFiles(fileStore.currentFolder?.id);
      } catch (error) {
        console.error('Ошибка загрузки:', error);
        alert(error.response?.data?.detail || 'Ошибка загрузки файла');
      }
    };
  
    return (
      <div>
        <input
          type="file"
          ref={fileInputRef}
          style={{ display: 'none' }}
          onChange={handleFileSelect}
        />
        <button 
          className="upload-btn" 
          onClick={() => fileInputRef.current?.click()}
        >
          Загрузить
        </button>
      </div>
    );
  });
  
  export default Download;