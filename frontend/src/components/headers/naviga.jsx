import { useStore } from "../../store/store-context";
import { useState } from "react";

const Navigate = () => {
    const { fileStore } = useStore();
    const [searchValue, setSearchValue] = useState('');

    const handleInputChange = (e) => {
        const value = e.target.value;
        setSearchValue(value);
        fileStore.setSearchQuery(value);
    };

    return (
        <div className="search-bar">
            <input 
                type="text" 
                placeholder="Поиск файлов..." 
                value={searchValue}
                onChange={handleInputChange}
            />
            <button><i className="fas fa-search"></i></button>
        </div>
    );
};

export default Navigate;