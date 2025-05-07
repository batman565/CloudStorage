import { observer } from "mobx-react-lite";

const Filecard = observer(({ item, isFolder, onDoubleClick, onClick}) => {
  const getFileIcon = (fileName) => {
    const ext = fileName.split(".").pop().toLowerCase();
    const icons = {
      pdf: "fa-file-pdf",
      doc: "fa-file-word",
      docx: "fa-file-word",
      png: "fa-file-image",
      jpg: "fa-file-image",
      jpeg: "fa-file-image",
      default: "fa-file",
    };
    return icons[ext] || icons.default;
  };

  return (
    <div
      className={`file-card ${isFolder ? "folder" : "file"}`}
      onDoubleClick={isFolder ? onDoubleClick : null}
      
    >
      <i
        className={`fas ${
          isFolder ? "fa-folder" : getFileIcon(item.name)
        }`}
      />
      <span className="file-name" title={item.name}>
        {item.name}
      </span>
      {!isFolder && (
        <span className="file-size">
          {(item.weight / 1024).toFixed(1)} KB
        </span>
      )}
    </div>
  );
});

export default Filecard;