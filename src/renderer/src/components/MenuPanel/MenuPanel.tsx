import styles from './MenuPanel.module.css'
import Menu from './components/Menu/Menu'

function MenuPanel(): JSX.Element {
	return (
		<div className={styles.menuPanel}>
			<Menu />
		</div>
	)
}

export default MenuPanel
