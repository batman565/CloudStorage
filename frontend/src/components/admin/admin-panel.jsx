import { observer } from "mobx-react-lite";
import { useEffect, useState } from "react";
import axios from "axios";
import { useStore } from "../../store/store-context";

function formatBytes(bytes) {
  if (!bytes) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let i = 0;
  let n = bytes;
  while (n >= 1024 && i < units.length - 1) {
    n /= 1024;
    i += 1;
  }
  return `${n.toFixed(n >= 10 || i === 0 ? 0 : 1)} ${units[i]}`;
}

const AdminPanel = observer(() => {
  const { authStore } = useStore();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [viewing, setViewing] = useState(null); // {user, folder, parent, subfolders, files}

  const authHeader = { Authorization: `Bearer ${authStore.token}` };

  const loadUsers = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get("/api/admin/users/", { headers: authHeader });
      setUsers(response.data);
    } catch (e) {
      setError(e.response?.data?.detail || "Не удалось загрузить пользователей");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUsers();
  }, []);

  const toggleAdmin = async (user) => {
    try {
      await axios.patch(
        `/api/admin/users/${user.id}/`,
        { is_admin: !user.is_admin },
        { headers: authHeader }
      );
      loadUsers();
    } catch (e) {
      alert(e.response?.data?.detail || "Ошибка изменения прав");
    }
  };

  const deleteUser = async (user) => {
    if (!confirm(`Удалить пользователя ${user.username}?`)) return;
    try {
      await axios.delete(`/api/admin/users/${user.id}/`, { headers: authHeader });
      loadUsers();
    } catch (e) {
      alert(e.response?.data?.detail || "Не удалось удалить пользователя");
    }
  };

  const openStorage = async (user, folderId = null) => {
    try {
      const url = folderId
        ? `/api/admin/users/${user.id}/storage/?folder_id=${folderId}`
        : `/api/admin/users/${user.id}/storage/`;
      const response = await axios.get(url, { headers: authHeader });
      setViewing({
        user,
        folder: response.data.current_folder,
        parent: response.data.folder_parent_id,
        subfolders: response.data.subfolders,
        files: response.data.files,
      });
    } catch (e) {
      alert(e.response?.data?.detail || "Не удалось открыть хранилище");
    }
  };

  if (viewing) {
    return (
      <div className="admin-panel">
        <div className="admin-header">
          <button onClick={() => setViewing(null)}>← К пользователям</button>
          <h2>Хранилище: {viewing.user.username} / {viewing.folder.name}</h2>
        </div>
        {viewing.parent != null && (
          <button onClick={() => openStorage(viewing.user, viewing.parent)}>
            ⬆ Вверх
          </button>
        )}
        <h3>Папки</h3>
        <ul>
          {viewing.subfolders.map((f) => (
            <li key={`folder-${f.id}`}>
              <button onClick={() => openStorage(viewing.user, f.id)}>
                📁 {f.name} ({formatBytes(f.weight)})
              </button>
            </li>
          ))}
        </ul>
        <h3>Файлы</h3>
        <ul>
          {viewing.files.map((f) => (
            <li key={`file-${f.id}`}>📄 {f.name} ({formatBytes(f.weight)})</li>
          ))}
        </ul>
      </div>
    );
  }

  return (
    <div className="admin-panel">
      <h2>Управление пользователями</h2>
      {loading && <p>Загрузка...</p>}
      {error && <p className="error-message">{error}</p>}
      <table className="admin-users-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Логин</th>
            <th>Email</th>
            <th>Админ</th>
            <th>Файлы</th>
            <th>Хранилище</th>
            <th>Действия</th>
          </tr>
        </thead>
        <tbody>
          {users.map((u) => (
            <tr key={u.id}>
              <td>{u.id}</td>
              <td>{u.username}</td>
              <td>{u.email}</td>
              <td>
                <input
                  type="checkbox"
                  checked={u.is_admin}
                  onChange={() => toggleAdmin(u)}
                />
              </td>
              <td>{u.files_count} ({formatBytes(u.files_size)})</td>
              <td>
                {formatBytes(u.storage_used)} / {formatBytes(u.storage_max)}
              </td>
              <td>
                <button onClick={() => openStorage(u)}>Файлы</button>
                <button onClick={() => deleteUser(u)}>Удалить</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
});

export default AdminPanel;
