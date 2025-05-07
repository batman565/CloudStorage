import ProfileNav from "./profile-nav"
import Navigate from "./naviga"
import Logo from "./Logo"
import Download from "./download"
import CreFolder from "./create_folder"


const Header = () => {
    return (
        <div className="header">
            <Logo/>
            <Navigate/>
            <Download/>
            <CreFolder/>
            <ProfileNav/>
        </div>
    )
}

export default Header