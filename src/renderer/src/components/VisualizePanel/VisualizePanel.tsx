// import styles from './VisualizePanel.module.css'

function VisualizePanel({ children }: { children?: React.ReactNode }): JSX.Element {
	return (
		<div className="panel">
			<div className="inner-panel">{children}</div>
		</div>
	)
}

export default VisualizePanel
