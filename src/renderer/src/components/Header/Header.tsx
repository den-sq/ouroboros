import styles from './Header.module.css'

function Header({ text }): JSX.Element {
	return (
		<div className={`${styles.header} header-font-size poppins-bold`}>{text.toUpperCase()}</div>
	)
}

export default Header
