import styles from './MenuOption.module.css'

function MenuOption({ optionName, icon, active = false }): JSX.Element {
	const activeStyle = active ? styles.menuOptionActive : ''

	return (
		<>
			<div className={`${styles.menuOption} ${activeStyle}`}>
				<div className={styles.menuOptionIcon}>{icon}</div>
				<div className="header-font-size poppins-light">{optionName}</div>
			</div>
		</>
	)
}

export default MenuOption
