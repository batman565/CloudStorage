import { useEffect } from "react";
import { observer } from "mobx-react-lite";
import Filecard from "./file-cart";
import { useStore } from "../store/store-context";
import { useState } from "react";
import PopUp from "./popup";
import { useRef } from "react";

const Filelist = observer(() => {
  const { fileStore } = useStore();
  const popupTimer = useRef(null);

  const {
    filteredFiles,
    filteredFolders,
    currentFolder,
    isLoading,
    error,
    loadFiles,
  } = fileStore;
  const [popupVisible, setPopupVisible] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);
  const [isItemFolder, setIsItemFolder] = useState(false);

  const handleItemClick = (item, isFolder) => {
    if (popupTimer.current) {
      clearTimeout(popupTimer.current);
    }

    setSelectedItem(item);
    setIsItemFolder(isFolder);

    popupTimer.current = setTimeout(() => {
      setPopupVisible(true);
    }, 90);
  };

  const closePopup = () => {
    setPopupVisible(false);
    setSelectedItem(null);
    if (popupTimer.current) {
      clearTimeout(popupTimer.current);
    }
  };

  useEffect(() => {
    loadFiles(currentFolder?.id);
    closePopup();
  }, [currentFolder?.id, loadFiles]);

  useEffect(() => {
    return () => {
      if (popupTimer.current) {
        clearTimeout(popupTimer.current);
      }
    };
  }, []);

  if (error) return <div>Ошибка: {error}</div>;

  return (
    <div className="file-browser">
      <div className="breadcrumbs">
        {fileStore.folderParentId !== null && (
          <button
            onClick={() => fileStore.loadFiles(fileStore.folderParentId)}
            className="back-button"
          >
            ← Назад
          </button>
        )}
        <span className="current-folder">
          {fileStore.currentFolder?.name || "Мой Диск"}
        </span>
      </div>

      <div className="files-grid">
        {filteredFolders.map((folder) => (
          <div
            className="file-item"
            key={`folder-${folder.id}`}
            onClick={() => handleItemClick(folder, true)}
          >
            <Filecard
              item={folder}
              isFolder={true}
              onDoubleClick={() => loadFiles(folder.id)}
            />
          </div>
        ))}

        {filteredFiles.map((file) => (
          <div
            className="file-item"
            key={`file-${file.id}`}
            onClick={() => handleItemClick(file, false)}
          >
            <Filecard item={file} isFolder={false} />
          </div>
        ))}
      </div>
      {popupVisible && (
        <PopUp
          item={selectedItem}
          isFolder={isItemFolder}
          onClose={closePopup}
        />
      )}
    </div>
  );
});

export default Filelist;
