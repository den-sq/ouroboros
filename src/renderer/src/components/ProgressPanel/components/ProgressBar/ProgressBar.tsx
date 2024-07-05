import styles from './ProgressBar.module.css'

function ProgressBar({ progress, name }): JSX.Element {
	return (
		<div className={styles.progressBarParent}>
			<div className={styles.progressBarContainer}>
				<div className={styles.progressBarText}>{name}</div>
				<div className={styles.progressBar} style={{ width: `${progress}%` }}></div>
			</div>
			<div className={styles.progressLabel}>{Math.round(progress)}%</div>
		</div>
	)
}

export default ProgressBar
