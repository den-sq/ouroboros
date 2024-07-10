import { Link } from 'react-router-dom'
import styles from './MenuOption.module.css'

function MenuOption({ path, optionName, icon, location }): JSX.Element {
	const active = location.pathname ? location.pathname.includes(path) : false
	const activeStyle = active ? styles.menuOptionActive : ''

	return (
		<Link to={path} style={{ textDecoration: 'none' }}>
			<div className={`${styles.menuOption} ${activeStyle}`}>
				<div className={styles.menuOptionIcon}>{icon}</div>
				<div className="header-font-size poppins-light">{optionName}</div>
			</div>
		</Link>
	)
}

export default MenuOption
