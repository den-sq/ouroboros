import { Link } from 'react-router-dom'
import styles from './MenuOption.module.css'

function MenuOption({ path, optionName, icon, active, setActive }): JSX.Element {
	const activeStyle = active == optionName ? styles.menuOptionActive : ''

	return (
		<Link to={path} style={{ textDecoration: 'none' }} onClick={() => setActive(optionName)}>
			<div className={`${styles.menuOption} ${activeStyle}`}>
				<div className={styles.menuOptionIcon}>{icon}</div>
				<div className="header-font-size poppins-light">{optionName}</div>
			</div>
		</Link>
	)
}

export default MenuOption
